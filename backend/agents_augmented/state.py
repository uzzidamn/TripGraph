from typing import TypedDict, Optional


class TripState(TypedDict):
    # Input
    raw_chat: list[str]
    # Constraint extraction
    extracted_constraints: Optional[dict]
    missing_fields: list[str]
    assumptions: dict
    # Constraint validation
    conflict_report: Optional[dict]
    is_ready_to_plan: bool
    # Data retrieval
    route_candidates: list[dict]
    hotel_candidates: list[dict]
    transport_candidates: list[dict]
    activity_candidates: list[dict]
    food_candidates: list[dict]
    waypoint_candidates: list[dict]
    # Planning
    itinerary_candidates: list[dict]
    selected_itinerary: Optional[dict]
    alternative_itineraries: list[dict]
    validation_report: Optional[dict]
    score_breakdown: Optional[dict]
    timeline: list[dict]
    map_points: list[dict]
    cost_breakdown: Optional[dict]
    # Explanation
    explanation: Optional[str]
    # Replanning
    delay_event: Optional[dict]
    replanned_itinerary: Optional[dict]
    replanning_explanation: Optional[str]


def init_state(chat_messages: list[str]) -> TripState:
    return TripState(
        raw_chat=chat_messages,
        extracted_constraints=None,
        missing_fields=[],
        assumptions={},
        conflict_report=None,
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
        validation_report=None,
        score_breakdown=None,
        timeline=[],
        map_points=[],
        cost_breakdown=None,
        explanation=None,
        delay_event=None,
        replanned_itinerary=None,
        replanning_explanation=None,
    )
