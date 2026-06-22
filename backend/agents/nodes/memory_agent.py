"""
Agent 2: load user memory, extract visited destinations, merge into constraints.
Pure Python — no LLM call. Runs after Chat Parser, before Constraint Validator.
"""
from backend.agents.state import TripState
from backend.memory.store import get_user_memory

_OVERRIDE_KEYWORDS = {"again", "same place", "revisit", "back to", "once more"}


def memory_agent_node(state: TripState) -> dict:
    user_id = state.get("user_id")
    memory = get_user_memory(user_id)

    # 1. Extract visited destinations from past_trips
    visited: list[str] = [
        t["destination"]
        for t in memory.get("past_trips", [])
        if t.get("destination")
    ]

    # 2. Build user_profile (everything except past_trips)
    user_profile: dict = {k: v for k, v in memory.items() if k != "past_trips"}

    # 3. Detect dedup override from chat text
    chat_text = " ".join(state.get("raw_chat") or []).lower()
    user_confirmed_repeat = any(kw in chat_text for kw in _OVERRIDE_KEYWORDS)

    memory_context: dict = {}
    if user_confirmed_repeat:
        memory_context["dedup_override"] = True

    # 4. Merge memory into extracted_constraints (absent fields only)
    constraints = dict(state.get("extracted_constraints") or {})

    # Destination: inject from memory only if destination, destination_type, and must_include
    # are all absent — explicit preferences always take precedence over memory
    has_explicit_preference = (
        constraints.get("destination")
        or constraints.get("destination_type")
        or constraints.get("must_include")
    )
    if not has_explicit_preference:
        preferred = memory.get("preferred_destinations") or []
        if preferred:
            candidate = preferred[0]
            if candidate not in visited or user_confirmed_repeat:
                constraints["destination"] = candidate
                memory_context["source"] = "user_memory"
            else:
                memory_context["skip_reason"] = (
                    f"Destination {candidate} already visited."
                )

    # Hotel tier: inject from memory if absent
    if not constraints.get("hotel_tier") and memory.get("preferred_hotel_tier"):
        constraints["hotel_tier"] = memory["preferred_hotel_tier"]

    # Budget: inject from memory range if absent
    budget_range = memory.get("budget_range") or {}
    if not constraints.get("budget_per_person") and budget_range.get("min"):
        constraints["budget_per_person"] = budget_range["min"]

    # Avoidances: merge into special_requirements
    memory_avoidances = [f"avoid_{a}" for a in (memory.get("avoidances") or [])]
    if memory_avoidances:
        existing = list(constraints.get("special_requirements") or [])
        constraints["special_requirements"] = list(set(existing + memory_avoidances))

    return {
        "extracted_constraints": constraints,
        "user_profile": user_profile,
        "memory_context": memory_context,
        "visited_destinations": visited,
    }
