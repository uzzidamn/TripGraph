"""
LangGraph workflow for Bucket 2 agentic pipeline.
Public API: run_workflow(chat_messages, user_id) and run_replan_workflow(state, delay_event).
Engine selected via PIPELINE_MODE env var: 'langgraph' (default) or 'augmented_llm'.
"""
import os

from dotenv import load_dotenv

load_dotenv()

from backend.agents.state import TripState, init_state
from backend.config import configure_langsmith

configure_langsmith()  # enable LangSmith tracing if LANGCHAIN_API_KEY is set


# ---------------------------------------------------------------------------
# Public entry points — called by Bucket 3 API and eval runner
# ---------------------------------------------------------------------------

def run_workflow(
    chat_messages: list[str],
    user_id: str | None = None,
    run_metadata: dict | None = None,
) -> TripState:
    """Plan a trip from raw chat messages. Engine selected via PIPELINE_MODE."""
    engine = os.getenv("PIPELINE_MODE", "langgraph")
    if engine == "augmented_llm":
        from backend.agents_augmented.workflow import run_workflow as _run
        return _run(chat_messages)
    return _langgraph_run_workflow(chat_messages, user_id, run_metadata)


def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    """Replan an existing trip after a delay event. Engine selected via PIPELINE_MODE."""
    engine = os.getenv("PIPELINE_MODE", "langgraph")
    if engine == "augmented_llm":
        from backend.agents_augmented.workflow import run_replan_workflow as _replan
        return _replan(state, delay_event)
    return _langgraph_replan_workflow(state, delay_event)


# ---------------------------------------------------------------------------
# LangGraph implementation
# ---------------------------------------------------------------------------

def _route_after_guardrail(state: TripState) -> str:
    action = (state.get("guardrail_result") or {}).get("action", "proceed")
    return "__end__" if action in ("clarify", "confirm") else "chat_parser"


def _should_plan(state: TripState) -> str:
    from langgraph.graph import END
    return "retrieve_data" if state.get("is_ready_to_plan") else END


def _route_after_retriever(state: TripState):
    """Exit early if no routes found; otherwise fan-out to domain sub-nodes."""
    from langgraph.graph import END
    from langgraph.types import Send
    if state.get("unsupported_route"):
        return END
    return [
        Send("hotel_retriever",     state),
        Send("transport_retriever", state),
        Send("activity_retriever",  state),
        Send("food_retriever",      state),
        Send("waypoint_retriever",  state),
    ]


def _langgraph_run_workflow(
    chat_messages: list[str],
    user_id: str | None,
    run_metadata: dict | None = None,
) -> TripState:
    from langgraph.graph import END, StateGraph

    from backend.agents.nodes.activity_retriever import activity_retriever_node
    from backend.agents.nodes.chat_parser import chat_parser_node
    from backend.agents.nodes.constraint_validator import constraint_validator_node
    from backend.agents.nodes.data_retriever import route_retriever_node
    from backend.agents.nodes.explainer import explainer_node
    from backend.agents.nodes.food_retriever import food_retriever_node
    from backend.agents.nodes.guardrail import guardrail_node
    from backend.agents.nodes.hotel_retriever import hotel_retriever_node
    from backend.agents.nodes.memory_agent import memory_agent_node
    from backend.agents.nodes.memory_updater import memory_updater_node
    from backend.agents.nodes.planner_orchestrator import planner_orchestrator_node
    from backend.agents.nodes.transport_retriever import transport_retriever_node
    from backend.agents.nodes.waypoint_retriever import waypoint_retriever_node

    graph = StateGraph(TripState)

    # Sequential spine
    graph.add_node("guardrail",            guardrail_node)
    graph.add_node("chat_parser",          chat_parser_node)
    graph.add_node("memory_agent",         memory_agent_node)
    graph.add_node("constraint_validator", constraint_validator_node)

    # Route retrieval + dedup (produces route_candidates + all_route_candidates)
    graph.add_node("route_retriever",      route_retriever_node)

    # 5 domain sub-nodes — LangGraph runs them concurrently via Send fan-out
    graph.add_node("hotel_retriever",      hotel_retriever_node)
    graph.add_node("transport_retriever",  transport_retriever_node)
    graph.add_node("activity_retriever",   activity_retriever_node)
    graph.add_node("food_retriever",       food_retriever_node)
    graph.add_node("waypoint_retriever",   waypoint_retriever_node)

    # Planning + explanation (fan-out after planner)
    graph.add_node("planner_orchestrator", planner_orchestrator_node)
    graph.add_node("explainer",            explainer_node)
    graph.add_node("memory_updater",       memory_updater_node)

    # Edges
    graph.set_entry_point("guardrail")
    graph.add_conditional_edges(
        "guardrail",
        _route_after_guardrail,
        {"chat_parser": "chat_parser", "__end__": END},
    )
    graph.add_edge("chat_parser",           "memory_agent")
    graph.add_edge("memory_agent",          "constraint_validator")
    graph.add_conditional_edges(
        "constraint_validator",
        _should_plan,
        {"retrieve_data": "route_retriever", "__end__": END},
    )

    # Send fan-out: route_retriever → 5 sub-nodes in parallel (or exit if unsupported)
    graph.add_conditional_edges("route_retriever", _route_after_retriever)

    # Fan-in: all 5 sub-nodes → planner (LangGraph waits for all before proceeding)
    for sub_node in (
        "hotel_retriever", "transport_retriever", "activity_retriever",
        "food_retriever",  "waypoint_retriever",
    ):
        graph.add_edge(sub_node, "planner_orchestrator")

    # Fan-out after planner: explainer + memory_updater run concurrently
    graph.add_edge("planner_orchestrator", "explainer")
    graph.add_edge("planner_orchestrator", "memory_updater")
    graph.add_edge("explainer",            END)
    graph.add_edge("memory_updater",       END)

    app = graph.compile()
    initial = init_state(chat_messages, user_id=user_id)
    from backend.config import RunIdCapture, get_runnable_config
    capture = RunIdCapture()
    config  = get_runnable_config(run_name="tripgraph-plan", metadata=run_metadata or {}, callbacks=[capture])
    result  = app.invoke(initial, config=config)
    result["langsmith_run_id"] = capture.run_id
    return result


def _langgraph_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    from langgraph.graph import END, StateGraph

    from backend.agents.nodes.memory_updater import memory_updater_node
    from backend.agents.nodes.replanner_agent import replanner_agent_node

    updated = dict(state)
    updated["delay_event"] = delay_event

    graph = StateGraph(TripState)
    graph.add_node("replanner_agent", replanner_agent_node)
    graph.add_node("memory_updater", memory_updater_node)
    graph.set_entry_point("replanner_agent")
    graph.add_edge("replanner_agent", "memory_updater")
    graph.add_edge("memory_updater", END)

    app = graph.compile()
    return app.invoke(updated)
