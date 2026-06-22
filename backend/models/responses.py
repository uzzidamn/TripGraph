"""Pydantic response models for all API endpoints."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ParseChatResponse(BaseModel):
    """Response for POST /api/parse-chat."""

    # Agent 0: Guardrail
    guardrail_result: Optional[Dict[str, Any]] = None
    # Agent 1: Chat Parser
    extracted_constraints: Optional[Dict[str, Any]] = None
    missing_fields: Optional[List[str]] = None
    assumptions: Optional[Dict[str, Any]] = None
    # Agent 2: Memory Agent
    user_profile: Optional[Dict[str, Any]] = None
    memory_context: Optional[Dict[str, Any]] = None
    visited_destinations: Optional[List[str]] = None
    # Agent 3: Constraint Validator
    conflict_report: Optional[Dict[str, Any]] = None
    is_ready_to_plan: Optional[bool] = None


class ItineraryResponse(BaseModel):
    """Response for POST /api/generate-itinerary."""

    # Unsupported route (checked first in failure path)
    unsupported_route: Optional[Dict[str, Any]] = None
    suggested_routes: Optional[List[Dict[str, Any]]] = None
    # Agent 0: Guardrail
    guardrail_result: Optional[Dict[str, Any]] = None
    # Agents 1-3
    extracted_constraints: Optional[Dict[str, Any]] = None
    missing_fields: Optional[List[str]] = None
    assumptions: Optional[Dict[str, Any]] = None
    conflict_report: Optional[Dict[str, Any]] = None
    is_ready_to_plan: Optional[bool] = None
    # Agent 2: Memory
    user_profile: Optional[Dict[str, Any]] = None
    memory_context: Optional[Dict[str, Any]] = None
    visited_destinations: Optional[List[str]] = None
    # Agent 4: Data Retrieval candidates
    route_candidates: Optional[List[Dict[str, Any]]] = None
    hotel_candidates: Optional[List[Dict[str, Any]]] = None
    transport_candidates: Optional[List[Dict[str, Any]]] = None
    activity_candidates: Optional[List[Dict[str, Any]]] = None
    food_candidates: Optional[List[Dict[str, Any]]] = None
    waypoint_candidates: Optional[List[Dict[str, Any]]] = None
    # Agent 5: Planner
    recommended_itinerary: Optional[Dict[str, Any]] = None
    alternatives: Optional[List[Dict[str, Any]]] = None
    validation_report: Optional[Dict[str, Any]] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    map_points: Optional[List[Dict[str, Any]]] = None
    cost_breakdown: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = ""

    # New planning-loop telemetry
    retrieval_passes: Optional[int] = 0
    retrieval_source: Optional[Dict[str, str]] = None

    # Scaffolded pending-API payloads — present-but-silent until keys configured
    flights: Optional[Dict[str, Any]] = None
    trains: Optional[Dict[str, Any]] = None
    hotel_deals: Optional[Dict[str, Any]] = None
    traffic: Optional[Dict[str, Any]] = None
    weather_forecast: Optional[Dict[str, Any]] = None

    # Final AI review of the assembled plan
    review: Optional[Dict[str, Any]] = None

    # Architect's full structured plan (day themes, excluded, gear, tips, lead times)
    architect_plan: Optional[Dict[str, Any]] = None

    # Per-event fatigue model output for the timeline gauges
    fatigue_per_event: Optional[Dict[str, Any]] = None

    # DuckDuckGo insights — extra context per destination/hotel/activity
    insights_per_place: Optional[Dict[str, Any]] = None

    # Terminal info — airports/stations with first/last mile travel times
    terminal_info: Optional[Dict[str, Any]] = None

    # Per-segment road polylines (ORS-routed) for drawing real directions
    segment_polylines: Optional[List[Dict[str, Any]]] = None


class RefinementQuestionsResponse(BaseModel):
    """Response for POST /api/refinement-questions.

    Exactly 4 questions, each renderable as a yes/no toggle or a checkbox grid.
    """

    questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Frozen schema: [{id, prompt, kind, options, default, why_it_matters}, ...]",
    )


class DelaySimulationResponse(BaseModel):
    """Response for POST /api/simulate-delay."""

    updated_itinerary: Optional[Dict[str, Any]] = None
    changes: Optional[List[str]] = None
    validation_report: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = ""


class ErrorResponse(BaseModel):
    """Standard error response shape for 4xx/5xx responses."""

    error: str
    detail: str = ""
