"""Pydantic request models for all API endpoints."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ParseChatRequest(BaseModel):
    """Request body for POST /api/parse-chat."""

    chat_messages: List[str] = Field(
        ...,
        min_length=1,
        description="List of group chat messages to extract constraints from",
        json_schema_extra={
            "examples": [
                ["Let's go from Gurugram", "Budget under 15k", "Mountains please",
                 "No night driving", "Need rafting and good cafes"]
            ]
        },
    )


class GenerateItineraryRequest(BaseModel):
    """Request body for POST /api/generate-itinerary."""

    constraints: Dict[str, Any] = Field(
        ...,
        description="Structured constraints dict (from /api/parse-chat or provided directly)",
        json_schema_extra={
            "examples": [{
                "origin": "Gurugram",
                "destination_type": "mountains",
                "budget_per_person": 15000,
                "avoid_night_driving": True,
                "must_include": ["rafting", "cafes"],
                "return_deadline": "Monday morning",
                "hotel_tier": "comfort",
                "group_size": 4,
            }]
        },
    )
    refinement_answers: Optional[Dict[str, Any]] = Field(
        None,
        description="Answers to the 4 LLM-generated refinement questions, "
                    "keyed by question id. Merged into constraints before planning.",
    )


class RefinementQuestionsRequest(BaseModel):
    """Request body for POST /api/refinement-questions."""

    constraints: Dict[str, Any] = Field(
        ...,
        description="Constraints dict from /api/parse-chat",
    )
    assumptions: Optional[Dict[str, Any]] = Field(
        None,
        description="Already-assumed values so the LLM doesn't re-ask",
    )


class SimulateDelayRequest(BaseModel):
    """Request body for POST /api/simulate-delay."""

    delay_type: str = Field(
        ...,
        description="Type of delay event (e.g. departure_delay, traffic_delay)",
        json_schema_extra={"examples": ["departure_delay"]},
    )
    delay_minutes: int = Field(
        ...,
        ge=15,
        le=300,
        description="Delay duration in minutes (15–300)",
        json_schema_extra={"examples": [90]},
    )
    constraints: Optional[Dict[str, Any]] = Field(
        None,
        description="The trip constraints used for the original itinerary",
    )
    selected_itinerary: Optional[Dict[str, Any]] = Field(
        None,
        description="The full selected itinerary object to replan around the delay",
    )
