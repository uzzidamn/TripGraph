from typing import TypedDict, List, Dict, Any, Optional


class TripState(TypedDict):
    # Input
    raw_chat: List[str]

    # Constraint extraction (Chat Parser)
    extracted_constraints: Dict[str, Any]
    missing_fields: List[str]
    assumptions: Dict[str, str]

    # Constraint validation
    conflict_report: Dict[str, Any]
    is_ready_to_plan: bool

    # Data retrieval
    route_candidates: List[Dict[str, Any]]
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

    # Observability
    trace_id: Optional[str]

    # Replanning
    delay_event: Optional[Dict[str, Any]]
    replanned_itinerary: Optional[Dict[str, Any]]
    replanning_explanation: Optional[str]


def init_state(chat_messages: list[str]) -> TripState:
    """Return a fully initialized TripState — every field has a value."""
    return TripState(
        raw_chat=chat_messages,
        extracted_constraints={},
        missing_fields=[],
        assumptions={},
        conflict_report={},
        is_ready_to_plan=False,
        route_candidates=[],
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
        trace_id=None,
        delay_event=None,
        replanned_itinerary=None,
        replanning_explanation=None,
    )
