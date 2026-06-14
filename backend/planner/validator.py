"""
Validate itinerary against hard and soft constraints.
"""

def validate_itinerary(itinerary: dict, constraints: dict) -> dict:
    """
    Check hard and soft constraints. Returns validation report.
    """
    hard_violations = []
    soft_warnings = []

    cost = itinerary.get("total_cost_per_person", 0)
    budget = constraints.get("budget_per_person")
    if budget is None:
        budget = float("inf")

    # Hard: Budget
    if cost > budget:
        hard_violations.append(f"Cost ₹{cost:,.0f} exceeds budget ₹{budget:,.0f}")

    # Hard: Night driving
    if constraints.get("avoid_night_driving"):
        transport = itinerary.get("transport", {})
        if transport.get("night_driving_allowed") and transport.get("mode") == "self_drive":
            hard_violations.append("Self-drive with night driving conflicts with 'no night driving' constraint")

    # Hard: Must-include activities
    raw_must_include = constraints.get("must_include") or []
    must_include = {str(x).lower() for x in raw_must_include if x}
    
    available_tags = set()
    for act in itinerary.get("activities", []):
        for tag in (act.get("tags") or []):
            available_tags.add(str(tag).lower())
        if act.get("name"):
            available_tags.add(act.get("name").lower())
            
    missing = must_include - available_tags
    if missing:
        hard_violations.append(f"Missing required activities: {', '.join(missing)}")

    # Hard: Destination type mismatch
    dest_type = constraints.get("destination_type")
    route_dest_type = itinerary.get("route", {}).get("destination_type")
    if dest_type and route_dest_type and str(dest_type).lower() != str(route_dest_type).lower():
        hard_violations.append(f"Destination type '{route_dest_type}' does not match preference '{dest_type}'")

    # Soft: Comfort level
    comfort_score = itinerary.get("hotel", {}).get("comfort_score")
    if comfort_score is None:
        comfort_score = 10
    if comfort_score < 5:
        soft_warnings.append("Hotel comfort is below average")

    return {
        "is_valid": len(hard_violations) == 0,
        "hard_constraint_violations": hard_violations,
        "soft_constraint_warnings": soft_warnings,
        "budget_used": cost,
        "budget_limit": budget,
        "must_include_satisfied": list(must_include - missing) if must_include else [],
    }
