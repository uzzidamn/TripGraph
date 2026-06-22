"""
Agent 4: generate, score, validate, and select itinerary candidates.
"""
from backend.agents.state import TripState
from backend.planner.candidate_generator import generate_candidates
from backend.planner.scorer import score_itinerary
from backend.planner.validator import validate_itinerary
from backend.planner.timeline_generator import generate_timeline


def _extract_map_points(itinerary: dict) -> list[dict]:
    points = []
    route = itinerary.get("route") or {}
    hotel = itinerary.get("hotel") or {}
    activities = itinerary.get("activities") or []
    waypoints = itinerary.get("waypoints") or []

    # Origin (Gurugram coords — not in route data)
    points.append({
        "lat": 28.4595, "lng": 77.0266,
        "label": route.get("origin", "Gurugram"), "type": "origin",
    })

    # Waypoints
    for wp in waypoints:
        if wp.get("lat") and wp.get("lng"):
            points.append({
                "lat": wp["lat"], "lng": wp["lng"],
                "label": wp.get("name", "Waypoint"), "type": "waypoint",
            })

    # Destination
    if route.get("dest_lat") and route.get("dest_lng"):
        points.append({
            "lat": route["dest_lat"], "lng": route["dest_lng"],
            "label": route.get("destination", "Destination"), "type": "destination",
        })

    # Hotel
    if hotel.get("lat") and hotel.get("lng"):
        points.append({
            "lat": hotel["lat"], "lng": hotel["lng"],
            "label": hotel.get("name", "Hotel"), "type": "hotel",
        })

    # Activities
    for act in activities:
        if act.get("lat") and act.get("lng"):
            points.append({
                "lat": act["lat"], "lng": act["lng"],
                "label": act.get("name", "Activity"), "type": "activity",
            })

    return points


def planner_orchestrator_node(state: TripState) -> dict:
    constraints = state.get("extracted_constraints") or {}
    conflict_report = dict(state.get("conflict_report") or {})
    memory_context = dict(state.get("memory_context") or {})

    # route_retriever already applied dedup; if all routes were visited it returns []
    # and we fall back to all_route_candidates so the planner can still produce a plan
    routes = list(state.get("route_candidates") or [])
    if not routes:
        routes = list(state.get("all_route_candidates") or [])
        if routes:
            memory_context["all_candidates_visited"] = True

    data = {
        "routes": routes,
        "hotels": state.get("hotel_candidates") or [],
        "transport": state.get("transport_candidates") or [],
        "activities": state.get("activity_candidates") or [],
        "food": state.get("food_candidates") or [],
        "waypoints": state.get("waypoint_candidates") or [],
    }

    candidates = generate_candidates(constraints, data)

    scored: list[tuple[dict, dict, dict]] = []
    for candidate in candidates:
        score = score_itinerary(candidate, constraints)
        validation = validate_itinerary(candidate, constraints)
        scored.append((candidate, score, validation))

    # Sort: valid first (by final_score desc), then invalid
    valid = [(c, s, v) for c, s, v in scored if v.get("is_valid")]
    invalid = [(c, s, v) for c, s, v in scored if not v.get("is_valid")]
    valid.sort(key=lambda x: x[1].get("final_score", 0), reverse=True)
    invalid.sort(key=lambda x: x[1].get("final_score", 0), reverse=True)
    sorted_all = valid + invalid

    if not sorted_all:
        return {
            "itinerary_candidates": [],
            "selected_itinerary": None,
            "alternative_itineraries": [],
            "validation_report": {"is_valid": False, "error": "no_candidates_generated"},
            "score_breakdown": {},
            "timeline": [],
            "map_points": [],
            "cost_breakdown": {},
            "conflict_report": conflict_report,
        }

    best_candidate, best_score, best_validation = sorted_all[0]

    # Budget exceeded warning (Decision 26)
    if not best_validation.get("is_valid"):
        violations = best_validation.get("hard_constraint_violations", [])
        budget_violation = any("budget" in str(v).lower() or "cost" in str(v).lower() for v in violations)
        if budget_violation:
            conflict_report.setdefault("warnings", []).append({
                "type": "budget_exceeded",
                "field": "budget_per_person",
                "description": str(violations[0]) if violations else "Selected itinerary exceeds budget.",
                "suggestion": "Increase budget or reduce group size.",
            })
            conflict_report["has_conflicts"] = True

    # must_include not satisfiable warning (Decision 27)
    must_include = [str(x).lower() for x in (constraints.get("must_include") or [])]
    if must_include:
        all_activity_names = [str(a.get("name", "")).lower() for a in (best_candidate.get("activities") or [])]
        all_activity_tags = [str(t).lower() for a in (best_candidate.get("activities") or []) for t in (a.get("tags") or [])]
        for item in must_include:
            matched = any(item in name for name in all_activity_names) or any(item in tag for tag in all_activity_tags)
            if not matched:
                conflict_report.setdefault("warnings", []).append({
                    "type": "must_include_unavailable",
                    "field": "must_include",
                    "description": f"No activity found matching '{item}' at {best_candidate.get('destination', 'destination')}.",
                    "suggestion": "Consider removing this requirement or choosing a different destination.",
                })
                conflict_report["has_conflicts"] = True

    timeline = generate_timeline(best_candidate)
    map_points = _extract_map_points(best_candidate)
    cost_breakdown = best_candidate.get("cost_breakdown") or {}
    alternatives = [c for c, _, _ in sorted_all[1:4]]

    return {
        "itinerary_candidates": [c for c, _, _ in sorted_all],
        "selected_itinerary": best_candidate,
        "alternative_itineraries": alternatives,
        "validation_report": best_validation,
        "score_breakdown": best_score,
        "timeline": timeline,
        "map_points": map_points,
        "cost_breakdown": cost_breakdown,
        "conflict_report": conflict_report,
        "memory_context": memory_context,
    }
