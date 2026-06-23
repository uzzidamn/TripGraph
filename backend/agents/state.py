"""
Shared state schema for the LangGraph agentic pipeline.
All nodes read from and write to TripState.
"""
from typing import Any, Dict, List, Optional, TypedDict


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

    # Enrichment
    enrichment_applied: bool

    # Replanning
    delay_event: Optional[Dict[str, Any]]
    replanned_itinerary: Optional[Dict[str, Any]]
    replanning_explanation: Optional[str]

    # Refinement (1-round LLM counter-questions answered by the user)
    refinement_questions: List[Dict[str, Any]]
    refinement_answers: Dict[str, Any]

    # Planning loop telemetry — used by /api/generate-itinerary to debug 2-pass loop
    retrieval_passes: int
    retrieval_source: Dict[str, str]   # bucket -> 'kg' | 'api+kg' | 'empty'

    # Pending-API agent payloads (scaffolded; silent until keys configured)
    flights: Optional[Dict[str, Any]]
    trains: Optional[Dict[str, Any]]
    hotel_deals: Optional[Dict[str, Any]]
    traffic: Optional[Dict[str, Any]]
    weather_forecast: Dict[str, Any]   # keyed by lat,lng tuple-as-string

    # Final AI review of the assembled itinerary
    review: Optional[Dict[str, Any]]

    # Fatigue model
    fatigue_per_event: Dict[str, Any]   # event_id -> {base, adjusted, skippability}

    # DuckDuckGo insights — place_id -> {abstract, source_url, related_topics, ...}
    insights_per_place: Dict[str, Any]

    # Architect critic loop — review feedback from the previous iteration
    last_review_feedback: Optional[Dict[str, Any]]

    # Architect's full structured plan (persisted for frontend)
    architect_plan: Optional[Dict[str, Any]]

    # Terminal info — airports/stations for origin + destination with first/last mile times
    terminal_info: Optional[Dict[str, Any]]

    # Per-segment road polylines (drawn between consecutive stops via ORS)
    segment_polylines: List[Dict[str, Any]]


def initialize_state(raw_chat: List[str]) -> TripState:
    """Return a fully initialized TripState with all fields set to safe defaults.

    LangGraph raises KeyError if any field is absent when a node tries to read it.
    Every field must be present from the start even if its value is empty.
    """
    return TripState(
        raw_chat=raw_chat,
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
        enrichment_applied=False,
        delay_event=None,
        replanned_itinerary=None,
        replanning_explanation=None,
        refinement_questions=[],
        refinement_answers={},
        retrieval_passes=0,
        retrieval_source={},
        flights=None,
        trains=None,
        hotel_deals=None,
        traffic=None,
        weather_forecast={},
        fatigue_per_event={},
        insights_per_place={},
        review=None,
        last_review_feedback=None,
        architect_plan=None,
        terminal_info=None,
        segment_polylines=[],
    )
