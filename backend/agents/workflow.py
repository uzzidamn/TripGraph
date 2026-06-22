"""
LangGraph workflow definitions for TripGraph AI.

Exports three public functions consumed by Bucket 3 (FastAPI):
    run_workflow(chat_messages, user_id)       — full 14-node pipeline from raw chat
    run_workflow_from_constraints(constraints)  — skip LLM re-parse, inject constraints directly
    run_replan_workflow(state, delay)           — delay-aware replanning

Main workflow graph (Bucket 2 v2 — 14 nodes):
    guardrail → chat_parser → memory_agent → constraint_validator → route_retriever
    → [Send fan-out: hotel/transport/activity/food/waypoint retrievers (parallel)]
    → planner_orchestrator → [explainer + memory_updater (parallel)]

Replan workflow graph:
    replan → memory_updater → END
"""
import os

from langgraph.graph import END, StateGraph

from backend.agents.nodes.chat_parser import chat_parser_node
from backend.agents.nodes.constraint_validator import constraint_validator_node
from backend.agents.nodes.guardrail import guardrail_node
from backend.agents.nodes.memory_agent import memory_agent_node
from backend.agents.nodes.replanner_agent import replanner_agent_node
from backend.agents.state import TripState, initialize_state


def _route_after_guardrail(state: TripState) -> str:
    action = (state.get("guardrail_result") or {}).get("action", "proceed")
    if action in ("clarify", "confirm"):
        return END
    return "chat_parser"


def build_main_workflow() -> StateGraph:
    """Parse + validate only — stops at constraint_validator.

    parse-chat only needs to extract constraints and confirm they're complete.
    Planning runs in generate-itinerary via run_workflow_from_constraints.
    Keeping this graph small (4 nodes) keeps parse-chat under ~4s.
    """
    graph = StateGraph(TripState)

    graph.add_node("guardrail",            guardrail_node)
    graph.add_node("chat_parser",          chat_parser_node)
    graph.add_node("memory_agent",         memory_agent_node)
    graph.add_node("constraint_validator", constraint_validator_node)

    graph.set_entry_point("guardrail")
    graph.add_conditional_edges("guardrail", _route_after_guardrail,
        {"chat_parser": "chat_parser", END: END})
    graph.add_edge("chat_parser",          "memory_agent")
    graph.add_edge("memory_agent",         "constraint_validator")
    graph.add_edge("constraint_validator", END)

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


def run_workflow(chat_messages: list[str], user_id: str | None = None) -> TripState:
    """Run the full 14-node planning pipeline from raw chat messages."""
    from backend.config import settings
    if getattr(settings, "PIPELINE_MODE", "agentic") == "augmented":
        print("\n🚀 Starting Augmented LLM workflow (Bucket 2.1)")
        from backend.agents_augmented.workflow import run_workflow as run_augmented
        result = run_augmented(chat_messages)
        from backend.agents.nodes.itinerary_enricher import itinerary_enricher_node
        enriched = itinerary_enricher_node(result)
        result.update(enriched)
        return result

    print("\n🚀 Starting TripGraph workflow (Bucket 2 v2)")
    initial_state = initialize_state(chat_messages)
    if user_id:
        initial_state["user_id"] = user_id
        # Pre-load memory so guardrail can check past trips
        from backend.memory.store import get_user_memory
        initial_state["user_profile"] = get_user_memory(user_id)
    result = _main_app.invoke(initial_state)
    print("✅ Workflow complete\n")
    return result


def run_workflow_from_constraints(constraints: dict) -> TripState:
    """Run the planning pipeline with pre-extracted constraints, skipping LLM re-parse.

    Pipeline order (post-pivot 2026-06-21):
        data_retriever (2-pass KG↔API↔cache) → planner_orchestrator →
        itinerary_enricher → weather_agent → fatigue_adjuster →
        flights_agent + deals_agent + traffic_agent (silent stubs) → explainer
    """
    print("\n🚀 Starting TripGraph workflow (from constraints)")
    state = initialize_state([])
    state["extracted_constraints"] = constraints
    state["is_ready_to_plan"] = True

    from backend.agents.nodes.weather_agent import weather_agent_node
    from backend.agents.nodes.flights_agent import flights_agent_node
    from backend.agents.nodes.train_agent import train_agent_node
    from backend.agents.nodes.mode_planner import mode_planner_node
    from backend.agents.nodes.terminal_resolver import terminal_resolver_node
    from backend.agents.nodes.deals_agent import deals_agent_node
    from backend.agents.nodes.data_retriever import data_retriever_node, route_retriever_node
    from backend.agents.nodes.planner_orchestrator import planner_orchestrator_node
    from backend.agents.nodes.explainer import explainer_node
    from backend.agents.nodes.traffic_agent import traffic_agent_node
    from backend.agents.nodes.insights_agent import insights_agent_node
    from backend.agents.nodes.architect import architect_node
    from backend.agents.nodes.photo_enricher import photo_enricher_node
    from backend.agents.nodes.segment_router import segment_router_node
    from backend.agents.nodes.review_agent import review_agent_node

    # 0) Gate: check origin/destination are in the catalog before any expensive work
    state.update(route_retriever_node(state))
    if state.get("unsupported_route"):
        print("  ⛔ Unsupported route — returning early without planning")
        return state

    # 1) Retrieve candidate data (2-pass KG↔API)
    state.update(data_retriever_node(state))

    # 2) Context the architect needs upstream:
    #    - flight/train advisories (with DDG-grounded prices)
    #    - mode_planner injects a flight transport option for long hauls
    #    - terminal_resolver finds airports/stations + first/last mile times
    #    - weather forecast (drives gear checklist)
    #    - DDG insights (Wikipedia-style abstracts per place)
    state.update(flights_agent_node(state))
    state.update(train_agent_node(state))
    state.update(mode_planner_node(state))
    state.update(planner_orchestrator_node(state))   # picks route/transport/hotel shell
    state.update(terminal_resolver_node(state))
    state.update(weather_agent_node(state))
    state.update(insights_agent_node(state))

    # 3) Architect (optional — disabled by default for latency)
    use_architect = os.getenv("ENABLE_ARCHITECT", "false").lower() == "true"
    if use_architect:
        print("\n🧠 Running Architect (ENABLE_ARCHITECT=true)...")
        state.update(architect_node(state))

    state.update(explainer_node(state))
    state.update(photo_enricher_node(state))
    state.update(segment_router_node(state))
    state.update(deals_agent_node(state))
    state.update(traffic_agent_node(state))

    _fold_review_into_explanation(state)

    print("✅ Workflow complete\n")
    return state


def _fold_review_into_explanation(state: TripState) -> None:
    """Prepend a short AI-review caveat to the explanation when the plan is flawed."""
    review = state.get("review") or {}
    verdict = review.get("verdict")
    if verdict == "needs_attention":
        notes = review.get("notes") or []
        top = notes[0].get("issue") if notes else review.get("summary", "")
        caveat = f"⚠️ AI review flagged this plan: {top} "
        state["explanation"] = caveat + (state.get("explanation") or "")


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
        result = run_augmented(state, delay_event)
        # Apply itinerary enrichment post-planning!
        from backend.agents.nodes.itinerary_enricher import itinerary_enricher_node
        enriched = itinerary_enricher_node(result)
        result.update(enriched)
        return result

    print("\n🔄 Starting replan workflow")
    replan_state = {**state, "delay_event": delay_event}
    result = _replan_app.invoke(replan_state)
    print("✅ Replan complete\n")
    return result
