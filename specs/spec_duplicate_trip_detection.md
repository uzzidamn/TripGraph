# TripGraph AI — Duplicate Trip Detection

Version: 2.1 (simplified to proceed/cancel)
Depends on: `spec_user_auth_memory.md`

---

# 1. Overview

## Purpose

When a logged-in user submits a trip plan request for a destination they have already planned (or completed) before, the system shall **stop inside the guardrail** — before any retrieval, planning, weather, reviews, or LLM calls run — and ask:

> "You already have a trip to **{destination}** from **{origin}**.  
> Would you like to proceed with the same?"

The user picks one of two actions:
- **Proceed** — go ahead and plan the same route
- **Cancel** — abort; user will change their request

This is a guardrail check, not an API-layer check. It runs before any expensive agent work.

---

# 2. Current State (what already exists)

`backend/agents/nodes/guardrail.py` already has:
- `_find_similar_past_trip(messages, past_trips)` — keyword scan of destination in raw chat text
- `guardrail_result = {action: "confirm", matched_trip: {...}}` — the halting signal
- `_route_after_guardrail` in `workflow.py` routes to `END` on `action == "confirm"`

**Gaps to fix:**

| Gap | Problem |
|-----|---------|
| Matching is text-keyword only | `_find_similar_past_trip` scans raw chat strings — misses structured constraints path entirely |
| `run_workflow_from_constraints` skips guardrail | The generate-itinerary path (`/api/generate-itinerary`) never calls `guardrail_node` — duplicate check never fires there |
| No `duplicate_action` resolution | There is no way for the user to respond to `action: "confirm"` and resume planning |
| `past_trips` entries have no `origin` or `status` field | `_find_similar_past_trip` reads `.destination` and `.status` — the actual entries stored by `update_user_memory` have no guaranteed schema |

---

# 3. Architecture

## Two entry paths, one guardrail layer

```
Path A: POST /api/parse-chat
  run_workflow(chat_messages, user_id)
    │
    └─ guardrail_node ──► [action=confirm] ──► END  ← already works, needs upgrade
                     └──► [action=proceed] ──► chat_parser → memory_agent → ...

Path B: POST /api/generate-itinerary
  run_workflow_from_constraints(constraints, user_id, duplicate_action)
    │
    ├─ [NEW] duplicate_guardrail(constraints, user_id, duplicate_action)
    │         │
    │         ├── no user_id or no past_trips → skip, continue
    │         ├── no match → continue
    │         ├── match + no duplicate_action → return {guardrail_result: {action:"confirm",...}}
    │         ├── duplicate_action="proceed"  → continue (no state change to old trip)
    │         └── duplicate_action="cancel"   → return {guardrail_result: {action:"cancel"}}
    │
    ├─ route_retriever_node   ← first expensive node (only reached if guardrail passes)
    ├─ data_retriever_node
    ├─ ... all agents ...
    └─ review_agent_node      ← guardrail stops before this ever runs
```

---

# 4. Trip Fingerprint

Two trips are considered the same if **both** match:
- `origin.strip().lower()` == `past_trip.origin.strip().lower()`
- `destination.strip().lower()` == `past_trip.destination.strip().lower()`

Trips with `status == "planned"` **and** `status == "completed"` are both checked. Only `status == "cancelled"` trips are skipped.

For the **parse-chat path** (Path A), the guardrail fires before constraint extraction — origin and destination may not be in state yet. In this case the existing text-keyword check on destination alone is kept as a fallback.

For the **generate-itinerary path** (Path B), structured `constraints["origin"]` and `constraints["destination"]` are available — use the exact fingerprint.

---

# 5. `past_trips` Entry Schema

Entries written to memory must include these fields from this point forward.
Existing entries missing fields default to: `status="planned"`, `origin=""`.

```json
{
  "trip_id": "uuid4-string",
  "origin": "Gurugram",
  "destination": "Rishikesh",
  "trip_duration": "2D1N",
  "planned_at": "2026-06-23T10:00:00Z",
  "status": "planned",
  "constraints_snapshot": {
    "budget_per_person": 15000,
    "hotel_tier": "comfort",
    "must_include": ["rafting"]
  }
}
```

| Field                  | Type   | Notes                                               |
|------------------------|--------|-----------------------------------------------------|
| `trip_id`              | string | UUID v4, generated at planning time                 |
| `origin`               | string | From `extracted_constraints.origin`                 |
| `destination`          | string | From `extracted_constraints.destination`            |
| `trip_duration`        | string | Optional, from constraints                          |
| `planned_at`           | string | ISO-8601 UTC, set when itinerary is finalized       |
| `status`               | enum   | `"planned"` \| `"completed"` \| `"cancelled"`       |
| `constraints_snapshot` | object | Full constraints dict (for replan context injection)|

---

# 6. Code Changes

## 6.1 `backend/agents/nodes/guardrail.py`

### Upgrade `_find_similar_past_trip`

Current signature: `(messages: list[str], past_trips: list[dict]) -> dict | None`

Add a second matcher that uses structured fields when available:

```python
def _find_similar_past_trip(
    messages: list[str],
    past_trips: list[dict],
    origin: str | None = None,
    destination: str | None = None,
) -> dict | None:
```

Logic:
1. If `origin` and `destination` are provided → use exact fingerprint match (normalize both sides)
2. Otherwise → fall back to existing destination-keyword-in-text scan
3. Skip entries with `status == "cancelled"` only — planned and completed trips both trigger the check

### Update `guardrail_node` to pass structured fields

```python
def guardrail_node(state: TripState) -> dict:
    ...
    constraints = state.get("extracted_constraints") or {}
    origin = constraints.get("origin")
    destination = constraints.get("destination")

    similar = _find_similar_past_trip(
        messages, past_trips,
        origin=origin,
        destination=destination,
    )
```

The rest of the response shape stays identical — `action: "confirm"`, `matched_trip`, `response` message.

---

## 6.2 `backend/agents/workflow.py`

### Add `duplicate_guardrail` helper

A pure function (no LLM, no graph node) called at the top of `run_workflow_from_constraints`:

```python
def _duplicate_guardrail(
    constraints: dict,
    user_id: str | None,
    duplicate_action: str | None,
) -> dict | None:
    """
    Returns a partial TripState dict to short-circuit the workflow,
    or None if planning should proceed normally.
    """
```

Behaviour:
- If no `user_id` → return `None` (anonymous, skip)
- Load past_trips from memory store
- Call `_find_similar_past_trip([], past_trips, origin=..., destination=...)`
- If no match → return `None`
- If match found:
  - `duplicate_action is None` → return `{guardrail_result: {action:"confirm", ...}}`
  - `duplicate_action == "proceed"` → return `None` (continue with fresh planning; old trip entry unchanged)
  - `duplicate_action == "cancel"` → return `{guardrail_result: {action:"cancel", response:"Planning cancelled."}}`

### Update `run_workflow_from_constraints` signature

```python
def run_workflow_from_constraints(
    constraints: dict,
    user_id: str | None = None,
    duplicate_action: str | None = None,
) -> TripState:
```

Add at the top of the function, before `route_retriever_node`:

```python
early_exit = _duplicate_guardrail(constraints, user_id, duplicate_action)
if early_exit is not None:
    state.update(early_exit)
    return state
```

---

## 6.3 `backend/memory/store.py`

Add two functions:

```python
def find_duplicate_trip(user_id: str, origin: str, destination: str) -> dict | None:
    """Return the first planned or completed past trip matching origin+destination, or None.
    Cancelled trips are skipped."""

def record_new_trip(user_id: str, constraints: dict) -> str:
    """Append a new past_trips entry with status='planned'. Returns the new trip_id."""
```

`record_new_trip` is called from `run_workflow_from_constraints` after the workflow completes successfully (i.e., `state.get("selected_itinerary")` is not None).

---

## 6.4 `backend/api/itinerary_routes.py`

Pass `user_id` and `duplicate_action` from the request into `run_workflow_from_constraints`:

```python
result = run_workflow_from_constraints(
    constraints,
    user_id=request.user_id,
    duplicate_action=request.duplicate_action,
)
```

---

## 6.5 `backend/models/requests.py` — `GenerateItineraryRequest`

Add one field:

```python
duplicate_action: Optional[Literal["proceed", "cancel"]] = None
```

---

## 6.6 `backend/models/responses.py` — `ItineraryResponse`

`guardrail_result` is already a field. No new fields needed — the frontend reads `guardrail_result.action == "confirm"` to show the duplicate dialog, same as it does for off-topic messages.

---

# 7. `guardrail_result` Shapes

### When duplicate found (planning halted)
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
      "planned_at": "2026-06-23T10:00:00Z",
      "trip_duration": "2D1N",
      "status": "planned"
    }
  },
  "recommended_itinerary": null,
  "timeline": null
}
```

### When user cancels
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

### When user proceeds (`duplicate_action: "proceed"`)
`guardrail_result` is `{}` (empty, cleared), full itinerary fields populated normally.

---

# 8. Frontend Behaviour (informational)

The frontend already handles `guardrail_result.action == "clarify"` (off-topic message) by showing a banner. Extend the same pattern:

- `action == "confirm"`: show a modal dialog with the `response` message and two buttons:
  - **"Yes, proceed"** → resend the request with `duplicate_action: "proceed"`
  - **"Cancel"** → resend with `duplicate_action: "cancel"` (or just dismiss locally)
- `action == "cancel"`: show a dismissible toast with `response` text

The `matched_trip` object can be used to show trip details (destination, date) in the dialog.

---

# 9. Deliverables

| Deliverable | File | Change |
|---|---|---|
| Upgraded `_find_similar_past_trip` (structured + text fallback, checks planned+completed) | `backend/agents/nodes/guardrail.py` | Modify existing function |
| Pass `origin`/`destination` into `_find_similar_past_trip` from `guardrail_node` | `backend/agents/nodes/guardrail.py` | Modify `guardrail_node` |
| `_duplicate_guardrail()` helper | `backend/agents/workflow.py` | New function |
| Updated `run_workflow_from_constraints` signature + early-exit call | `backend/agents/workflow.py` | Modify existing function |
| `find_duplicate_trip()` | `backend/memory/store.py` | New function |
| `record_new_trip()` | `backend/memory/store.py` | New function |
| `duplicate_action` field | `backend/models/requests.py` | New field on `GenerateItineraryRequest` |
| Pass `user_id` + `duplicate_action` to workflow | `backend/api/itinerary_routes.py` | Modify route handler |

**No new files.** All changes go into existing modules.

---

# 10. Acceptance Criteria

## AC 1 — Duplicate halts generate-itinerary before any agent runs
Given a second call to `/api/generate-itinerary` with same origin + destination (no `duplicate_action`),
the system shall return `guardrail_result.action == "confirm"` and `recommended_itinerary == null`.
No calls to `route_retriever_node`, `data_retriever_node`, or any downstream agent shall occur.

## AC 2 — Warning message contains trip details
`guardrail_result.response` shall include the destination, origin, and `planned_at` date in human-readable form.
`guardrail_result.matched_trip` shall include the full matched past_trips entry.

## AC 3 — `duplicate_action: "proceed"` runs planning unchanged
Given `duplicate_action: "proceed"`,
the full planning workflow shall run and return an itinerary.
The matched past trip's status shall remain unchanged in memory.

## AC 4 — `duplicate_action: "cancel"` returns immediately without planning
Given `duplicate_action: "cancel"`,
`guardrail_result.action` shall equal `"cancel"` and no itinerary fields shall be populated.

## AC 5 — Completed trips are also flagged
Given a past trip with `status: "completed"`,
a new plan for the same origin and destination shall return `guardrail_result.action == "confirm"`,
asking the user whether to proceed.

## AC 6 — Anonymous users bypass the check
Given no `user_id` in the request and no auth token,
the duplicate check is skipped and planning proceeds immediately.

## AC 7 — Memory failure is non-fatal
Given a failure to load `past_trips` from memory,
the duplicate check is skipped with a logged warning and planning proceeds.

## AC 8 — Successful plan writes a new past_trips entry
Given a completed planning run,
a new entry with `status: "planned"`, a UUID `trip_id`, and a `constraints_snapshot` shall be appended to the user's `past_trips`.

## AC 9 — parse-chat path also gets the upgrade
Given a `/api/parse-chat` call where origin and destination are extractable from state,
`guardrail_node` shall use the structured fingerprint match (not just text keyword).

---

# 11. Out of Scope

- Fuzzy city alias matching ("Gurgaon" == "Gurugram")
- Date-based deduplication (same route on different dates still triggers)
- A standalone `/api/trips/{trip_id}/status` endpoint (not needed — `duplicate_action` handles status updates inline)
- Deleting past trip entries
- Duplicate detection across group members
