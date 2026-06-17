"""Pydantic response models for all API endpoints."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ParseChatResponse(BaseModel):
    """Response for POST /api/parse-chat."""

    extracted_constraints: Dict[str, Any] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    conflict_report: Optional[Dict[str, Any]] = None


class ItineraryResponse(BaseModel):
    """Response for POST /api/generate-itinerary."""

    recommended_itinerary: Optional[Dict[str, Any]] = None
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    validation_report: Optional[Dict[str, Any]] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    map_points: List[Dict[str, Any]] = Field(default_factory=list)
    cost_breakdown: Optional[Dict[str, Any]] = None
    explanation: str = ""


class DelaySimulationResponse(BaseModel):
    """Response for POST /api/simulate-delay."""

    updated_itinerary: Optional[Dict[str, Any]] = None
    changes: List[str] = Field(default_factory=list)
    validation_report: Optional[Dict[str, Any]] = None
    explanation: str = ""


class ErrorResponse(BaseModel):
    """Standard error response shape for 4xx/5xx responses."""

    error: str
    detail: str = ""
