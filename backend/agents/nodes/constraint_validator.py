"""
Agent 2: validate extracted constraints — pure Python, no LLM call.
"""
from backend.agents.state import TripState

# Known destination → destination_type mapping for mismatch detection (Decision 25)
_DEST_TYPE_MAP: dict[str, str] = {
    "rishikesh": "mountains",
    "manali": "mountains",
    "shimla": "mountains",
    "mussoorie": "mountains",
    "tirthan": "mountains",
    "jaipur": "heritage",
    "agra": "heritage",
    "varanasi": "heritage",
    "udaipur": "heritage",
    "jodhpur": "heritage",
    "corbett": "nature",
    "ranthambore": "nature",
    "kaziranga": "nature",
}


def constraint_validator_node(state: TripState) -> dict:
    constraints = dict(state.get("extracted_constraints") or {})
    blocking: list[dict] = []
    warnings: list[dict] = []
    missing_fields: list[str] = []

    # ── Normalize (defensive — chat_parser should have done this already) ──
    for field in ("origin", "destination"):
        if constraints.get(field):
            constraints[field] = str(constraints[field]).strip().title()

    for field in ("hotel_tier", "risk_tolerance", "destination_type"):
        if constraints.get(field):
            constraints[field] = str(constraints[field]).strip().lower()

    for field in ("transport_preference", "must_include"):
        if isinstance(constraints.get(field), list):
            constraints[field] = [str(x).strip().lower() for x in constraints[field] if x]

    # ── Required field checks (Decision 20) ──
    if not constraints.get("origin"):
        missing_fields.append("origin")
        blocking.append({
            "type": "missing_required_field",
            "field": "origin",
            "description": "Origin city is required to plan a trip.",
        })

    if not constraints.get("budget_per_person") and not constraints.get("trip_duration"):
        missing_fields.extend(["budget_per_person", "trip_duration"])
        blocking.append({
            "type": "missing_required_field",
            "field": "budget_per_person / trip_duration",
            "description": "At least one of budget_per_person or trip_duration is required.",
        })

    has_preference = any([
        constraints.get("destination"),
        constraints.get("destination_type"),
        constraints.get("must_include"),
    ])
    if not has_preference:
        missing_fields.append("destination / destination_type / must_include")
        blocking.append({
            "type": "missing_required_field",
            "field": "destination",
            "description": "At least one preference (destination, destination_type, or must_include) is required.",
        })

    # ── Invalid value checks ──
    budget = constraints.get("budget_per_person")
    if budget is not None:
        try:
            if int(budget) <= 0:
                blocking.append({
                    "type": "invalid_value",
                    "field": "budget_per_person",
                    "description": f"budget_per_person must be positive, got {budget}.",
                })
        except (TypeError, ValueError):
            pass

    group_size = constraints.get("group_size")
    if group_size is not None:
        try:
            if int(group_size) <= 0:
                blocking.append({
                    "type": "invalid_value",
                    "field": "group_size",
                    "description": f"group_size must be positive, got {group_size}.",
                })
        except (TypeError, ValueError):
            pass

    # ── Destination vs destination_type mismatch (Decision 25) ──
    destination = constraints.get("destination", "")
    dest_type = constraints.get("destination_type", "")
    if destination and dest_type:
        known_type = _DEST_TYPE_MAP.get(destination.lower())
        if known_type and known_type != dest_type.lower():
            blocking.append({
                "type": "destination_mismatch",
                "field": "destination_type",
                "description": (
                    f"{destination} is a {known_type} destination, "
                    f"not a {dest_type} destination."
                ),
            })

    conflict_report = {
        "has_conflicts": len(blocking) > 0 or len(warnings) > 0,
        "blocking_conflicts": blocking,
        "warnings": warnings,
    }
    is_ready_to_plan = len(blocking) == 0

    return {
        "extracted_constraints": constraints,
        "conflict_report": conflict_report,
        "is_ready_to_plan": is_ready_to_plan,
        "missing_fields": missing_fields,
    }
