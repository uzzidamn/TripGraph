"""
User memory store — SQL-backed (SQLite by default, PostgreSQL-ready).

Public API is identical to the old JSON-file store so all callers are unchanged:
  get_user_memory(user_id)          -> dict
  update_user_memory(user_id, updates) -> None
"""


def _coerce_id(user_id) -> int | None:
    """Coerce str/int user_id to int for DB lookup. Returns None on failure."""
    if user_id is None:
        return None
    try:
        return int(user_id)
    except (ValueError, TypeError):
        return None


def get_user_memory(user_id) -> dict:
    from backend.memory.sql_store import _DEFAULT, get_user_memory as _get
    uid = _coerce_id(user_id)
    if uid is None:
        return dict(_DEFAULT)
    return _get(uid)


def update_user_memory(user_id, updates: dict) -> None:
    from backend.memory.sql_store import update_user_memory as _update
    uid = _coerce_id(user_id)
    if uid is None:
        return
    _update(uid, updates)


def find_duplicate_trip(user_id, origin: str, destination: str) -> dict | None:
    from backend.memory.sql_store import find_duplicate_trip as _find
    uid = _coerce_id(user_id)
    if uid is None:
        return None
    return _find(uid, origin, destination)


def record_new_trip(user_id, constraints: dict) -> str | None:
    from backend.memory.sql_store import record_new_trip as _record
    uid = _coerce_id(user_id)
    if uid is None:
        return None
    return _record(uid, constraints)
