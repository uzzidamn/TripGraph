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

# City → (lat, lng) lookup for origin pin placement
_CITY_COORDS: dict[str, tuple[float, float]] = {
    # India
    "gurugram": (28.4595, 77.0266), "gurgaon": (28.4595, 77.0266),
    "delhi": (28.6139, 77.2090), "new delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777), "pune": (18.5204, 73.8567),
    "bangalore": (12.9716, 77.5946), "bengaluru": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707), "hyderabad": (17.3850, 78.4867),
    "kolkata": (22.5726, 88.3639), "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873), "lucknow": (26.8467, 80.9462),
    "chandigarh": (30.7333, 76.7794), "kochi": (9.9312, 76.2673),
    "surat": (21.1702, 72.8311), "indore": (22.7196, 75.8577),
    "bhopal": (23.2599, 77.4126), "nagpur": (21.1458, 79.0882),
    "goa": (15.2993, 74.1240), "panaji": (15.4909, 73.8278),
    "rishikesh": (30.0869, 78.2676), "haridwar": (29.9457, 78.1642),
    "dehradun": (30.3165, 78.0322), "shimla": (31.1048, 77.1734),
    "manali": (32.2432, 77.1892), "leh": (34.1526, 77.5771),
    "srinagar": (34.0837, 74.7973), "darjeeling": (27.0360, 88.2627),
    "amritsar": (31.6340, 74.8723), "varanasi": (25.3176, 82.9739),
    "agra": (27.1767, 78.0081), "mathura": (27.4924, 77.6737),
    "udaipur": (24.5854, 73.7125), "jodhpur": (26.2389, 73.0243),
    "noida": (28.5355, 77.3910),
    # Americas
    "new york": (40.7128, -74.0060), "new york city": (40.7128, -74.0060),
    "nyc": (40.7128, -74.0060), "ny": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437), "la": (34.0522, -118.2437),
    "san francisco": (37.7749, -122.4194), "sf": (37.7749, -122.4194),
    "chicago": (41.8781, -87.6298), "houston": (29.7604, -95.3698),
    "miami": (25.7617, -80.1918), "seattle": (47.6062, -122.3321),
    "boston": (42.3601, -71.0589), "las vegas": (36.1699, -115.1398),
    "dallas": (32.7767, -96.7970), "washington": (38.9072, -77.0369),
    "dc": (38.9072, -77.0369), "toronto": (43.6532, -79.3832),
    "vancouver": (49.2827, -123.1207), "montreal": (45.5017, -73.5673),
    "honolulu": (21.3069, -157.8583),
    # Europe
    "london": (51.5074, -0.1278), "paris": (48.8566, 2.3522),
    "amsterdam": (52.3676, 4.9041), "berlin": (52.5200, 13.4050),
    "rome": (41.9028, 12.4964), "barcelona": (41.3851, 2.1734),
    "madrid": (40.4168, -3.7038), "vienna": (48.2082, 16.3738),
    "zurich": (47.3769, 8.5417), "prague": (50.0755, 14.4378),
    "lisbon": (38.7169, -9.1395), "dublin": (53.3498, -6.2603),
    "stockholm": (59.3293, 18.0686), "oslo": (59.9139, 10.7522),
    "copenhagen": (55.6761, 12.5683), "athens": (37.9838, 23.7275),
    "budapest": (47.4979, 19.0402),
    # Asia-Pacific
    "tokyo": (35.6762, 139.6503), "osaka": (34.6937, 135.5023),
    "singapore": (1.3521, 103.8198), "bangkok": (13.7563, 100.5018),
    "phuket": (7.8804, 98.3923), "bali": (-8.3405, 115.0920),
    "sydney": (-33.8688, 151.2093), "melbourne": (-37.8136, 144.9631),
    "brisbane": (-27.4698, 153.0251), "perth": (-31.9505, 115.8605),
    "adelaide": (-34.9285, 138.6007), "auckland": (-36.8485, 174.7633),
    "kuala lumpur": (3.1390, 101.6869), "hong kong": (22.3193, 114.1694),
    "beijing": (39.9042, 116.4074), "shanghai": (31.2304, 121.4737),
    "seoul": (37.5665, 126.9780),
    # Middle East & Africa
    "dubai": (25.2048, 55.2708), "abu dhabi": (24.4539, 54.3773),
    "cairo": (30.0444, 31.2357), "nairobi": (-1.2921, 36.8219),
    "cape town": (-33.9249, 18.4241), "johannesburg": (-26.2041, 28.0473),
    # South America
    "sao paulo": (-23.5505, -46.6333), "rio de janeiro": (-22.9068, -43.1729),
}


def _lookup_coords(city: str) -> tuple[float, float] | None:
    key = city.lower().strip()
    if key in _CITY_COORDS:
        return _CITY_COORDS[key]
    for name, coords in _CITY_COORDS.items():
        if name.startswith(key) or key.startswith(name):
            return coords
    return None


def _extract_map_points(itinerary: dict, origin: str | None = None) -> list[dict]:
    """Extract lat/lng points from an itinerary for Leaflet map rendering.

    Returns list of {lat, lng, label, type} dicts.
    Types: "origin", "waypoint", "destination", "hotel", "activity"
    """
    points: list[dict] = []
    route = itinerary.get("route") or {}
    hotel = itinerary.get("hotel") or {}
    activities = itinerary.get("activities") or []
    waypoints = itinerary.get("waypoints") or []

    # Origin — prefer coords from enriched route data, then fall back to lookup table
    origin_city = origin or route.get("origin", "")
    o_lat = route.get("origin_lat") or 0.0
    o_lng = route.get("origin_lng") or 0.0
    if not (o_lat and o_lng):
        fallback = _lookup_coords(origin_city)
        if fallback:
            o_lat, o_lng = fallback
    if o_lat and o_lng:
        points.append({
            "lat": o_lat,
            "lng": o_lng,
            "label": origin_city,
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
    timeline = generate_timeline(selected, constraints)
    map_points = _extract_map_points(selected, origin=constraints.get("origin"))

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
