"""
Simple JSON file-based user memory store.

Files are written to /tmp/tripgraph_memory_{user_id}.json.
Falls back to empty dict on any error — planning must never be blocked by memory.
"""
import json
import os
from pathlib import Path

_MEMORY_DIR = Path(os.getenv("MEMORY_DIR", "/tmp"))

_DEFAULT_MEMORY = {
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


def _path(user_id: str) -> Path:
    safe_id = "".join(c for c in user_id if c.isalnum() or c in "-_")
    return _MEMORY_DIR / f"tripgraph_memory_{safe_id}.json"


def get_user_memory(user_id: str) -> dict:
    """Load memory for user_id. Returns empty default on any error."""
    if not user_id:
        return dict(_DEFAULT_MEMORY)
    try:
        p = _path(user_id)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            merged = dict(_DEFAULT_MEMORY)
            merged.update(data)
            return merged
        return dict(_DEFAULT_MEMORY) | {"user_id": user_id}
    except Exception as e:
        print(f"  ⚠️  Memory store read failed for {user_id}: {e}")
        return dict(_DEFAULT_MEMORY)


def update_user_memory(user_id: str, updates: dict) -> None:
    """Atomically merge updates into the user's memory file."""
    if not user_id or not updates:
        return
    try:
        current = get_user_memory(user_id)
        for key, value in updates.items():
            if value is None or value == [] or value == {}:
                continue  # never overwrite with empty
            if key == "past_trips" and isinstance(value, list):
                existing = current.get("past_trips", [])
                current["past_trips"] = existing + [v for v in value if v not in existing]
            else:
                current[key] = value
        current["user_id"] = user_id
        p = _path(user_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  ⚠️  Memory store write failed for {user_id}: {e}")
