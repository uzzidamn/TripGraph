"""
POST /api/simulate-delay
Simulates a delay event and returns the updated, replanned itinerary.
"""
import traceback

from fastapi import APIRouter, HTTPException

from backend.models.requests import SimulateDelayRequest
from backend.models.responses import DelaySimulationResponse

router = APIRouter(prefix="/api", tags=["Replanning"])


@router.post("/simulate-delay", response_model=DelaySimulationResponse)
async def simulate_delay(request: SimulateDelayRequest) -> DelaySimulationResponse:
    """Simulate a delay event and return the adjusted itinerary.

    Builds a minimal TripState from the request payload (the selected itinerary
    and constraints are passed through directly — no pipeline re-run needed).
    Calls run_replan_workflow which invokes the deterministic replanner and
    then asks the LLM to explain what changed.
    """
    try:
        # --- STUB MODE ---
        # Uncomment this block for frontend development without a live LLM.
        # return DelaySimulationResponse(
        #     updated_itinerary=request.selected_itinerary,
        #     changes=[
        #         "Breakfast shortened by 22 minutes",
        #         "Lunch shortened by 15 minutes",
        #         "Rest period reduced by 30 minutes",
        #     ],
        #     validation_report={"is_valid": True, "hard_constraint_violations": [], "soft_constraint_warnings": []},
        #     explanation="The plan absorbs the delay by compressing flexible events. Rafting and return are preserved.",
        # )

        from backend.agents.workflow import run_replan_workflow

        # Build a TripState-compatible dict from the request
        # Only selected_itinerary and extracted_constraints are needed by the replanner node
        state = {
            "raw_chat": [],
            "extracted_constraints": request.constraints or {},
            "missing_fields": [],
            "assumptions": {},
            "conflict_report": {},
            "is_ready_to_plan": True,
            "route_candidates": [],
            "hotel_candidates": [],
            "transport_candidates": [],
            "activity_candidates": [],
            "food_candidates": [],
            "waypoint_candidates": [],
            "itinerary_candidates": [],
            "selected_itinerary": request.selected_itinerary,
            "alternative_itineraries": [],
            "validation_report": {},
            "score_breakdown": {},
            "timeline": [],
            "map_points": [],
            "cost_breakdown": {},
            "explanation": "",
            "delay_event": None,
            "replanned_itinerary": None,
            "replanning_explanation": None,
        }

        delay_event = {
            "delay_type": request.delay_type,
            "delay_minutes": request.delay_minutes,
        }

        result = run_replan_workflow(state, delay_event)

        # Extract the changes list — replanner stores it inside the updated_itinerary dict
        replanned = result.get("replanned_itinerary") or {}
        changes = replanned.pop("changes", []) if isinstance(replanned, dict) else []

        return DelaySimulationResponse(
            updated_itinerary=replanned,
            changes=changes,
            validation_report=result.get("validation_report", {}),
            explanation=result.get("replanning_explanation", ""),
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
