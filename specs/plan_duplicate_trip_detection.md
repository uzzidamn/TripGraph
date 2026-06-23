# Duplicate Trip Detection — Implementation Plan

Source: `spec_duplicate_trip_detection.md` (Version 2.1)
Depends on: `plan_user_auth_memory.md` (auth + SQL memory already implemented)

---

## Current State Audit

Before writing any code, here is the exact state of each file that will be touched:

| File | Relevant current state |
|------|----------------------|
| `guardrail.py` | `_find_similar_past_trip` exists but does text-keyword scan only; `guardrail_node` has a bug — status defaults to `"completed"` (line 228), so old entries with no `status` field are silently skipped |
| `workflow.py` | `run_workflow_from_constraints(constraints, user_id=None)` already accepts `user_id` and loads memory; no `duplicate_action` param; no `_duplicate_guardrail` helper; no `record_new_trip` call |
| `memory/sql_store.py` | Has `get_user_memory`, `update_user_memory`; missing `find_active_duplicate_trip`, `mark_trip_completed`, `record_new_trip` |
| `memory/store.py` | Thin router over `sql_store`; exposes only `get_user_memory`, `update_user_memory` |
| `models/requests.py` | `GenerateItineraryRequest` has no `duplicate_action` field |
| `api/itinerary_routes.py` | Calls `run_workflow_from_constraints(constraints, user_id=user_id)` — no `duplicate_action` passed |

---

## Implementation Order

Each step only imports from steps before it.

1. `backend/memory/sql_store.py` — add `find_duplicate_trip`, `record_new_trip`
2. `backend/memory/store.py` — expose the two new functions through the public API
3. `backend/agents/nodes/guardrail.py` — upgrade `_find_similar_past_trip` + fix bug in `guardrail_node`
4. `backend/agents/workflow.py` — add `_duplicate_guardrail`, update `run_workflow_from_constraints`
5. `backend/models/requests.py` — add `duplicate_action` to `GenerateItineraryRequest`
6. `backend/api/itinerary_routes.py` — pass `duplicate_action` from request to workflow

---

## Step 1 — `backend/memory/sql_store.py`

Add two functions after `update_user_memory`. These are the only functions that read/mutate `past_trips` at the SQL level.

```python
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

    Called after every successful planning run. Strips internal keys
    (prefixed with '_') before saving the constraints snapshot.
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
```

Note on `record_new_trip`: any `_`-prefixed keys in constraints are stripped before saving the snapshot, keeping history clean of internal workflow keys.

---

## Step 2 — `backend/memory/store.py`

Add two thin wrappers that call `_coerce_id` then delegate to `sql_store`. Append after `update_user_memory`.

```python
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
```

---

## Step 3 — `backend/agents/nodes/guardrail.py`

### 3a. Replace `_find_similar_past_trip`

Replace the entire existing function with the upgraded version. Signature gains two optional keyword arguments.

```python
def _find_similar_past_trip(
    messages: list[str],
    past_trips: list[dict],
    origin: str | None = None,
    destination: str | None = None,
) -> dict | None:
    """Match a past trip (planned or completed) with the same origin+destination.

    Uses exact fingerprint match when origin+destination are available (generate-itinerary path).
    Falls back to destination-keyword scan of raw messages (parse-chat path).
    Cancelled trips are always skipped.
    """
    if not past_trips:
        return None

    # Skip only cancelled trips — both planned and completed trips trigger the check
    checkable = [
        t for t in past_trips
        if t.get("status", "planned") != "cancelled"
    ]
    if not checkable:
        return None

    if origin and destination:
        o, d = origin.strip().lower(), destination.strip().lower()
        for trip in checkable:
            if (trip.get("origin", "").strip().lower() == o and
                    trip.get("destination", "").strip().lower() == d):
                return trip
        return None  # structured path: only exact match qualifies

    # Text-keyword fallback for parse-chat path
    text = " ".join(messages).lower()
    for trip in checkable:
        dest = (trip.get("destination") or "").lower()
        if dest and dest in text:
            return trip
    return None
```

### 3b. Update `guardrail_node`

Two changes inside `guardrail_node`:
1. Read `extracted_constraints` from state and pass structured fields to `_find_similar_past_trip`
2. Replace the old status-branched response block with the unified "confirm" response (only `planned` trips reach here now — filtering moved into `_find_similar_past_trip`)

Replace the section from `# Similar past-trip check` to the end of the function:

```python
    # Similar past-trip check — structured fingerprint when available, text fallback otherwise
    constraints = state.get("extracted_constraints") or {}
    similar = _find_similar_past_trip(
        messages, past_trips,
        origin=constraints.get("origin"),
        destination=constraints.get("destination"),
    )
    if similar:
        dest = similar.get("destination", "that destination")
        origin_str = similar.get("origin", "")
        planned_at = similar.get("planned_at", "")
        date_str = ""
        if planned_at:
            try:
                from datetime import datetime as _dt
                dt = _dt.fromisoformat(planned_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%d %b %Y")
            except Exception:
                date_str = planned_at[:10]

        status_str = similar.get("status", "planned")
        verb = "had" if status_str == "completed" else "have"
        response = (
            f"You already {verb} a trip to {dest}"
            + (f" from {origin_str}" if origin_str else "")
            + (f" ({date_str})" if date_str else "")
            + ". Would you like to proceed with the same?"
        )
        print(f"  ⏸  Guardrail: {status_str} trip to {dest} found — confirming with user")
        return {"guardrail_result": {
            "action": "confirm",
            "reason": "similar_trip_found",
            "response": response,
            "matched_trip": similar,
        }}

    # All clear
    print("  ✅ Guardrail: valid trip message — proceeding")
    return {"guardrail_result": {
        "action": "proceed",
        "reason": "no_prior_match",
        "response": None,
        "matched_trip": None,
    }}
```

**Why this removes the old status branching:** The `_find_similar_past_trip` upgrade now checks both planned and completed trips. Only cancelled trips are skipped. The response message is unified — the same "proceed?" question regardless of whether the matched trip is planned or completed.

---

## Step 4 — `backend/agents/workflow.py`

### 4a. Add `_duplicate_guardrail` helper

Add this function immediately before `run_workflow_from_constraints`. It is a pure Python function — no LLM, no graph node.

```python
def _duplicate_guardrail(
    constraints: dict,
    user_id,
    duplicate_action: str | None,
) -> dict | None:
    """Check for a duplicate past trip before any expensive agent work.

    Returns a partial state dict to short-circuit the workflow, or None to proceed.
    Anonymous users (no user_id) are always passed through.
    Any exception skips the check — planning is never blocked.
    """
    if not user_id:
        return None

    origin = constraints.get("origin", "")
    destination = constraints.get("destination") or constraints.get("destination_type", "")
    if not origin or not destination:
        return None  # can't fingerprint without both fields

    try:
        from backend.memory.store import find_duplicate_trip

        if duplicate_action == "cancel":
            return {"guardrail_result": {
                "action": "cancel",
                "reason": "user_cancelled",
                "response": "Planning cancelled. Let me know if you'd like to plan a different trip.",
                "matched_trip": None,
            }}

        if duplicate_action == "proceed":
            print(f"  ✅ Duplicate guard: user chose to proceed — planning {origin} → {destination}")
            return None  # continue with fresh planning; old trip entry unchanged

        matched = find_duplicate_trip(user_id, origin, destination)

        if matched is None:
            return None  # no duplicate — proceed normally

        # Duplicate found and no action yet — ask the user
        planned_at = matched.get("planned_at", "")
        date_str = ""
        if planned_at:
            try:
                from datetime import datetime as _dt
                dt = _dt.fromisoformat(planned_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%d %b %Y")
            except Exception:
                date_str = planned_at[:10]

        status_str = matched.get("status", "planned")
        verb = "had" if status_str == "completed" else "have"
        response = (
            f"You already {verb} a trip to {destination} from {origin}"
            + (f" ({date_str})" if date_str else "")
            + ". Would you like to proceed with the same?"
        )
        print(f"  ⏸  Duplicate guard: {status_str} trip to {destination} — confirming with user")
        return {"guardrail_result": {
            "action": "confirm",
            "reason": "similar_trip_found",
            "response": response,
            "matched_trip": matched,
        }}

    except Exception as e:
        print(f"  ⚠️  Duplicate guardrail failed ({e}) — skipping check")
        return None
```

### 4b. Update `run_workflow_from_constraints`

Three changes:
1. Add `duplicate_action` parameter to signature
2. Call `_duplicate_guardrail` before `route_retriever_node`  
3. Call `record_new_trip` after successful planning

**Updated signature:**
```python
def run_workflow_from_constraints(
    constraints: dict,
    user_id: int | str | None = None,
    duplicate_action: str | None = None,
) -> TripState:
```

**After the memory-load block, before the node imports, add:**
```python
    # Duplicate trip gate — stops before any expensive work
    early_exit = _duplicate_guardrail(constraints, user_id, duplicate_action)
    if early_exit is not None:
        state.update(early_exit)
        return state
```

**After `_fold_review_into_explanation(state)` and before `print("✅ Workflow complete")`, add:**
```python
    # Record the new trip in memory if planning succeeded
    if user_id and state.get("selected_itinerary"):
        from backend.memory.store import record_new_trip
        trip_id = record_new_trip(user_id, constraints)
        print(f"  💾 Trip recorded: {trip_id}")
```

**Full updated function signature + body (showing the three insertion points):**

```python
def run_workflow_from_constraints(
    constraints: dict,
    user_id: int | str | None = None,
    duplicate_action: str | None = None,
) -> TripState:
    """...(existing docstring unchanged)..."""
    print("\n🚀 Starting TripGraph workflow (from constraints)")
    state = initialize_state([])
    state["extracted_constraints"] = constraints
    state["is_ready_to_plan"] = True

    if user_id:
        state["user_id"] = user_id
        from backend.memory.store import get_user_memory
        state["user_profile"] = get_user_memory(user_id)
        print(f"  🧠 Memory loaded for user_id={user_id}")

    # ── NEW: duplicate trip gate ──────────────────────────────────────────────
    early_exit = _duplicate_guardrail(constraints, user_id, duplicate_action)
    if early_exit is not None:
        state.update(early_exit)
        return state
    # ─────────────────────────────────────────────────────────────────────────

    from backend.agents.nodes.weather_agent import weather_agent_node
    # ... (all existing node imports unchanged) ...

    # 0) Gate: check origin/destination are in the catalog
    state.update(route_retriever_node(state))
    if state.get("unsupported_route"):
        print("  ⛔ Unsupported route — returning early without planning")
        return state

    # ... (all existing agent calls unchanged) ...

    _fold_review_into_explanation(state)

    # ── NEW: record successful plan in memory ─────────────────────────────────
    if user_id and state.get("selected_itinerary"):
        from backend.memory.store import record_new_trip
        trip_id = record_new_trip(user_id, constraints)
        print(f"  💾 Trip recorded: {trip_id}")
    # ─────────────────────────────────────────────────────────────────────────

    print("✅ Workflow complete\n")
    return state
```

---

## Step 5 — `backend/models/requests.py`

Add one field to `GenerateItineraryRequest`. Import `Literal` at the top.

**Add to imports:**
```python
from typing import Any, Dict, List, Literal, Optional
```

**Add field to `GenerateItineraryRequest` after `refinement_answers`:**
```python
    duplicate_action: Optional[Literal["proceed", "cancel"]] = Field(
        None,
        description=(
            "Response to a duplicate trip warning. "
            "'proceed' continues planning the same route. "
            "'cancel' aborts planning."
        ),
    )
```

---

## Step 6 — `backend/api/itinerary_routes.py`

One line change — pass `duplicate_action` from request to workflow:

```python
        result = run_workflow_from_constraints(
            constraints,
            user_id=user_id,
            duplicate_action=request.duplicate_action,
        )
```

---

## Response Shapes

### Duplicate detected (no `duplicate_action`)
```json
{
  "guardrail_result": {
    "action": "confirm",
    "reason": "similar_trip_found",
    "response": "You already have a trip to Rishikesh from Gurugram (23 Jun 2026). Would you like to proceed with the same?",
    "matched_trip": {
      "trip_id": "abc-123",
      "origin": "Gurugram",
      "destination": "Rishikesh",
      "planned_at": "2026-06-23T10:00:00+00:00",
      "trip_duration": "2D1N",
      "status": "planned"
    }
  },
  "recommended_itinerary": null,
  "timeline": null
}
```

### User cancels (`duplicate_action: "cancel"`)
```json
{
  "guardrail_result": {
    "action": "cancel",
    "reason": "user_cancelled",
    "response": "Planning cancelled. Let me know if you'd like to plan a different trip.",
    "matched_trip": null
  },
  "recommended_itinerary": null
}
```

### User proceeds (`duplicate_action: "proceed"`)
`guardrail_result` is `{}` (from `initialize_state`), full itinerary fields populated normally.

---

## File Layout (changes only)

```
backend/
  memory/
    sql_store.py    — ADD: find_duplicate_trip, record_new_trip
    store.py        — ADD: 2 thin wrappers with _coerce_id
  agents/
    nodes/
      guardrail.py  — REPLACE: _find_similar_past_trip (structured + fallback, checks planned+completed)
                    — MODIFY: guardrail_node (pass structured fields, unified "proceed?" message)
    workflow.py     — ADD: _duplicate_guardrail() (proceed/cancel only)
                    — MODIFY: run_workflow_from_constraints (duplicate_action param,
                               early-exit call, record_new_trip call)
  models/
    requests.py     — ADD: duplicate_action: Literal["proceed","cancel"] to GenerateItineraryRequest
  api/
    itinerary_routes.py  — MODIFY: pass duplicate_action to workflow
```

---

## Acceptance Criteria Coverage

| AC | Statement | Implementation |
|----|-----------|----------------|
| 1 | Duplicate halts before any agent runs | `_duplicate_guardrail` returns early before `route_retriever_node` is ever called |
| 2 | Warning message contains trip details | `_duplicate_guardrail` formats response with `destination`, `origin`, `date_str`; uses "have" vs "had" based on status |
| 3 | `"proceed"` continues planning unchanged | `_duplicate_guardrail`: `if duplicate_action == "proceed": return None` — workflow continues, old trip entry untouched |
| 4 | `"cancel"` returns immediately | `_duplicate_guardrail`: checked before loading matched trip, returns cancel state immediately |
| 5 | Completed trips are also flagged | `_find_similar_past_trip`: filters `checkable = [t for t in past_trips if status != "cancelled"]` — includes completed |
| 6 | Anonymous users bypass check | `_duplicate_guardrail`: `if not user_id: return None` |
| 7 | Memory failure is non-fatal | Both `_duplicate_guardrail` and `find_duplicate_trip` wrap all logic in `try/except`, log warning, return `None` |
| 8 | Successful plan writes new past_trips entry | `run_workflow_from_constraints`: `record_new_trip(user_id, constraints)` called when `state.get("selected_itinerary")` is truthy |
| 9 | parse-chat path upgraded | `guardrail_node`: reads `state.get("extracted_constraints")` and passes `origin`/`destination` to upgraded `_find_similar_past_trip` |
