"""Pydantic response models for all API endpoints."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ParseChatResponse(BaseModel):
    """Response for POST /api/parse-chat."""

    extracted_constraints: Optional[Dict[str, Any]] = None
    missing_fields: Optional[List[str]] = None
    assumptions: Optional[Dict[str, Any]] = None
    conflict_report: Optional[Dict[str, Any]] = None


class ItineraryResponse(BaseModel):
    """Response for POST /api/generate-itinerary."""

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
