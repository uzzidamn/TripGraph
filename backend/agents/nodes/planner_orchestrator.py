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

# Last-resort fallback if neither the KG nor ORS can resolve the origin city.
# Gurugram is the most common origin in the seed data but no longer assumed.
_FALLBACK_ORIGIN_LAT = 28.4595
_FALLBACK_ORIGIN_LNG = 77.0266


def _origin_coords(route: dict, constraints: dict) -> tuple[float, float]:
    """Resolve origin lat/lng, in priority order:
       1. route.origin_lat / route.origin_lng  (set by data_retriever from KG)
       2. ORS geocode of the named origin city
       3. Hardcoded fallback (Gurugram)
    Caches geocode hits implicitly via the KG-write path inside route_tool.
    """
    if route.get("origin_lat") is not None and route.get("origin_lng") is not None:
        return float(route["origin_lat"]), float(route["origin_lng"])
    origin_name = route.get("origin") or constraints.get("origin")
    if origin_name:
        try:
            from backend.api_clients.ors_client import ORSClient
            geo = ORSClient.geocode(origin_name)
            if geo:
                return float(geo["lat"]), float(geo["lng"])
        except Exception as e:
            print(f"  ⚠️  ORS geocode for origin '{origin_name}' failed: {e}")
    return _FALLBACK_ORIGIN_LAT, _FALLBACK_ORIGIN_LNG


def _extract_map_points(itinerary: dict, constraints: dict | None = None) -> list[dict]:
    """Extract lat/lng points from an itinerary for Leaflet map rendering.

    Each point carries a stable `id` (e.g. "origin:Chandigarh", "hotel:<id>")
    so the frontend can sync map markers ↔ timeline cards by id.
    """
    points: list[dict] = []
    route = itinerary.get("route") or {}
    hotel = itinerary.get("hotel") or {}
    activities = itinerary.get("activities") or []
    waypoints = itinerary.get("waypoints") or []

    olat, olng = _origin_coords(route, constraints or {})
    origin_label = route.get("origin") or (constraints or {}).get("origin") or "Origin"
    points.append({
        "id": f"origin:{origin_label}",
        "lat": olat,
        "lng": olng,
        "label": origin_label,
        "type": "origin",
    })

    # Waypoints — ordered stops on the route
    for wp in sorted(waypoints, key=lambda w: w.get("order", 0)):
        if wp.get("lat") and wp.get("lng"):
            wid = wp.get("waypoint_id") or wp.get("name") or "wp"
            points.append({
                "id": f"waypoint:{wid}",
                "lat": wp["lat"],
                "lng": wp["lng"],
                "label": wp.get("name", "Waypoint"),
                "type": "waypoint",
            })

    # Destination city
    if route.get("dest_lat") and route.get("dest_lng"):
        dest_label = route.get("destination", "Destination")
        points.append({
            "id": f"destination:{dest_label}",
            "lat": route["dest_lat"],
            "lng": route["dest_lng"],
            "label": dest_label,
            "type": "destination",
        })

    # Hotel
    if hotel.get("lat") and hotel.get("lng"):
        points.append({
            "id": f"hotel:{hotel.get('hotel_id') or hotel.get('name', 'hotel')}",
            "lat": hotel["lat"],
            "lng": hotel["lng"],
            "label": hotel.get("name", "Hotel"),
            "type": "hotel",
        })

    # Activities
    for act in activities:
        if act.get("lat") and act.get("lng"):
            aid = act.get("activity_id") or act.get("name", "activity")
            points.append({
                "id": f"activity:{aid}",
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
    timeline = generate_timeline(selected, constraints)
    map_points = _extract_map_points(selected, constraints)

    # Stamp each timeline event with the matching map point_id so the
    # frontend can sync timeline ↔ map by a single key.
    point_by_label = {p.get("label"): p.get("id") for p in map_points if p.get("id")}
    for ev in timeline:
        title = ev.get("title") or ""
        for label, pid in point_by_label.items():
            if label and label.lower() in title.lower():
                ev["point_id"] = pid
                break

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
