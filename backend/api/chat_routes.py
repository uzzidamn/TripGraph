"""
POST /api/parse-chat
Parses group chat messages and extracts structured trip constraints.
Uses the Chat Parser + Constraint Validator agents from the LangGraph pipeline.
"""
import traceback

from fastapi import APIRouter, HTTPException

from backend.models.requests import ParseChatRequest
from backend.models.responses import ParseChatResponse

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/parse-chat", response_model=ParseChatResponse)
async def parse_chat(request: ParseChatRequest) -> ParseChatResponse:
    """Parse group chat messages and extract structured trip constraints.

    Runs the full workflow but returns only the constraint extraction portion.
    If is_ready_to_plan is False, returns missing_fields so the client can
    prompt the user for clarification.
    """
    try:
        # --- STUB MODE ---
        # Uncomment this block for frontend development without a live LLM.
        # return ParseChatResponse(
        #     extracted_constraints={
        #         "origin": "Gurugram",
        #         "destination": None,
        #         "destination_type": "mountains",
        #         "budget_per_person": 15000,
        #         "dates": None,
        #         "trip_duration": "2D1N",
        #         "transport_preference": ["cab_with_driver"],
        #         "avoid_night_driving": True,
        #         "must_include": ["rafting", "cafes"],
        #         "return_deadline": "Monday morning",
        #         "hotel_tier": "comfort",
        #         "risk_tolerance": "medium",
        #         "group_size": 4,
        #         "special_requirements": [],
        #     },
        #     missing_fields=[],
        #     assumptions={"group_size": "4 (default)", "risk_tolerance": "medium (default)"},
        #     conflict_report={"has_conflicts": False, "conflicts": []},
        # )

        from backend.agents.workflow import run_workflow

        result = run_workflow(request.chat_messages, user_id=request.user_id)
        return ParseChatResponse(
            guardrail_result=result.get("guardrail_result"),
            extracted_constraints=result.get("extracted_constraints", {}),
            missing_fields=result.get("missing_fields", []),
            assumptions=result.get("assumptions", {}),
            user_profile=result.get("user_profile"),
            memory_context=result.get("memory_context"),
            visited_destinations=result.get("visited_destinations", []),
            conflict_report=result.get("conflict_report", {}),
            is_ready_to_plan=result.get("is_ready_to_plan"),
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
