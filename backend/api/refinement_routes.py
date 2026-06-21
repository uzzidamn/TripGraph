"""
POST /api/refinement-questions
Generates 1 round of 4 LLM-tailored counter-questions to sharpen the trip plan
before the user kicks off /api/generate-itinerary.

This is a thin wrapper around `refinement_questioner_node` — no graph, no
side-effects on the planner state.
"""
import traceback

from fastapi import APIRouter, HTTPException

from backend.agents.nodes.refinement_questioner import refinement_questioner_node
from backend.agents.state import initialize_state
from backend.models.requests import RefinementQuestionsRequest
from backend.models.responses import RefinementQuestionsResponse

router = APIRouter(prefix="/api", tags=["Refinement"])


@router.post("/refinement-questions", response_model=RefinementQuestionsResponse)
async def refinement_questions(request: RefinementQuestionsRequest) -> RefinementQuestionsResponse:
    """Return exactly 4 follow-up questions tailored to the given constraints."""
    try:
        state = initialize_state([])
        state["extracted_constraints"] = request.constraints
        state["assumptions"] = request.assumptions or {}
        result = refinement_questioner_node(state)
        return RefinementQuestionsResponse(questions=result.get("refinement_questions", []))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
