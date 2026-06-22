"""
Agent 8 — Memory Updater

Appends the completed trip to the user's past_trips list.
Runs only on successful workflow completion (selected_itinerary present).
"""
from backend.agents.state import TripState
from backend.memory.store import update_user_memory


def memory_updater_node(state: TripState) -> dict:
    user_id = state.get("user_id")
    itinerary = state.get("selected_itinerary")

    if not user_id:
        print("  ℹ️  Memory updater: no user_id — skipping")
        return {"memory_updates": {}}

    if not itinerary:
        print("  ℹ️  Memory updater: no selected_itinerary — skipping")
        return {"memory_updates": {}}

    cost_breakdown = state.get("cost_breakdown") or {}
    new_trip = {
        "destination": itinerary.get("destination") or (itinerary.get("route") or {}).get("destination"),
        "date": itinerary.get("start_date"),
        "duration": itinerary.get("duration"),
        "hotel_tier": itinerary.get("hotel_tier") or (itinerary.get("hotel") or {}).get("tier"),
        "activities": [a.get("name") for a in (itinerary.get("activities") or []) if a.get("name")],
        "budget_spent": cost_breakdown.get("total"),
        "status": "completed",
    }
    # Filter out None values
    new_trip = {k: v for k, v in new_trip.items() if v is not None}

    updates = {"past_trips": [new_trip]}
    update_user_memory(user_id, updates)

    print(f"  ✅ Memory updater: saved trip to {new_trip.get('destination')} for user {user_id}")
    return {"memory_updates": updates}
