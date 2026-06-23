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
import os
from concurrent.futures import ThreadPoolExecutor

from langgraph.graph import END, StateGraph

from backend.agents.nodes.chat_parser import chat_parser_node
from backend.agents.nodes.constraint_validator import constraint_validator_node
from backend.agents.nodes.data_retriever import data_retriever_node
from backend.agents.nodes.explainer import explainer_node
from backend.agents.nodes.planner_orchestrator import planner_orchestrator_node
from backend.agents.nodes.replanner_agent import replanner_agent_node
from backend.agents.nodes.itinerary_enricher import itinerary_enricher_node
from backend.agents.state import TripState, initialize_state


def _run_parallel(state: TripState, nodes: list) -> None:
    """Run independent agent nodes concurrently and merge their state patches.

    Each node reads the shared state and returns a patch dict (it must not depend
    on the others' output). Patches are applied after all complete, so the nodes
    see a consistent pre-update view. Used for I/O-bound agents whose network
    waits can overlap (flights+train, weather+insights).
    """
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


def _route_after_validation(state: TripState) -> str:
    """Conditional edge: proceed to data retrieval only if constraints are complete."""
    if state.get("is_ready_to_plan"):
        return "retrieve_data"
    return END

def check_kg_coverage(state: TripState) -> str:
    """Route to full enrichment if KG data is sparse."""
    hotels = state.get("hotel_candidates", [])
    activities = state.get("activity_candidates", [])
    
    # If KG returned very little data, use LLM-heavy enrichment path
    if len(hotels) == 0 or len(activities) <= 1:
        return "llm_heavy_enrichment"
    return "standard_enrichment"


def build_main_workflow() -> StateGraph:
    """Construct and compile the main planning workflow graph."""
    graph = StateGraph(TripState)

    graph.add_node("parse_chat", chat_parser_node)
    graph.add_node("validate_constraints", constraint_validator_node)
    graph.add_node("retrieve_data", data_retriever_node)
    graph.add_node("plan_itinerary", planner_orchestrator_node)
    graph.add_node("enrich_itinerary", itinerary_enricher_node)
    graph.add_node("explain_plan", explainer_node)

    graph.set_entry_point("parse_chat")
    graph.add_edge("parse_chat", "validate_constraints")
    graph.add_conditional_edges(
        "validate_constraints",
        _route_after_validation,
        {"retrieve_data": "retrieve_data", END: END},
    )
    graph.add_edge("retrieve_data", "plan_itinerary")
    graph.add_conditional_edges(
        "plan_itinerary",
        check_kg_coverage,
        {
            "standard_enrichment": "enrich_itinerary",
            "llm_heavy_enrichment": "enrich_itinerary"
        }
    )
    graph.add_edge("enrich_itinerary", "explain_plan")
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
        result = run_augmented(chat_messages)
        # Apply itinerary enrichment post-planning!
        from backend.agents.nodes.itinerary_enricher import itinerary_enricher_node
        enriched = itinerary_enricher_node(result)
        result.update(enriched)
        return result

    print("\n🚀 Starting TripGraph workflow")
    initial_state = initialize_state(chat_messages)
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
    from backend.agents.nodes.traffic_agent import traffic_agent_node
    from backend.agents.nodes.insights_agent import insights_agent_node
    from backend.agents.nodes.architect import architect_node
    from backend.agents.nodes.photo_enricher import photo_enricher_node
    from backend.agents.nodes.segment_router import segment_router_node
    from backend.agents.nodes.review_agent import review_agent_node

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

    # 3) The Architect + Reviewer critic loop.
    # Each iteration re-runs the (expensive) architect, so default to a single
    # pass — on small hosts a 2nd full generation doubles latency for marginal
    # gain. Bump ARCHITECT_MAX_ITERS=2 to re-enable self-correction.
    max_iterations = int(os.getenv("ARCHITECT_MAX_ITERS", "1"))
    for iteration in range(max_iterations):
        print(f"\n🧠 Planner iteration {iteration + 1}/{max_iterations}...")
        state.update(architect_node(state))

        # Enrich timeline events with Google Place photos (for KG-sourced events
        # that don't carry a photo_name).
        state.update(photo_enricher_node(state))

        # Compute real road-following polylines between consecutive stops
        state.update(segment_router_node(state))

        # 4) Side-channel pending-API agents (silent stubs)
        state.update(deals_agent_node(state))
        state.update(traffic_agent_node(state))

        # 5) Final AI sanity-review
        state.update(review_agent_node(state))
        
        review = state.get("review") or {}
        if review.get("verdict") != "needs_attention" or iteration == max_iterations - 1:
            break
            
        print(f"  🔄 Critic loop: Plan needs attention. Re-running architect with review feedback...")
        state["last_review_feedback"] = review

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
