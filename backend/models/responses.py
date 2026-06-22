"""Pydantic response models for all API endpoints."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ParseChatResponse(BaseModel):
    """Response for POST /api/parse-chat — includes all agent stage outputs."""

    # Guardrail (Agent 0)
    guardrail_result: Optional[Dict[str, Any]] = None
    # Chat Parser (Agent 1)
    extracted_constraints: Optional[Dict[str, Any]] = None
    missing_fields: Optional[List[str]] = None
    assumptions: Optional[Dict[str, Any]] = None
    # Memory Agent (Agent 2)
    user_profile: Optional[Dict[str, Any]] = None
    memory_context: Optional[Dict[str, Any]] = None
    visited_destinations: Optional[List[str]] = None
    # Constraint Validator (Agent 3)
    conflict_report: Optional[Dict[str, Any]] = None
    is_ready_to_plan: Optional[bool] = None


class ItineraryResponse(BaseModel):
    unsupported_route: Optional[Dict[str, Any]] = None
    suggested_routes: Optional[List[Dict[str, Any]]] = None

    """Response for POST /api/generate-itinerary — includes all agent stage outputs."""

    # Guardrail (Agent 0)
    guardrail_result: Optional[Dict[str, Any]] = None
    # Chat Parser + Constraint Validator
    extracted_constraints: Optional[Dict[str, Any]] = None
    missing_fields: Optional[List[str]] = None
    assumptions: Optional[Dict[str, Any]] = None
    conflict_report: Optional[Dict[str, Any]] = None
    is_ready_to_plan: Optional[bool] = None
    # Memory Agent
    user_profile: Optional[Dict[str, Any]] = None
    memory_context: Optional[Dict[str, Any]] = None
    visited_destinations: Optional[List[str]] = None
    # Data Retrieval agents
    route_candidates: Optional[List[Dict[str, Any]]] = None
    hotel_candidates: Optional[List[Dict[str, Any]]] = None
    transport_candidates: Optional[List[Dict[str, Any]]] = None
    activity_candidates: Optional[List[Dict[str, Any]]] = None
    food_candidates: Optional[List[Dict[str, Any]]] = None
    waypoint_candidates: Optional[List[Dict[str, Any]]] = None
    # Planner
    itinerary_candidates: Optional[List[Dict[str, Any]]] = None
    recommended_itinerary: Optional[Dict[str, Any]] = None
    alternatives: Optional[List[Dict[str, Any]]] = None
    validation_report: Optional[Dict[str, Any]] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    map_points: Optional[List[Dict[str, Any]]] = None
    cost_breakdown: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = ""


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
