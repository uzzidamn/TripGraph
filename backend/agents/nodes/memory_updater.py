"""
Agent 8: persist the completed itinerary to user memory.
Runs in fan-out parallel with Explainer after Planner Orchestrator.
Only writes memory on successful (non-null) itinerary with a valid destination.
"""
from backend.agents.state import TripState
from backend.memory.store import get_user_memory, update_user_memory


def memory_updater_node(state: TripState) -> dict:
    user_id = state.get("user_id")
    selected = state.get("selected_itinerary") or {}
    cost = state.get("cost_breakdown") or {}

    # Only update on a successful plan with a user_id
    if not selected or not user_id:
        return {"memory_updates": {}}

    # Resolve destination from itinerary or nested route
    destination = selected.get("destination") or (selected.get("route") or {}).get("destination")
    if not destination:
        return {"memory_updates": {}}

    memory = get_user_memory(user_id)
    past_trips = list(memory.get("past_trips", []))

    new_entry: dict = {
        "destination": destination,
        "date": selected.get("start_date"),
        "duration": selected.get("duration"),
        "hotel_tier": (selected.get("hotel") or {}).get("tier"),
        "activities": [
            a.get("name")
            for a in (selected.get("activities") or [])
            if a.get("name")
        ],
        "budget_spent": cost.get("total"),
        "status": "planned",
    }
    # Strip None values so update_user_memory doesn't skip the whole entry
    new_entry = {k: v for k, v in new_entry.items() if v is not None}

    past_trips.append(new_entry)
    updates = {"past_trips": past_trips}
    update_user_memory(user_id, updates)

    return {"memory_updates": updates}
