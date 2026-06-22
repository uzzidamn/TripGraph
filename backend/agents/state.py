from typing import TypedDict, List, Dict, Any, Optional


class TripState(TypedDict):
    # Input
    raw_chat: List[str]
    user_id: Optional[str]

    # Guardrail
    guardrail_result: Dict[str, Any]

    # Memory
    user_profile: Dict[str, Any]
    memory_context: Dict[str, Any]
    memory_updates: Dict[str, Any]
    visited_destinations: List[str]

    # Constraint extraction (Chat Parser)
    extracted_constraints: Dict[str, Any]
    missing_fields: List[str]
    assumptions: Dict[str, str]

    # Constraint validation
    conflict_report: Dict[str, Any]
    is_ready_to_plan: bool

    # Data retrieval
    route_candidates: List[Dict[str, Any]]      # dedup-filtered; what the planner uses
    all_route_candidates: List[Dict[str, Any]]  # unfiltered; fallback when all visited
    hotel_candidates: List[Dict[str, Any]]
    transport_candidates: List[Dict[str, Any]]
    activity_candidates: List[Dict[str, Any]]
    food_candidates: List[Dict[str, Any]]
    waypoint_candidates: List[Dict[str, Any]]

    # Planning
    itinerary_candidates: List[Dict[str, Any]]
    selected_itinerary: Optional[Dict[str, Any]]
    alternative_itineraries: List[Dict[str, Any]]
    validation_report: Dict[str, Any]
    score_breakdown: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    map_points: List[Dict[str, Any]]
    cost_breakdown: Dict[str, Any]

    # Explanation
    explanation: str

    # Unsupported route
    unsupported_route: Optional[Dict[str, Any]]   # set when origin/destination has no catalog match
    suggested_routes: List[Dict[str, Any]]          # available routes to suggest instead

    # Replanning
    delay_event: Optional[Dict[str, Any]]
    replanned_itinerary: Optional[Dict[str, Any]]
    replanning_explanation: Optional[str]

    # Observability
    langsmith_run_id: Optional[str]   # root run ID captured by RunIdCapture after app.invoke()


def init_state(chat_messages: list[str], user_id: str | None = None) -> TripState:
    """Return a fully initialized TripState — every field has a value."""
    return TripState(
        raw_chat=chat_messages,
        user_id=user_id,
        guardrail_result={},
        user_profile={},
        memory_context={},
        memory_updates={},
        visited_destinations=[],
        extracted_constraints={},
        missing_fields=[],
        assumptions={},
        conflict_report={},
        is_ready_to_plan=False,
        route_candidates=[],
        all_route_candidates=[],
        hotel_candidates=[],
        transport_candidates=[],
        activity_candidates=[],
        food_candidates=[],
        waypoint_candidates=[],
        itinerary_candidates=[],
        selected_itinerary=None,
        alternative_itineraries=[],
        validation_report={},
        score_breakdown={},
        timeline=[],
        map_points=[],
        cost_breakdown={},
        explanation="",
        unsupported_route=None,
        suggested_routes=[],
        delay_event=None,
        replanned_itinerary=None,
        replanning_explanation=None,
        langsmith_run_id=None,
    )
