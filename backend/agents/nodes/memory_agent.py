"""
Agent 2 — Memory Agent

Loads user travel history, extracts visited destinations, and merges
memory-inferred preferences into the extracted constraints.

Priority order: Explicit User Input > Current Chat > User Memory > Dedup Filter
"""
from backend.agents.state import TripState
from backend.memory.store import get_user_memory

_REPEAT_SIGNALS = {"again", "same place", "revisit", "back to", "once more"}


def _has_repeat_signal(messages: list[str]) -> bool:
    text = " ".join(messages).lower()
    return any(sig in text for sig in _REPEAT_SIGNALS)


def memory_agent_node(state: TripState) -> dict:
    user_id = state.get("user_id")
    messages = state.get("raw_chat") or []

    # Load memory — gracefully falls back to {} if unavailable
    profile = get_user_memory(user_id) if user_id else {}

    past_trips = profile.get("past_trips", [])
    visited = [t["destination"] for t in past_trips if t.get("destination")]

    constraints = dict(state.get("extracted_constraints") or {})
    memory_context: dict = {
        "visited_destinations": visited,
        "profile_applied": [],
    }

    dedup_override = _has_repeat_signal(messages)

    # If user explicitly names a visited destination with repeat signal, allow it
    explicit_dest = constraints.get("destination")
    if explicit_dest and explicit_dest in visited and dedup_override:
        memory_context["dedup_override"] = True
        print(f"  🔁 Memory agent: repeat override for '{explicit_dest}'")
    elif explicit_dest and explicit_dest in visited and not dedup_override:
        # Don't block explicit requests — user knows what they want
        memory_context["dedup_override"] = False

    # Apply memory-inferred values only when the field is absent from current chat
    if not constraints.get("origin") and profile.get("preferred_origins"):
        constraints["origin"] = profile["preferred_origins"][0]
        memory_context["profile_applied"].append("origin")

    if not constraints.get("hotel_tier") and profile.get("preferred_hotel_tier"):
        constraints["hotel_tier"] = profile["preferred_hotel_tier"]
        memory_context["profile_applied"].append("hotel_tier")

    if not constraints.get("destination") and not constraints.get("destination_type"):
        preferred_dest = (profile.get("preferred_destinations") or [None])[0]
        if preferred_dest and preferred_dest not in visited:
            constraints["destination"] = preferred_dest
            memory_context["profile_applied"].append("destination")
        elif preferred_dest and preferred_dest in visited:
            memory_context["skip_reason"] = f"Destination {preferred_dest} already visited."

    print(f"  ✅ Memory agent: visited={len(visited)}, applied={memory_context['profile_applied']}, "
          f"dedup_override={dedup_override}")

    return {
        "user_profile": profile,
        "memory_context": memory_context,
        "visited_destinations": visited,
        "extracted_constraints": constraints,
    }
