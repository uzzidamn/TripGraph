"""
Score itinerary candidates using a multi-objective function.
Higher score = better itinerary.
"""

def score_itinerary(itinerary: dict, constraints: dict) -> dict:
    """
    Score an itinerary candidate.
    Returns a dict with individual scores and final_score.
    """
    scores = {}

    # 1. Preference match (0-25 points)
    # Full marks when no must_include specified — absence of preference is not a mismatch.
    raw_must_include = constraints.get("must_include") or []
    must_include = {str(x).lower() for x in raw_must_include if x}

    if not must_include:
        scores["preference_match"] = 25
    else:
        activity_tags = set()
        for act in itinerary.get("activities", []):
            for tag in (act.get("tags") or []):
                activity_tags.add(str(tag).lower())
            if act.get("name"):
                activity_tags.add(act.get("name").lower())
        matched = must_include & activity_tags
        scores["preference_match"] = (len(matched) / len(must_include)) * 25

    # 2. Budget efficiency (0-20 points)
    budget = constraints.get("budget_per_person", 15000)
    if budget is None:
        budget = 15000
    cost = itinerary.get("total_cost_per_person", 0)
    if budget > 0 and cost <= budget:
        scores["budget_efficiency"] = ((budget - cost) / budget) * 20
    else:
        scores["budget_efficiency"] = 0

    # 3. Comfort score (0-15 points)
    hotel_comfort = itinerary.get("hotel", {}).get("comfort_score")
    if hotel_comfort is None:
        hotel_comfort = 5
    transport_comfort = itinerary.get("transport", {}).get("comfort_score")
    if transport_comfort is None:
        transport_comfort = 5
        
    scores["comfort"] = ((hotel_comfort + transport_comfort) / 2) * 1.5

    # 4. Scenic score (0-10 points)
    scenic = itinerary.get("route", {}).get("scenic_score")
    if scenic is None:
        scenic = 5
    scores["scenic"] = scenic

    # 5. Fatigue penalty (0-15 points, lower fatigue = higher score)
    fatigue = itinerary.get("transport", {}).get("fatigue_score")
    if fatigue is None:
        fatigue = 5
    scores["fatigue"] = max(0, (10 - fatigue)) * 1.5

    # 6. Risk penalty (0-10 points, lower risk = higher score)
    risk_map = {"low": 10, "medium": 6, "high": 3}
    route_risk = itinerary.get("route", {}).get("risk_level", "medium")
    scores["risk"] = risk_map.get(route_risk if route_risk else "medium", 5)

    # 7. Night driving penalty
    avoid_night = constraints.get("avoid_night_driving")
    night_allowed = itinerary.get("transport", {}).get("night_driving_allowed")
    if avoid_night and night_allowed:
        scores["night_driving_penalty"] = -20
    else:
        scores["night_driving_penalty"] = 0

    scores["final_score"] = sum(scores.values())
    return scores
