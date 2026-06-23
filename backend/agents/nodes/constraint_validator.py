"""
Agent 2: Constraint Validator
Validates extracted constraints for completeness and logical consistency.

Phase A (Python): Check required fields and obvious hard conflicts.
Phase B (LLM):    Detect subtle logical conflicts and suggest assumptions.
"""
import json

from backend.agents.llm_client import get_llm
from backend.agents.nodes.chat_parser import _parse_llm_json
from backend.agents.prompts import CONSTRAINT_VALIDATOR_HUMAN, CONSTRAINT_VALIDATOR_SYSTEM
from backend.agents.state import TripState


def _check_required_fields(constraints: dict) -> list[str]:
    """Return list of required fields that are missing (null or absent)."""
    missing = []
    if not constraints.get("origin"):
        missing.append("origin")
    has_duration = constraints.get("budget_per_person") or constraints.get("trip_duration")
    if not has_duration:
        missing.append("budget_per_person_or_trip_duration")
    has_preference = (
        constraints.get("destination_type")
        or constraints.get("must_include")
        or constraints.get("destination")
    )
    if not has_preference:
        missing.append("destination_type_or_must_include")
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

    # Phase B: LLM checks — subtle conflicts and assumptions
    llm = get_llm()
    messages = [
        ("system", CONSTRAINT_VALIDATOR_SYSTEM),
        ("human", CONSTRAINT_VALIDATOR_HUMAN.format(constraints=json.dumps(constraints, indent=2))),
    ]

    llm_result: dict = {}
    try:
        response = llm.invoke(messages)
        llm_result = _parse_llm_json(response.content)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  Constraint validator JSON parse failed: {e}")
        llm_result = {"conflict_report": {}, "assumptions": {}}
    except Exception as e:
        print(f"  ❌ LLM call failed: {e}")
        raise

    # Merge Python-detected conflicts with LLM-detected conflicts
    llm_conflicts = llm_result.get("conflict_report", {}).get("conflicts", [])
    all_conflicts = hard_conflicts + llm_conflicts
    assumptions = llm_result.get("assumptions", {})

    print(f"  ✅ Constraint validator: ready_to_plan=True, "
          f"conflicts={len(all_conflicts)}, assumptions={len(assumptions)}")

    return {
        "is_ready_to_plan": True,
        "conflict_report": {
            "has_conflicts": bool(all_conflicts),
            "conflicts": all_conflicts,
        },
        "assumptions": assumptions,
        "missing_fields": [],
    }
