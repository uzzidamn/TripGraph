"""
Agent 4: Planner Orchestrator
Coordinates the deterministic planning engine: generates candidates, scores,
validates, selects the best itinerary, builds timeline and map points.

No LLM call. All logic is deterministic Python via the planner modules.
"""
from backend.agents.state import TripState
from backend.planner.candidate_generator import generate_candidates
from backend.planner.scorer import score_itinerary
from backend.planner.timeline_generator import generate_timeline
from backend.planner.validator import validate_itinerary

# Gurugram origin coordinates (hardcoded — it is the only origin in scope)
_GURUGRAM_LAT = 28.4595
_GURUGRAM_LNG = 77.0266


def _extract_map_points(itinerary: dict) -> list[dict]:
    """Extract lat/lng points from an itinerary for Leaflet map rendering.

    Returns list of {lat, lng, label, type} dicts.
    Types: "origin", "waypoint", "destination", "hotel", "activity"
    """
    points: list[dict] = []
    route = itinerary.get("route") or {}
    hotel = itinerary.get("hotel") or {}
    activities = itinerary.get("activities") or []
    waypoints = itinerary.get("waypoints") or []

    # Origin — always Gurugram
    points.append({
        "lat": _GURUGRAM_LAT,
        "lng": _GURUGRAM_LNG,
        "label": route.get("origin", "Gurugram"),
        "type": "origin",
    })

    # Waypoints — ordered stops on the route
    for wp in sorted(waypoints, key=lambda w: w.get("order", 0)):
        if wp.get("lat") and wp.get("lng"):
            points.append({
                "lat": wp["lat"],
                "lng": wp["lng"],
                "label": wp.get("name", "Waypoint"),
                "type": "waypoint",
            })

    # Destination city
    if route.get("dest_lat") and route.get("dest_lng"):
        points.append({
            "lat": route["dest_lat"],
            "lng": route["dest_lng"],
            "label": route.get("destination", "Destination"),
            "type": "destination",
        })

    # Hotel
    if hotel.get("lat") and hotel.get("lng"):
        points.append({
            "lat": hotel["lat"],
            "lng": hotel["lng"],
            "label": hotel.get("name", "Hotel"),
            "type": "hotel",
        })

    # Activities
    for act in activities:
        if act.get("lat") and act.get("lng"):
            points.append({
                "lat": act["lat"],
                "lng": act["lng"],
                "label": act.get("name", "Activity"),
                "type": "activity",
            })

    return points


def planner_orchestrator_node(state: TripState) -> dict:
    """Generate, score, validate, and select the best itinerary.

    Candidate generation crosses: routes × transport × hotels × activities.
    Sorting: valid candidates (by final_score desc) first, then invalid candidates.
    Falls back to best invalid candidate if no valid candidates exist.
    """
    constraints = state["extracted_constraints"]

    # Pack retrieved data into the shape candidate_generator expects
    data = {
        "routes": state["route_candidates"],
        "hotels": state["hotel_candidates"],
        "transport": state["transport_candidates"],
        "activities": state["activity_candidates"],
        "food": state["food_candidates"],
        "waypoints": state["waypoint_candidates"],
    }

    # Generate all candidate combinations
    candidates = generate_candidates(constraints, data)

    if not candidates:
        print("  ⚠️  Planner: no candidates generated")
        return {
            "itinerary_candidates": [],
            "selected_itinerary": None,
            "alternative_itineraries": [],
            "validation_report": {"is_valid": False, "hard_constraint_violations": ["No candidates generated"]},
            "score_breakdown": {},
            "timeline": [],
            "map_points": [],
            "cost_breakdown": {},
        }

    # Score and validate every candidate
    scored: list[dict] = []
    for candidate in candidates:
        scores = score_itinerary(candidate, constraints)
        validation = validate_itinerary(candidate, constraints)
        scored.append({
            **candidate,
            "_score_breakdown": scores,
            "_validation_report": validation,
            "_final_score": scores.get("final_score", 0),
            "_is_valid": validation.get("is_valid", False),
        })

    # Sort: valid first (score desc), then invalid (score desc)
    valid = sorted([c for c in scored if c["_is_valid"]], key=lambda c: c["_final_score"], reverse=True)
    invalid = sorted([c for c in scored if not c["_is_valid"]], key=lambda c: c["_final_score"], reverse=True)
    sorted_candidates = valid + invalid

    selected = sorted_candidates[0]
    alternatives = sorted_candidates[1:4]  # up to 3 alternatives

    # Build timeline and map points for the selected itinerary
    timeline = generate_timeline(selected)
    map_points = _extract_map_points(selected)

    # Strip internal scoring keys from the selected itinerary before storing
    score_breakdown = selected.pop("_score_breakdown", {})
    validation_report = selected.pop("_validation_report", {})
    selected.pop("_final_score", None)
    selected.pop("_is_valid", None)
    # Remove non-serializable trip_graph from stored state
    selected.pop("trip_graph", None)

    # Clean alternatives too
    clean_alternatives = []
    for alt in alternatives:
        alt.pop("_score_breakdown", None)
        alt.pop("_validation_report", None)
        alt.pop("_final_score", None)
        alt.pop("_is_valid", None)
        alt.pop("trip_graph", None)
        clean_alternatives.append(alt)

    cost_breakdown = selected.get("cost_breakdown", {})

    print(f"  ✅ Planner: {len(candidates)} candidates, selected='{selected.get('destination')}' "
          f"({selected.get('transport', {}).get('tier')} tier), "
          f"valid={validation_report.get('is_valid')}, "
          f"cost=₹{cost_breakdown.get('total', 0):,}/person, "
          f"{len(timeline)} timeline events, {len(map_points)} map points")

    return {
        "itinerary_candidates": [c for c in sorted_candidates[:5]],
        "selected_itinerary": selected,
        "alternative_itineraries": clean_alternatives,
        "validation_report": validation_report,
        "score_breakdown": score_breakdown,
        "timeline": timeline,
        "map_points": map_points,
        "cost_breakdown": cost_breakdown,
    }
