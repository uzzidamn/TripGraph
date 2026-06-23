"""
Agent 2: Constraint Validator
Validates extracted constraints for completeness and logical consistency.

Phase A (Python): Check required fields and obvious hard conflicts.
Phase B (LLM):    Detect subtle logical conflicts and suggest assumptions.
"""
from backend.agents.state import TripState


def _check_required_fields(constraints: dict) -> list[str]:
    """Return list of required fields that are missing (null or absent).

    Per spec F.6 — five required fields checked independently:
      origin, destination/destination_type/must_include, trip_duration,
      budget_per_person, group_size
    """
    missing = []
    if not constraints.get("origin"):
        missing.append("origin")
    has_destination = (
        constraints.get("destination")
        or constraints.get("destination_type")
        or constraints.get("must_include")
    )
    if not has_destination:
        missing.append("destination")
    if not constraints.get("trip_duration"):
        missing.append("trip_duration")
    if not constraints.get("budget_per_person"):
        missing.append("budget_per_person")
    if not constraints.get("group_size"):
        missing.append("group_size")
    return missing


def _check_hard_conflicts(constraints: dict) -> list[str]:
    """Detect obvious hard conflicts using Python rules — no LLM needed."""
    conflicts = []
    budget = constraints.get("budget_per_person")
    tier = constraints.get("hotel_tier")

    # Luxury tier with very low budget
    if budget and tier == "comfort" and budget < 5000:
        conflicts.append(
            f"Hotel tier 'comfort' typically costs ₹3,500–5,500/night but budget is only ₹{budget}/person"
        )
    if budget and tier == "expedition" and budget < 3000:
        conflicts.append(
            f"Expedition-tier camps cost ₹2,000–4,000/night but budget is only ₹{budget}/person"
        )

    # Night driving conflict
    avoid_night = constraints.get("avoid_night_driving", False)
    transport_prefs = constraints.get("transport_preference", [])
    if avoid_night and "self_drive" in transport_prefs:
        conflicts.append(
            "avoid_night_driving=true conflicts with self_drive preference (self-drive allows night driving)"
        )

    return conflicts


def constraint_validator_node(state: TripState) -> dict:
    """Validate constraints and decide if planning can proceed.

    Returns is_ready_to_plan=False immediately if required fields are missing.
    Otherwise calls LLM to detect subtle conflicts and fill assumptions.
    """
    constraints = state["extracted_constraints"]

    # Phase A: Python checks — fast, no LLM
    missing = _check_required_fields(constraints)
    hard_conflicts = _check_hard_conflicts(constraints)

    if missing:
        print(f"  ⚠️  Constraint validator: missing required fields: {missing}")
        return {
            "is_ready_to_plan": False,
            "missing_fields": missing,
            "conflict_report": {
                "has_conflicts": bool(hard_conflicts),
                "conflicts": hard_conflicts,
            },
            "assumptions": {},
        }

    # Phase B removed — Python Phase A covers all hard blockers.
    # LLM conflict-scan added ~2s per request with no decision impact.
    print(f"  ✅ Constraint validator: ready_to_plan=True, conflicts={len(hard_conflicts)}")
    return {
        "is_ready_to_plan": True,
        "conflict_report": {
            "has_conflicts": bool(hard_conflicts),
            "conflicts": hard_conflicts,
        },
        "assumptions": {},
        "missing_fields": [],
    }
