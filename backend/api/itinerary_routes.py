"""
POST /api/generate-itinerary
Generates scored, validated itineraries from a constraints dict.
Runs the full agentic pipeline: data retrieval → planning → scoring → explanation.
"""
import traceback
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.models.requests import GenerateItineraryRequest
from backend.models.responses import ItineraryResponse

router = APIRouter(prefix="/api", tags=["Itinerary"])


def _constraints_to_chat(constraints: dict[str, Any]) -> list[str]:
    """Convert a structured constraints dict into synthetic chat messages.

    The LangGraph pipeline always enters via run_workflow(chat_messages).
    When /generate-itinerary receives a pre-built constraints dict (not raw chat),
    we synthesize natural-language sentences so the chat parser can re-extract them.
    This preserves the single pipeline entry point and avoids duplicating extraction logic.
    """
    messages: list[str] = []

    if constraints.get("origin"):
        messages.append(f"We want to travel from {constraints['origin']}")
    if constraints.get("destination"):
        messages.append(f"We want to go to {constraints['destination']}")
    if constraints.get("destination_type"):
        messages.append(f"Prefer {constraints['destination_type']} type destination")
    if constraints.get("budget_per_person"):
        messages.append(f"Budget is under {constraints['budget_per_person']} rupees per person")
    if constraints.get("trip_duration"):
        messages.append(f"Trip duration: {constraints['trip_duration']}")
    if constraints.get("avoid_night_driving"):
        messages.append("No night driving please, avoid driving after dark")
    if constraints.get("must_include"):
        items = ", ".join(constraints["must_include"])
        messages.append(f"Must include: {items}")
    if constraints.get("return_deadline"):
        messages.append(f"Need to return by {constraints['return_deadline']}")
    if constraints.get("hotel_tier"):
        messages.append(f"Hotel preference is {constraints['hotel_tier']} tier")
    if constraints.get("group_size"):
        messages.append(f"We are a group of {constraints['group_size']} people")
    if constraints.get("risk_tolerance"):
        messages.append(f"Risk tolerance is {constraints['risk_tolerance']}")
    if constraints.get("transport_preference"):
        prefs = ", ".join(constraints["transport_preference"])
        messages.append(f"Transport preference: {prefs}")
    for req in constraints.get("special_requirements", []):
        messages.append(str(req))

    return messages if messages else ["Plan a weekend trip from Gurugram"]


@router.post("/generate-itinerary", response_model=ItineraryResponse)
async def generate_itinerary(request: GenerateItineraryRequest) -> ItineraryResponse:
    """Generate scored, validated itineraries from a structured constraints dict.

    Converts constraints to synthetic chat, runs the full pipeline, and returns
    the recommended itinerary with timeline, map points, cost breakdown, and explanation.
    """
    try:
        # --- STUB MODE ---
        # Uncomment this block for frontend development without a live LLM.
        # return ItineraryResponse(
        #     recommended_itinerary={
        #         "route": {
        #             "route_id": "gurugram_rishikesh_2d1n",
        #             "origin": "Gurugram",
        #             "destination": "Rishikesh",
        #             "distance_km": 260,
        #             "destination_type": "mountains",
        #         },
        #         "transport": {"mode": "cab_with_driver", "tier": "comfort", "cost_total": 9500},
        #         "hotel": {"name": "Riverside Comfort Stay", "price_per_night": 4200},
        #         "activities": [{"name": "White Water Rafting (16 km)", "cost_per_person": 1800}],
        #         "total_cost_per_person": 10275,
        #         "destination": "Rishikesh",
        #     },
        #     alternatives=[],
        #     validation_report={"is_valid": True, "hard_constraint_violations": [], "soft_constraint_warnings": []},
        #     score_breakdown={"final_score": 66.8},
        #     timeline=[
        #         {"day": 1, "start_time": "06:00", "end_time": "09:00", "title": "Drive from Gurugram", "type": "travel"},
        #         {"day": 2, "start_time": "15:00", "end_time": "21:30", "title": "Return to Gurugram", "type": "travel"},
        #     ],
        #     map_points=[
        #         {"lat": 28.4595, "lng": 77.0266, "label": "Gurugram", "type": "origin"},
        #         {"lat": 30.0869, "lng": 78.2676, "label": "Rishikesh", "type": "destination"},
        #     ],
        #     cost_breakdown={"transport": 2375, "hotel": 1050, "activities": 1800, "food": 1050, "miscellaneous": 2000, "total": 10275},
        #     explanation="Stub: Rishikesh comfort itinerary within ₹15,000 budget.",
        # )

        from backend.agents.workflow import run_workflow_from_constraints
        from backend.agents.nodes.refinement_questioner import apply_refinement_answers

        constraints = apply_refinement_answers(
            request.constraints,
            request.refinement_answers or {},
        )

        result = run_workflow_from_constraints(constraints)

        return ItineraryResponse(
            unsupported_route=result.get("unsupported_route"),
            suggested_routes=result.get("suggested_routes", []),
            guardrail_result=result.get("guardrail_result"),
            extracted_constraints=result.get("extracted_constraints", {}),
            missing_fields=result.get("missing_fields", []),
            assumptions=result.get("assumptions", {}),
            conflict_report=result.get("conflict_report", {}),
            is_ready_to_plan=result.get("is_ready_to_plan"),
            user_profile=result.get("user_profile"),
            memory_context=result.get("memory_context"),
            visited_destinations=result.get("visited_destinations", []),
            route_candidates=result.get("route_candidates", []),
            hotel_candidates=result.get("hotel_candidates", []),
            transport_candidates=result.get("transport_candidates", []),
            activity_candidates=result.get("activity_candidates", []),
            food_candidates=result.get("food_candidates", []),
            waypoint_candidates=result.get("waypoint_candidates", []),
            recommended_itinerary=result.get("selected_itinerary"),
            alternatives=result.get("alternative_itineraries", []),
            validation_report=result.get("validation_report", {}),
            score_breakdown=result.get("score_breakdown", {}),
            timeline=result.get("timeline", []),
            map_points=result.get("map_points", []),
            cost_breakdown=result.get("cost_breakdown", {}),
            explanation=result.get("explanation", ""),
            retrieval_passes=result.get("retrieval_passes", 0),
            retrieval_source=result.get("retrieval_source", {}),
            flights=result.get("flights"),
            trains=result.get("trains"),
            hotel_deals=result.get("hotel_deals"),
            traffic=result.get("traffic"),
            weather_forecast=result.get("weather_forecast", {}),
            fatigue_per_event=result.get("fatigue_per_event", {}),
            insights_per_place=result.get("insights_per_place", {}),
            review=result.get("review"),
            architect_plan=result.get("architect_plan"),
            terminal_info=result.get("terminal_info"),
            segment_polylines=result.get("segment_polylines") or [],
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
