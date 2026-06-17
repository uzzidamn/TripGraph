"""
LangGraph workflow for Bucket 2 agentic pipeline.
Public API: run_workflow(chat_messages) and run_replan_workflow(state, delay_event).
Engine selected via PIPELINE_MODE env var: 'langgraph' (default) or 'augmented_llm'.
"""
import os

from dotenv import load_dotenv

load_dotenv()

from backend.agents.state import TripState, init_state


# ---------------------------------------------------------------------------
# Public entry points — called by Bucket 3 API
# ---------------------------------------------------------------------------

def run_workflow(chat_messages: list[str]) -> TripState:
    """Plan a trip from raw chat messages. Engine selected via PIPELINE_MODE."""
    engine = os.getenv("PIPELINE_MODE", "langgraph")
    if engine == "augmented_llm":
        from backend.agents_augmented.workflow import run_workflow as _run
        return _run(chat_messages)
    return _langgraph_run_workflow(chat_messages)


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

def _should_plan(state: TripState) -> str:
    from langgraph.graph import END
    return "retrieve_data" if state.get("is_ready_to_plan") else END


def _langgraph_run_workflow(chat_messages: list[str]) -> TripState:
    from langgraph.graph import END, StateGraph

    from backend.agents.nodes.chat_parser import chat_parser_node
    from backend.agents.nodes.constraint_validator import constraint_validator_node
    from backend.agents.nodes.data_retriever import data_retriever_node
    from backend.agents.nodes.explainer import explainer_node
    from backend.agents.nodes.planner_orchestrator import planner_orchestrator_node
    from backend.agents.llm_client import get_trace_url

    graph = StateGraph(TripState)

    graph.add_node("chat_parser", chat_parser_node)
    graph.add_node("constraint_validator", constraint_validator_node)
    graph.add_node("retrieve_data", data_retriever_node)
    graph.add_node("plan_itinerary", planner_orchestrator_node)
    graph.add_node("explain_plan", explainer_node)

    graph.set_entry_point("chat_parser")
    graph.add_edge("chat_parser", "constraint_validator")
    graph.add_conditional_edges(
        "constraint_validator",
        _should_plan,
        {"retrieve_data": "retrieve_data", "__end__": END},
    )
    graph.add_edge("retrieve_data", "plan_itinerary")
    graph.add_edge("plan_itinerary", "explain_plan")
    graph.add_edge("explain_plan", END)

    app = graph.compile()
    initial = init_state(chat_messages)
    result = app.invoke(initial)

    result["trace_id"] = get_trace_url()
    return result


def _langgraph_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    from langgraph.graph import END, StateGraph

    from backend.agents.nodes.replanner_agent import replanner_agent_node
    from backend.agents.llm_client import get_trace_url

    # Inject delay event into state before running
    updated = dict(state)
    updated["delay_event"] = delay_event

    graph = StateGraph(TripState)
    graph.add_node("replanner_agent", replanner_agent_node)
    graph.set_entry_point("replanner_agent")
    graph.add_edge("replanner_agent", END)

    app = graph.compile()
    result = app.invoke(updated)

    result["trace_id"] = get_trace_url()
    return result
