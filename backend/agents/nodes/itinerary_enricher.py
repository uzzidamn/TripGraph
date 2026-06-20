import json
from langchain_core.messages import SystemMessage, HumanMessage
from backend.agents.llm_client import get_llm, extract_text_content
from backend.agents.prompts import ENRICHER_SYSTEM, ENRICHER_HUMAN
from backend.agents.state import TripState

def itinerary_enricher_node(state: TripState) -> dict:
    llm = get_llm()
    itinerary = state.get("selected_itinerary")
    if not itinerary:
        return {"enrichment_applied": False}
        
    constraints = state.get("extracted_constraints", {})
    timeline = state.get("timeline", [])

    # Detect time gaps in the timeline
    time_gaps = _find_time_gaps(timeline, threshold_minutes=90)

    # Build group profile string for the LLM
    group_profile = {
        "size": constraints.get("group_size", 4),
        "budget_per_person": constraints.get("budget_per_person"),
        "hotel_tier": constraints.get("hotel_tier", "comfort"),
        "must_include": constraints.get("must_include", []),
        "risk_tolerance": constraints.get("risk_tolerance", "medium")
    }

    response = llm.invoke([
        SystemMessage(content=ENRICHER_SYSTEM),
        HumanMessage(content=ENRICHER_HUMAN.format(
            destination=itinerary.get("route", {}).get("destination"),
            group_profile=json.dumps(group_profile),
            itinerary_skeleton=json.dumps(itinerary, indent=2),
            hotel_candidates=json.dumps(state.get("hotel_candidates", []), indent=2),
            time_gaps=json.dumps(time_gaps),
            drive_minutes=itinerary.get("route", {}).get("base_drive_minutes", 0)
        ))
    ])

    content_str = extract_text_content(response.content)
    try:
        enrichment = json.loads(content_str)
    except json.JSONDecodeError:
        if "```json" in content_str:
            content_str = content_str.split("```json")[1].split("```")[0]
        try:
            enrichment = json.loads(content_str.strip())
        except json.JSONDecodeError:
            enrichment = {}

    # Apply hotel selection from LLM recommendation
    selected_hotel_id = enrichment.get("selected_hotel", {}).get("hotel_id")
    if selected_hotel_id:
        matched = next(
            (h for h in state.get("hotel_candidates", []) if h.get("hotel_id") == selected_hotel_id),
            itinerary.get("hotel")  # fallback to KG-selected
        )
        itinerary["hotel"] = matched
        itinerary["hotel_selection_reason"] = enrichment.get("selected_hotel", {}).get("reason")

    # Attach enrichment data to itinerary
    itinerary["advisory_items"] = enrichment.get("advisory_items", [])
    itinerary["suggested_fillers"] = enrichment.get("suggested_fillers", [])
    itinerary["route_micro_stops"] = enrichment.get("route_micro_stops", [])
    itinerary["local_tips"] = enrichment.get("local_tips", [])

    return {
        "selected_itinerary": itinerary,
        "enrichment_applied": True
    }


def _find_time_gaps(timeline: list, threshold_minutes: int = 90) -> list:
    """Detect unscheduled gaps > threshold in the timeline."""
    from datetime import datetime
    gaps = []
    for i in range(len(timeline) - 1):
        end_time_str = timeline[i].get("end_time")
        start_time_str = timeline[i+1].get("start_time")
        if not end_time_str or not start_time_str:
            continue
            
        try:
            end = datetime.strptime(end_time_str, "%H:%M")
            start = datetime.strptime(start_time_str, "%H:%M")
            gap = (start - end).seconds // 60
            if gap > threshold_minutes:
                gaps.append({
                    "after_event": timeline[i].get("title"),
                    "gap_minutes": gap
                })
        except ValueError:
            pass
            
    return gaps
