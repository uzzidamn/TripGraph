from datetime import datetime, timezone

from backend.db.models import UserMemory
from backend.db.session import SessionLocal

_DEFAULT: dict = {
    "user_id": None,
    "preferred_origins": [],
    "preferred_destinations": [],
    "budget_range": {"min": 0, "max": 0},
    "preferred_hotel_tier": None,
    "activity_preferences": [],
    "avoidances": [],
    "travel_style": None,
    "past_trips": [],
}


def _row_to_dict(row: UserMemory, user_id: int) -> dict:
    return {
        "user_id": user_id,
        "preferred_origins": row.preferred_origins,
        "preferred_destinations": row.preferred_destinations,
        "budget_range": {"min": row.budget_min or 0, "max": row.budget_max or 0},
        "preferred_hotel_tier": row.preferred_hotel_tier,
        "activity_preferences": row.activity_preferences,
        "avoidances": row.avoidances,
        "travel_style": row.travel_style,
        "past_trips": row.past_trips,
    }


def get_user_memory(user_id: int) -> dict:
    """Load memory for user_id from DB. Returns empty default on any error."""
    try:
        with SessionLocal() as db:
            row = db.get(UserMemory, user_id)
            if row is None:
                return dict(_DEFAULT) | {"user_id": user_id}
            return _row_to_dict(row, user_id)
    except Exception as e:
        print(f"  ⚠️  SQL memory read failed for {user_id}: {e}")
        return dict(_DEFAULT)


def update_user_memory(user_id: int, updates: dict) -> None:
    """Merge updates into the user's DB memory row. Preserves existing data."""
    if not user_id or not updates:
        return
    try:
        with SessionLocal() as db:
            row = db.get(UserMemory, user_id)
            if row is None:
                row = UserMemory(user_id=user_id)
                db.add(row)

            for key, value in updates.items():
                if value is None or value == [] or value == {}:
                    continue  # never overwrite with empty

                if key == "preferred_origins":
                    row.preferred_origins = value
                elif key == "preferred_destinations":
                    row.preferred_destinations = value
                elif key == "budget_range" and isinstance(value, dict):
                    row.budget_min = value.get("min") or row.budget_min
                    row.budget_max = value.get("max") or row.budget_max
                elif key == "preferred_hotel_tier":
                    row.preferred_hotel_tier = value
                elif key == "activity_preferences":
                    row.activity_preferences = value
                elif key == "avoidances":
                    row.avoidances = value
                elif key == "travel_style":
                    row.travel_style = value
                elif key == "past_trips" and isinstance(value, list):
                    existing = row.past_trips or []
                    row.past_trips = existing + [v for v in value if v not in existing]

            row.updated_at = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        print(f"  ⚠️  SQL memory write failed for {user_id}: {e}")


import uuid as _uuid


def find_duplicate_trip(user_id: int, origin: str, destination: str) -> dict | None:
    """Return the first planned or completed past trip matching origin+destination, or None.

    Cancelled trips are skipped. Both planned and completed trips trigger the check.
    Falls back to None on any DB error so planning is never blocked.
    """
    try:
        with SessionLocal() as db:
            row = db.get(UserMemory, user_id)
            if row is None:
                return None
            o = origin.strip().lower()
            d = destination.strip().lower()
            for trip in (row.past_trips or []):
                if trip.get("status", "planned") == "cancelled":
                    continue
                if (trip.get("origin", "").strip().lower() == o and
                        trip.get("destination", "").strip().lower() == d):
                    return trip
            return None
    except Exception as e:
        print(f"  ⚠️  find_duplicate_trip failed for {user_id}: {e}")
        return None


def record_new_trip(user_id: int, constraints: dict) -> str:
    """Append a new past_trips entry with status='planned'. Returns the new trip_id.

    Strips internal '_'-prefixed keys before saving the constraints snapshot.
    """
    trip_id = str(_uuid.uuid4())
    snapshot = {k: v for k, v in constraints.items() if not k.startswith("_")}
    entry = {
        "trip_id": trip_id,
        "origin": constraints.get("origin", ""),
        "destination": (
            constraints.get("destination") or constraints.get("destination_type", "")
        ),
        "trip_duration": constraints.get("trip_duration", ""),
        "planned_at": datetime.now(timezone.utc).isoformat(),
        "status": "planned",
        "constraints_snapshot": snapshot,
    }
    try:
        with SessionLocal() as db:
            row = db.get(UserMemory, user_id)
            if row is None:
                row = UserMemory(user_id=user_id)
                db.add(row)
            row.past_trips = (row.past_trips or []) + [entry]
            row.updated_at = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        print(f"  ⚠️  record_new_trip failed for {user_id}: {e}")
    return trip_id
