"""
LangGraph workflow definitions for TripGraph AI.

Exports three public functions consumed by Bucket 3 (FastAPI):
    run_workflow(chat_messages)               — full pipeline from raw chat
    run_workflow_from_constraints(constraints) — skip LLM re-parse, inject constraints directly
    run_replan_workflow(state, delay)         — delay-aware replanning

Main workflow graph:
    parse_chat → validate_constraints → [conditional]
        is_ready=True  → retrieve_data → plan_itinerary → explain_plan → END
        is_ready=False → END (returns partial state with missing_fields)

Replan workflow graph:
    replan → END
"""
from langgraph.graph import END, StateGraph

from backend.agents.nodes.chat_parser import chat_parser_node
from backend.agents.nodes.constraint_validator import constraint_validator_node
from backend.agents.nodes.data_retriever import data_retriever_node
from backend.agents.nodes.explainer import explainer_node
from backend.agents.nodes.planner_orchestrator import planner_orchestrator_node
from backend.agents.nodes.replanner_agent import replanner_agent_node
from backend.agents.state import TripState, initialize_state


def _route_after_validation(state: TripState) -> str:
    """Conditional edge: proceed to data retrieval only if constraints are complete."""
    if state.get("is_ready_to_plan"):
        return "retrieve_data"
    return END


def build_main_workflow() -> StateGraph:
    """Construct and compile the main planning workflow graph."""
    graph = StateGraph(TripState)

    graph.add_node("parse_chat", chat_parser_node)
    graph.add_node("validate_constraints", constraint_validator_node)
    graph.add_node("retrieve_data", data_retriever_node)
    graph.add_node("plan_itinerary", planner_orchestrator_node)
    graph.add_node("explain_plan", explainer_node)

    graph.set_entry_point("parse_chat")
    graph.add_edge("parse_chat", "validate_constraints")
    graph.add_conditional_edges(
        "validate_constraints",
        _route_after_validation,
        {"retrieve_data": "retrieve_data", END: END},
    )
    graph.add_edge("retrieve_data", "plan_itinerary")
    graph.add_edge("plan_itinerary", "explain_plan")
    graph.add_edge("explain_plan", END)

    return graph.compile()


def build_replan_workflow() -> StateGraph:
    """Construct and compile the delay replanning workflow graph."""
    graph = StateGraph(TripState)
    graph.add_node("replan", replanner_agent_node)
    graph.set_entry_point("replan")
    graph.add_edge("replan", END)
    return graph.compile()


# Compiled graphs — built once at module load time
_main_app = build_main_workflow()
_replan_app = build_replan_workflow()


def run_workflow(chat_messages: list[str]) -> TripState:
    """Run the full planning pipeline from raw chat messages.

    Initializes a fresh TripState, invokes the main workflow, and returns
    the final state containing constraints, selected itinerary, timeline,
    map points, cost breakdown, and explanation.

    Args:
        chat_messages: List of raw chat message strings from the group.

    Returns:
        Populated TripState dict.
    """
    from backend.config import settings
    if getattr(settings, "PIPELINE_MODE", "agentic") == "augmented":
        print("\n🚀 Starting Augmented LLM workflow (Bucket 2.1)")
        from backend.agents_augmented.workflow import run_workflow as run_augmented
        return run_augmented(chat_messages)

    print("\n🚀 Starting TripGraph workflow")
    initial_state = initialize_state(chat_messages)
    result = _main_app.invoke(initial_state)
    print("✅ Workflow complete\n")
    return result


def run_workflow_from_constraints(constraints: dict) -> TripState:
    """Run the planning pipeline with pre-extracted constraints, skipping LLM re-parse.

    Used by /api/generate-itinerary when the frontend already holds a parsed
    constraints dict. Injecting directly avoids a second LLM extraction pass
    where destination / destination_type can drift (e.g. "heritage" → "cultural").

    Steps run: data_retriever → planner_orchestrator → explainer  (no chat_parser, no validator)
    """
    print("\n🚀 Starting TripGraph workflow (from constraints)")
    state = initialize_state([])
    state["extracted_constraints"] = constraints
    state["is_ready_to_plan"] = True

    state.update(data_retriever_node(state))
    state.update(planner_orchestrator_node(state))
    state.update(explainer_node(state))

    print("✅ Workflow complete\n")
    return state


def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    """Run the replanning workflow given an existing state and a delay event.

    Args:
        state: The TripState from a completed run_workflow() call.
        delay_event: Dict with keys: delay_type, delay_minutes, affected_event_id.

    Returns:
        Updated TripState with replanned_itinerary and replanning_explanation set.
    """
    from backend.config import settings
    if getattr(settings, "PIPELINE_MODE", "agentic") == "augmented":
        print("\n🔄 Starting Augmented LLM replan workflow (Bucket 2.1)")
        from backend.agents_augmented.workflow import run_replan_workflow as run_augmented
        return run_augmented(state, delay_event)

    print("\n🔄 Starting replan workflow")
    replan_state = {**state, "delay_event": delay_event}
    result = _replan_app.invoke(replan_state)
    print("✅ Replan complete\n")
    return result
