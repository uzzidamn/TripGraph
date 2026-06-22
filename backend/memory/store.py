"""
In-process user memory store. Keyed by user_id.
Swap this module's internals for a DB-backed store without changing the public API.
"""
from threading import Lock

_STORE: dict[str, dict] = {}
_LOCK: Lock = Lock()


def get_user_memory(user_id: str | None) -> dict:
    """Return memory for the given user; empty dict if user_id is None or not found."""
    if not user_id:
        return {}
    with _LOCK:
        return dict(_STORE.get(user_id, {}))


def update_user_memory(user_id: str | None, updates: dict) -> None:
    """Merge updates into existing user memory.

    Rules:
    - Never overwrites existing fields with None, [], or {}
    - past_trips is set as a whole list (caller is responsible for append logic)
    - All other fields are merged key-by-key
    """
    if not user_id:
        return
    with _LOCK:
        existing = _STORE.setdefault(user_id, {})
        for key, val in updates.items():
            if val is None or val == [] or val == {}:
                continue
            existing[key] = val


def clear_user_memory(user_id: str | None) -> None:
    """Remove all memory for a user. Used in tests."""
    if not user_id:
        return
    with _LOCK:
        _STORE.pop(user_id, None)
