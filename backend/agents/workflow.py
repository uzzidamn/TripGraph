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
from concurrent.futures import ThreadPoolExecutor

from langgraph.graph import END, StateGraph

from backend.agents.nodes.chat_parser import chat_parser_node
from backend.agents.nodes.constraint_validator import constraint_validator_node
from backend.agents.nodes.guardrail import guardrail_node
from backend.agents.nodes.memory_agent import memory_agent_node
from backend.agents.nodes.replanner_agent import replanner_agent_node
from backend.agents.state import TripState, initialize_state


def _run_parallel(state: TripState, nodes: list) -> None:
    """Run independent agent nodes concurrently and merge their state patches."""
    with ThreadPoolExecutor(max_workers=len(nodes)) as pool:
        futures = [pool.submit(n, state) for n in nodes]
        patches = []
        for f in futures:
            try:
                patches.append(f.result() or {})
            except Exception as e:
                print(f"  ⚠️  parallel node failed: {e}")
    for patch in patches:
        state.update(patch)


def _route_after_guardrail(state: TripState) -> str:
    action = (state.get("guardrail_result") or {}).get("action", "proceed")
    if action == "clarify":
        return END  # off-topic: stop immediately, no point extracting
    return "chat_parser"  # for "confirm" or "proceed": continue to extract constraints


def _route_after_validation(state: TripState) -> str:
    """Conditional edge: proceed to data retrieval only if constraints are complete."""
    if state.get("is_ready_to_plan"):
        return "retrieve_data"
    return END


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


def _duplicate_guardrail(
    constraints: dict,
    user_id,
    duplicate_action: str | None,
) -> dict | None:
    """Check for a duplicate past trip before any expensive agent work.

    Returns a partial state dict to short-circuit the workflow, or None to proceed.
    Anonymous users (no user_id) are always passed through.
    Any exception skips the check — planning is never blocked.
    """
    if not user_id:
        return None

    origin = constraints.get("origin", "")
    destination = constraints.get("destination") or constraints.get("destination_type", "")
    if not origin or not destination:
        return None

    try:
        from backend.memory.store import find_duplicate_trip

        if duplicate_action == "cancel":
            return {"guardrail_result": {
                "action": "cancel",
                "reason": "user_cancelled",
                "response": "Planning cancelled. Let me know if you'd like to plan a different trip.",
                "matched_trip": None,
            }}

        if duplicate_action == "proceed":
            print(f"  ✅ Duplicate guard: user chose to proceed — planning {origin} → {destination}")
            return None

        matched = find_duplicate_trip(user_id, origin, destination)

        if matched is None:
            return None

        planned_at = matched.get("planned_at", "")
        date_str = ""
        if planned_at:
            try:
                from datetime import datetime as _dt
                dt = _dt.fromisoformat(planned_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%d %b %Y")
            except Exception:
                date_str = planned_at[:10]

        status_str = matched.get("status", "planned")
        verb = "had" if status_str == "completed" else "have"
        response = (
            f"You already {verb} a trip to {destination} from {origin}"
            + (f" ({date_str})" if date_str else "")
            + ". Would you like to proceed with the same?"
        )
        print(f"  ⏸  Duplicate guard: {status_str} trip to {destination} — confirming with user")
        return {"guardrail_result": {
            "action": "confirm",
            "reason": "similar_trip_found",
            "response": response,
            "matched_trip": matched,
        }}

    except Exception as e:
        print(f"  ⚠️  Duplicate guardrail failed ({e}) — skipping check")
        return None


def run_workflow_from_constraints(
    constraints: dict,
    user_id: int | str | None = None,
    duplicate_action: str | None = None,
) -> TripState:
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

    if user_id:
        state["user_id"] = user_id
        from backend.memory.store import get_user_memory
        state["user_profile"] = get_user_memory(user_id)
        print(f"  🧠 Memory loaded for user_id={user_id}")

    # Duplicate trip gate — stops before any expensive work
    early_exit = _duplicate_guardrail(constraints, user_id, duplicate_action)
    if early_exit is not None:
        state.update(early_exit)
        return state

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
    #
    # flights/train both read only constraints and write disjoint keys, so run
    # them concurrently (each does a DDG scrape + LLM call). Same for
    # weather/insights after planning. This overlaps their network waits.
    _run_parallel(state, [flights_agent_node, train_agent_node])
    state.update(mode_planner_node(state))
    state.update(planner_orchestrator_node(state))   # picks route/transport/hotel shell
    state.update(terminal_resolver_node(state))
    _run_parallel(state, [weather_agent_node, insights_agent_node])

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

    # Record the new trip in memory if planning succeeded
    if user_id and state.get("selected_itinerary"):
        from backend.memory.store import record_new_trip
        trip_id = record_new_trip(user_id, constraints)
        print(f"  💾 Trip recorded: {trip_id}")

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
