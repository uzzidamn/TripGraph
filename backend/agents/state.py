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
    )
