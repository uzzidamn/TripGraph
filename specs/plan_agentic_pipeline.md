# Bucket 2: LangGraph Agentic Pipeline — Execution Plan

> **Spec**: `specs/bucket_2_agentic_pipeline.md`
> **Date**: 2026-06-17
> **Status**: Ready to execute

---

## 1. Starting State

### Already exists (do NOT recreate):
| Path | Status |
|------|--------|
| `backend/planner/candidate_generator.py` | Done — `generate_candidates(constraints, data)` |
| `backend/planner/scorer.py` | Done — `score_itinerary(itinerary, constraints)` |
| `backend/planner/validator.py` | Done — `validate_itinerary(itinerary, constraints)` |
| `backend/planner/timeline_generator.py` | Done — `generate_timeline(itinerary)` |
| `backend/planner/replanner.py` | Done — `replan_itinerary(itinerary, delay_event, constraints)` |
| `backend/tools/route_tool.py` | Done — `get_routes(origin, destination_type)` |
| `backend/tools/hotel_tool.py` | Done — `get_hotels(destination, tier)` |
| `backend/tools/activity_tool.py` | Done — `get_activities(destination, tags)` |
| `backend/tools/transport_tool.py` | Done — `get_transport_options(route_id, modes)` |
| `backend/tools/restaurant_tool.py` | Done — `get_restaurants(destination, route_id)` |
| `backend/tools/waypoint_tool.py` | Done — `get_waypoints(route_id)` |
| `backend/agents_augmented/` | Done — Bucket 2.1 single-LLM pipeline |
| `backend/__init__.py` | Done |

### Does NOT exist yet (build these):
- `backend/agents/` package (entire directory)
- `backend/tests/test_bucket_2.py`
- `specs/logs/bucket_2_decisions.md`

---

## 2. Dependencies to Add

Append to `backend/requirements.txt` (currently only has `neo4j>=5.0.0` and `python-dotenv>=1.0.0`):

```
langgraph>=0.2.0
langchain-core>=0.3.0
langchain-google-genai>=2.0.0
langchain-anthropic>=0.2.0
langsmith>=0.1.0
google-genai>=0.8.0
python-dotenv>=1.0.0
```

Install only provider packages needed. `langchain-openai` and `langchain-ollama` are optional; skip unless testing those providers.

---

## 3. Build Order

Execute in this exact order — each step depends on the previous.

### Step 1 — Package init files

**File**: `backend/agents/__init__.py`
```python
# Agents package
```

**File**: `backend/agents/nodes/__init__.py`
```python
# Agent nodes package
```

**File**: `backend/tests/__init__.py`
```python
```

---

### Step 2 — `backend/agents/state.py`

Copy `TripState` TypedDict from spec Section B.1 verbatim. No additions, no removals.

```python
from typing import TypedDict, List, Dict, Any, Optional

class TripState(TypedDict):
    raw_chat: List[str]
    extracted_constraints: Dict[str, Any]
    missing_fields: List[str]
    assumptions: Dict[str, str]
    conflict_report: Dict[str, Any]
    is_ready_to_plan: bool
    route_candidates: List[Dict[str, Any]]
    hotel_candidates: List[Dict[str, Any]]
    transport_candidates: List[Dict[str, Any]]
    activity_candidates: List[Dict[str, Any]]
    food_candidates: List[Dict[str, Any]]
    waypoint_candidates: List[Dict[str, Any]]
    itinerary_candidates: List[Dict[str, Any]]
    selected_itinerary: Optional[Dict[str, Any]]
    alternative_itineraries: List[Dict[str, Any]]
    validation_report: Dict[str, Any]
    score_breakdown: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    map_points: List[Dict[str, Any]]
    cost_breakdown: Dict[str, Any]
    explanation: str
    trace_id: Optional[str]
    delay_event: Optional[Dict[str, Any]]
    replanned_itinerary: Optional[Dict[str, Any]]
    replanning_explanation: Optional[str]
```

**Also add** `init_state(chat_messages)` helper that returns a fully initialized dict (all list fields = `[]`, all dict fields = `{}`, all Optional fields = `None`, `is_ready_to_plan = False`, `explanation = ""`, `raw_chat = chat_messages`).

---

### Step 3 — `backend/agents/llm_client.py`

Implement the rate limiter, four public functions, and one private helper.

#### Rate limiter (module-level, Decision 10)

Declare at the top of the file, after imports:

```python
import time
from collections import deque
from threading import Lock

_rate_limit_rpm: int = int(os.getenv("LLM_RATE_LIMIT_RPM", "15"))
_call_timestamps: deque = deque()
_rate_lock: Lock = Lock()

def _wait_for_rate_limit() -> None:
    with _rate_lock:
        now = time.monotonic()
        while _call_timestamps and now - _call_timestamps[0] >= 60.0:
            _call_timestamps.popleft()
        if len(_call_timestamps) >= _rate_limit_rpm:
            sleep_for = 60.0 - (now - _call_timestamps[0])
            if sleep_for > 0:
                print(f"[RATE LIMIT] Sleeping {sleep_for:.1f}s to stay under {_rate_limit_rpm} RPM")
                time.sleep(sleep_for)
            now = time.monotonic()
            while _call_timestamps and now - _call_timestamps[0] >= 60.0:
                _call_timestamps.popleft()
        _call_timestamps.append(time.monotonic())
```

- Uses a **sliding 60-second window** — proactive, never breaches the limit.
- Thread-safe via `Lock`; safe across concurrent LangGraph node calls.
- `_rate_limit_rpm` is read once at module import — changing `LLM_RATE_LIMIT_RPM` at runtime has no effect.
- **Call timing**: each node must call `get_llm()` / `get_llm_json()` immediately before `.invoke()`, not at module load time. The rate check fires at construction — calling at load time silently skips it.

#### `get_llm(run_name=None) -> BaseChatModel`

Call `_wait_for_rate_limit()` as the **first line** before constructing any LLM. Then read `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE`. Supported providers:
- `gemini` → `ChatGoogleGenerativeAI` from `langchain-google-genai>=2.0`
- `claude` → `ChatAnthropic`; **must** also pass `max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))`
- `openai` → `ChatOpenAI`
- `ollama` → `ChatOllama`

Pass `run_name` via `**config` on the constructor so each LLM call appears as a named span in LangSmith.

#### `get_llm_json(run_name=None) -> BaseChatModel`

Call `_wait_for_rate_limit()` as the **first line** — same requirement as `get_llm()`. The Gemini and Claude branches in this function construct their LLM directly (they do not call `get_llm()` internally), so the rate check MUST be here explicitly. Without it, JSON-output nodes (chat_parser, explainer, replanner_agent) bypass the limiter entirely.

For Gemini, add:
```python
generation_config={"response_mime_type": "application/json"}
```
**Do NOT use `model_kwargs`** (deprecated old-SDK pattern). For Claude, JSON enforcement is done via assistant prefill in `_build_messages()` — no constructor change needed.

For openai/ollama, fall back to `return get_llm(run_name=run_name)` (rate limit already counted there).

#### `get_provider() -> str`
```python
return os.getenv("LLM_PROVIDER", "gemini")
```

#### `get_trace_url() -> str | None`
Returns LangSmith trace URL if `LANGCHAIN_TRACING_V2=true`, else `None`. Uses `langsmith.Client`.

**LangSmith note**: tracing is zero-config. LangChain reads `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` at import time. No code needed in nodes.

---

### Step 4 — `backend/agents/prompts.py`

Implement 8 prompt constants. Each JSON-output prompt must:
- Instruct the LLM to output **ONLY valid JSON**, no extra text
- Include the exact expected schema
- Say "Do NOT invent information"
- Tell the LLM to use `.title()` casing for location names, lowercase for all enum fields

#### Prompts to implement:

| Constant | Used in | LLM |
|----------|---------|-----|
| `CHAT_PARSER_SYSTEM` | `chat_parser_node` | JSON |
| `CHAT_PARSER_HUMAN` | `chat_parser_node` | JSON; takes `{chat_text}` |
| `CONSTRAINT_VALIDATOR_SYSTEM` | (unused — validator is pure Python) | — |
| `CONSTRAINT_VALIDATOR_HUMAN` | (unused) | — |
| `EXPLAINER_SYSTEM` | `explainer_node` | JSON |
| `EXPLAINER_HUMAN` | `explainer_node` | JSON; takes `{constraints_json}`, `{itinerary_json}`, `{timeline_json}` |
| `REPLANNER_EXPLAIN_SYSTEM` | `replanner_agent_node` | JSON |
| `REPLANNER_EXPLAIN_HUMAN` | `replanner_agent_node` | JSON; takes `{constraints_json}`, `{original_itinerary_json}`, `{updated_itinerary_json}`, `{changes_json}`, `{delay_event_json}` |

**`CHAT_PARSER_HUMAN`** must embed the Section B.5 constraint schema and tell the LLM:
- location fields use `.title()` casing: `"Gurugram"`, `"Rishikesh"`
- enum fields lowercase: `hotel_tier`, `risk_tolerance`, `destination_type`, items in `transport_preference` and `must_include`
- missing fields → `null` (not absent)

**`EXPLAINER_HUMAN`** must ask for a `{"explanation": "..."}` JSON (single key) — plain text inside the value. Do NOT ask for the full TripState — just the explanation field.

**`REPLANNER_EXPLAIN_HUMAN`** must ask for `{"replanning_explanation": "..."}` JSON.

---

### Step 5 — `backend/agents/nodes/mock_tools.py`

Implement all 6 mock functions with the same signatures as real tools (spec Section B.2). Use mock data from spec Section B.4. Each function must filter by the optional argument if provided.

```python
def get_routes(origin: str, destination_type: str | None = None) -> list[dict]:
    results = [r for r in MOCK_ROUTES if r["origin"].lower() == origin.lower()]
    if destination_type:
        results = [r for r in results if r["destination_type"] == destination_type.lower()]
    return results

def get_hotels(destination: str, tier: str | None = None) -> list[dict]:
    results = [h for h in MOCK_HOTELS if h.get("destination", "").lower() == destination.lower()]
    if tier:
        results = [h for h in results if h["tier"] == tier.lower()]
    return results

# ... same pattern for get_activities, get_transport_options, get_restaurants, get_waypoints
```

**Pitfall**: `get_transport_options` filters by `route_id`, not `destination`. `get_waypoints` also filters by `route_id`.

---

### Step 6 — `backend/agents/nodes/chat_parser.py`

**Function**: `chat_parser_node(state: TripState) -> dict`

Logic:
1. Format `state["raw_chat"]` as a single `chat_text` string
2. Call `_build_messages(CHAT_PARSER_SYSTEM, CHAT_PARSER_HUMAN.format(chat_text=chat_text))`
3. Call `get_llm_json(run_name="chat_parser").invoke(messages)`
4. Strip markdown fences from response (even with `response_mime_type`, Flash Lite sometimes wraps)
5. Parse JSON (Decision 7: retry once on invalid JSON)
6. **Immediately normalize** (Decision 21/22):
   - `origin`, `destination` → `.strip().title()`
   - `hotel_tier`, `risk_tolerance`, `destination_type` → `.strip().lower()`
   - each item in `transport_preference`, `must_include` → `.strip().lower()`
7. Apply defaults (Decisions 1–5): `group_size=4`, `hotel_tier="comfort"`, `risk_tolerance="medium"`, `origin="Gurugram"`, `trip_duration="2D1N"` — only if field is `None` after parsing
8. Return `{"extracted_constraints": parsed, "assumptions": assumptions_dict}`

**`_build_messages` helper** (defined in each JSON-output node):
```python
from backend.agents.llm_client import get_provider
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def _build_messages(system: str, human: str) -> list:
    msgs = [SystemMessage(content=system), HumanMessage(content=human)]
    if get_provider() == "claude":
        msgs.append(AIMessage(content="{"))  # prefill forces JSON-only output
    return msgs
```
When Claude prefill is active, prepend `{` to the raw response string before `json.loads()`.

**JSON retry** (Decision 7):
```python
raw = response.content
if get_provider() == "claude":
    raw = "{" + raw
raw = _strip_fences(raw)
try:
    parsed = json.loads(raw)
except json.JSONDecodeError:
    # retry once with a correction message
    ...
```

---

### Step 7 — `backend/agents/nodes/constraint_validator.py`

**Function**: `constraint_validator_node(state: TripState) -> dict`

**Pure Python — no LLM call.** Implements all constraint checks from spec Decision 20–27.

Logic (in order):
1. Read `extracted_constraints` from state; copy to `constraints` (don't mutate state directly)
2. **Normalize** (Decision 21/22): `.strip().title()` on location fields, `.strip().lower()` on enum fields. This is a safety net — `chat_parser_node` should have done this, but do it again defensively.
3. **Check required fields** (Decision 20): if `origin is None` → blocking conflict. If both `budget_per_person is None` AND `trip_duration is None` → blocking conflict. If none of (`destination_type`, `must_include`, `destination`) has a value → blocking conflict.
4. **Check destination/destination_type mismatch** (Decision 25): build a known lookup table (e.g., Rishikesh=mountains, Jaipur=heritage, Tirthan=nature). If both fields set and contradict → blocking conflict.
5. **Check invalid values**: `budget_per_person <= 0` or `group_size <= 0` → blocking conflict.
6. Build `conflict_report` shape (Decision 24):
   ```python
   {
       "has_conflicts": bool,
       "blocking_conflicts": [...],
       "warnings": [...],
   }
   ```
7. Set `is_ready_to_plan = len(blocking_conflicts) == 0`
8. Return `{"extracted_constraints": constraints, "conflict_report": conflict_report, "is_ready_to_plan": bool, "missing_fields": missing_fields}`

---

### Step 8 — `backend/agents/nodes/data_retriever.py`

**Function**: `data_retriever_node(state: TripState) -> dict`

Logic:
1. Read `PIPELINE_MODE`, `NEO4J_ENABLED` from env (Decision 35/36)
2. Import real or mock tools at module level with try/except fallback
3. Read `extracted_constraints`; **normalize locations** (Decision 21): `origin.strip().title()`, `destination.strip().title()` if present
4. Call `get_routes(origin, destination_type)` → `routes`
5. For each route: call `get_hotels`, `get_activities`, `get_transport_options`, `get_restaurants`, `get_waypoints`
6. Collect all results (deduplicated or flat lists)
7. If `NEO4J_ENABLED=true`, wrap each call in try/except; on exception: `print(f"[DATA] Tool failed, using mock: {e}")` then call mock equivalent
8. Return 6 state fields: `route_candidates`, `hotel_candidates`, `transport_candidates`, `activity_candidates`, `food_candidates`, `waypoint_candidates`

**Import block** (Decision 36):
```python
import os
_NEO4J = os.getenv("NEO4J_ENABLED", "false").lower() == "true"

if _NEO4J:
    from backend.tools.route_tool import get_routes
    # ... real tools
else:
    from backend.agents.nodes.mock_tools import get_routes
    # ... mock tools
```

**Pitfall**: aggregate across all routes. E.g., `hotel_candidates = []` then for each route: `hotel_candidates.extend(get_hotels(route["destination"]))`.

---

### Step 9 — `backend/agents/nodes/planner_orchestrator.py`

**Function**: `planner_orchestrator_node(state: TripState) -> dict`

Logic:
1. Build `data` dict with keys matching planner interface:
   ```python
   data = {
       "routes": state["route_candidates"],
       "hotels": state["hotel_candidates"],
       "transport": state["transport_candidates"],
       "activities": state["activity_candidates"],
       "food": state["food_candidates"],
       "waypoints": state["waypoint_candidates"],
   }
   ```
2. `candidates = generate_candidates(state["extracted_constraints"], data)`
3. For each candidate: `score = score_itinerary(c, constraints)` and `validation = validate_itinerary(c, constraints)`
4. Sort: valid first (score descending), then invalid
5. Select `selected = sorted_candidates[0]` (or best invalid if none valid — Decision 14)
6. `timeline = generate_timeline(selected)`
7. `map_points = _extract_map_points(selected)` (helper from spec Step 6)
8. Build `cost_breakdown = selected.get("cost_breakdown", {})`
9. Build warnings for budget exceeded (Decision 26) and must_include unavailable (Decision 27): merge into existing `conflict_report["warnings"]`
10. Return all 7 state fields: `selected_itinerary`, `alternative_itineraries` (up to 3, rest of sorted list — Decision 13), `itinerary_candidates`, `timeline`, `map_points`, `cost_breakdown`, `validation_report`, `score_breakdown`

**Map points helper** (Decision 15/16): copy `_extract_map_points()` from spec Section D, Step 6.

**Pitfall**: `trip_graph` in candidates is a non-serializable dataclass. Do NOT pass it to LLM prompts. Use `json.dumps(itinerary, default=str)` when including in prompts.

---

### Step 10 — `backend/agents/nodes/explainer.py`

**Function**: `explainer_node(state: TripState) -> dict`

Logic:
1. Build `human_prompt = EXPLAINER_HUMAN.format(...)` with JSON-serialized `extracted_constraints`, `selected_itinerary`, `timeline`
2. Call `get_llm_json(run_name="explainer").invoke(_build_messages(...))`
3. Strip fences; parse `{"explanation": "..."}` JSON
4. Return `{"explanation": parsed["explanation"]}`

**Pitfall**: Don't pass `trip_graph` to the LLM. Strip it from `selected_itinerary` before formatting: `{k: v for k, v in itinerary.items() if k != "trip_graph"}`.

---

### Step 11 — `backend/agents/nodes/replanner_agent.py`

**Function**: `replanner_agent_node(state: TripState) -> dict`

Logic:
1. Call planner: `result = replan_itinerary(state["selected_itinerary"], state["delay_event"], state["extracted_constraints"])`
2. Build `human_prompt = REPLANNER_EXPLAIN_HUMAN.format(...)` with constraints, original/updated itineraries, changes, delay_event
3. Call `get_llm_json(run_name="replanner_agent").invoke(_build_messages(...))`
4. Parse `{"replanning_explanation": "..."}` JSON
5. Return `{"replanned_itinerary": result["updated_itinerary"], "replanning_explanation": parsed["replanning_explanation"]}`

---

### Step 12 — `backend/agents/workflow.py`

Implements the public API and LangGraph state machines.

#### Public API (Decision 35):

```python
def run_workflow(chat_messages: list[str]) -> TripState:
    engine = os.getenv("PIPELINE_MODE", "langgraph")   # env var is PIPELINE_MODE
    if engine == "augmented_llm":
        from backend.agents_augmented.workflow import run_workflow as _run
        return _run(chat_messages)
    return _langgraph_run_workflow(chat_messages)

def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    engine = os.getenv("PIPELINE_MODE", "langgraph")
    if engine == "augmented_llm":
        from backend.agents_augmented.workflow import run_replan_workflow as _replan
        return _replan(state, delay_event)
    return _langgraph_replan_workflow(state, delay_event)
```

#### Main LangGraph workflow:

```
START → chat_parser → constraint_validator → [conditional] → retrieve_data
                                                     ↓ (not ready)
                                                    END
retrieve_data → planner_orchestrator → explainer → END
```

Conditional edge after `constraint_validator`:
```python
def _should_plan(state):
    return "retrieve_data" if state["is_ready_to_plan"] else END
```

After `_langgraph_run_workflow()` completes, call `get_trace_url()` and store in `state["trace_id"]`.

#### Replan workflow:
```
START → replanner_agent → END
```
State is initialized from the existing `TripState` passed in, with `delay_event` set.

#### `_init_state()` call:
`run_workflow()` must call `init_state(chat_messages)` to produce a fully initialized TripState — all fields must have values. Missing keys cause LangGraph errors.

---

### Step 13 — Update `backend/requirements.txt`

Add after existing content:
```
langgraph>=0.2.0
langchain-core>=0.3.0
langchain-google-genai>=2.0.0
langchain-anthropic>=0.2.0
langsmith>=0.1.0
google-genai>=0.8.0
```

---

### Step 14 — `backend/tests/test_bucket_2.py`

> **Note**: test script uses `PIPELINE_MODE` (not `WORKFLOW_ENGINE`) for engine switching tests.

Copy the validation script from spec Section F verbatim. The script:
- Tests TripState import
- Tests LLM init (skipped if no API key)
- Tests prompt loading
- Tests `run_workflow` / `run_replan_workflow` imports
- Runs end-to-end if `GOOGLE_API_KEY` is set

Run with: `PYTHONPATH=. python backend/tests/test_bucket_2.py`

---

### Step 15 — `specs/logs/bucket_2_decisions.md`

Create the decisions log (spec Section G). Required fields:
- Pre-Specified Decisions Applied
- Unspecified Decisions Made During Build
- Deviations from Spec
- External Assumptions
- Validation Results

---

### Step 16 — `backend/agents/run.py`

Create an output inspection script at **`backend/agents/run.py`** (inside the agents package, not at the project root).

Purpose: manually see exactly what the system produces for a given input — no pass/fail logic, no CLI args. Runs both the full workflow and replanning workflow with hardcoded sample inputs, then prints every TripState field so you can read and evaluate the raw output.

Key design:
- **No argparse** — hardcoded `SAMPLE_CHAT` and `SAMPLE_DELAY_EVENT` constants
- `_print_section(title, value)` helper: prints each field with a divider line; uses `json.dumps` for dicts/lists
- `_serializable(obj)` helper: recursively converts non-JSON-serializable objects (e.g. planner dataclasses) to strings
- Runs full workflow first, then immediately passes that state to replanning workflow
- Prints env config at startup (`NEO4J_ENABLED`, `LLM_PROVIDER`, `LLM_MODEL`)

**Run commands:**
```bash
# From project root — mock data, no API key needed
PYTHONPATH=. NEO4J_ENABLED=false python backend/agents/run.py

# With Gemini API key and real LLM output
PYTHONPATH=. GOOGLE_API_KEY=... python backend/agents/run.py

# With Claude
PYTHONPATH=. LLM_PROVIDER=claude ANTHROPIC_API_KEY=... python backend/agents/run.py

# Pipe to a file to review the full output
PYTHONPATH=. NEO4J_ENABLED=false python backend/agents/run.py > output.txt
```

Acceptance criteria tied to this file (spec Section H):
- `PYTHONPATH=. NEO4J_ENABLED=false python backend/agents/run.py` runs without crashing and prints all TripState fields
- Output shows a non-empty `explanation` and at least one `timeline` event
- Output shows a non-empty `replanning_explanation` in the replan section

---

## 4. Decision Reference

All 36 decisions from spec Section C, indexed here for quick lookup during implementation:

| # | Where Applied | Key Rule |
|---|---------------|----------|
| 1 | `chat_parser_node` | Default `group_size = 4` |
| 2 | `chat_parser_node` | Default `hotel_tier = "comfort"` |
| 3 | `chat_parser_node` | Default `risk_tolerance = "medium"` |
| 4 | `chat_parser_node` | Default `origin = "Gurugram"` |
| 5 | `chat_parser_node` | Default `trip_duration = "2D1N"` |
| 6 | All JSON-parsing nodes | Handle raw JSON, ` ```json ``` `, ` ``` ``` ` — strip fences before `json.loads()` |
| 7 | `chat_parser_node`, `explainer_node`, `replanner_agent_node` | Retry once on invalid JSON; on second failure use empty defaults |
| 8 | All nodes with LLM calls | Catch exception, log with `print(f"[ERROR] LLM call failed: {e}")`, re-raise (spec Section H requires this exact prefix for acceptance) |
| 9 | `llm_client.py` | `LLM_TEMPERATURE=0` |
| 10 | `llm_client.py` | Module-level `deque`+`Lock` sliding 60-second window. `_wait_for_rate_limit()` must be the **first line** of both `get_llm()` AND `get_llm_json()`. Call either function immediately before `.invoke()`, not at module load time. Default `LLM_RATE_LIMIT_RPM=15`. Logs `[RATE LIMIT] Sleeping Xs` when throttling. `llm.with_retry(stop_after_attempt=3)` applied separately for transient API errors. |
| 11 | `planner_orchestrator_node` | Empty `must_include` → accept all activities |
| 12 | `planner_orchestrator_node` | `avoid_night_driving=false` → do NOT penalize |
| 13 | `planner_orchestrator_node` | Up to 3 alternatives in `alternative_itineraries` |
| 14 | `planner_orchestrator_node` | No valid candidates → use best invalid; `validation_report.is_valid=False` |
| 15 | `planner_orchestrator_node` | `map_points`: origin, waypoints, destination, hotel, activities |
| 16 | `planner_orchestrator_node` | `map_points` type values: `"origin"`, `"waypoint"`, `"destination"`, `"hotel"`, `"activity"` |
| 17 | `workflow.py` | Public exports: `run_workflow(chat_messages)`, `run_replan_workflow(state, delay_event)` |
| 18 | `requirements.txt`, `llm_client.py` | `google-genai` + `langchain-google-genai>=2.0` for Gemini; `langchain-anthropic` for Claude |
| 19 | `data_retriever_node` | try real import, fallback to mock on ImportError |
| 20 | `constraint_validator_node` | Required: `origin` AND (`budget_per_person` OR `trip_duration`) AND ≥1 preference |
| 21 | `chat_parser_node`, `data_retriever_node` | Location names → `.strip().title()` |
| 22 | `constraint_validator_node` | Enum fields → `.strip().lower()` |
| 23 | `planner_orchestrator_node` | `must_include` matching: normalize to lowercase, substring match on name and tags |
| 24 | `constraint_validator_node` | `conflict_report` shape: `has_conflicts`, `blocking_conflicts`, `warnings` |
| 25 | `constraint_validator_node` | destination/destination_type mismatch → blocking conflict |
| 26 | `planner_orchestrator_node` | Budget exceeded → warning in `conflict_report`, still return best itinerary |
| 27 | `planner_orchestrator_node` | must_include not satisfiable → warning in `conflict_report`, planning continues |
| 28 | `llm_client.py` | LangSmith zero-config; pass `run_name` to each `get_llm()` call |
| 29 | `llm_client.py` | Each `invoke()` produces a span with inputs/outputs/tokens/latency |
| 30 | `workflow.py` | Call `get_trace_url()` after workflow, store in `state["trace_id"]` |
| 31 | `requirements.txt` | Add `langsmith` as dependency |
| 32 | `llm_client.py`, all nodes | Claude: system prompt as `SystemMessage` at index 0 via `_build_messages()` |
| 33 | `llm_client.py` | Claude: `max_tokens` required, read from `LLM_MAX_TOKENS` env var |
| 34 | All nodes using tools | Claude: no `anyOf`/union types in tool schemas — use explicit `type: string` |
| 35 | `workflow.py` | `PIPELINE_MODE` routes to LangGraph or augmented_llm backend (renamed from `WORKFLOW_ENGINE`) |
| 36 | `data_retriever_node` | `NEO4J_ENABLED=false` → mock; `true` → real with try/except mock fallback |

---

## 5. Prompt Content Guidance

### CHAT_PARSER_SYSTEM
```
You are a travel constraint extractor. Given group chat messages, extract structured travel preferences.
Output ONLY a valid JSON object matching this schema exactly. Do NOT invent information.
Use .title() casing for location names (e.g., "Gurugram", "Rishikesh").
Use lowercase for enum fields: hotel_tier, risk_tolerance, destination_type, transport_preference items, must_include items.
Use null for any field not mentioned — do NOT omit keys.

Schema: [embed Section B.5 dict with key: type annotations]
```

### CHAT_PARSER_HUMAN
```
Group chat messages:
{chat_text}

Extract travel constraints from these messages as JSON.
```

### EXPLAINER_SYSTEM
```
You are a travel planner assistant. Generate a friendly, concise explanation of the recommended itinerary.
Output ONLY a JSON object: {"explanation": "..."}.
The explanation should cover: destination, transport, hotel, key activities, and why it fits the group's budget and preferences.
2-4 sentences. Do NOT invent any details not in the provided data.
```

### EXPLAINER_HUMAN
```
Constraints:
{constraints_json}

Selected itinerary:
{itinerary_json}

Day-by-day timeline:
{timeline_json}

Generate the explanation JSON.
```

### REPLANNER_EXPLAIN_SYSTEM
```
You are a travel replanning assistant. Explain what changed when the itinerary was adjusted for a delay.
Output ONLY a JSON object: {"replanning_explanation": "..."}.
Be concise. Cover: what caused the delay, what was shifted or removed, and whether the trip still works.
Do NOT invent details not in the provided data.
```

### REPLANNER_EXPLAIN_HUMAN
```
Original constraints:
{constraints_json}

Original itinerary:
{original_itinerary_json}

Updated itinerary after delay:
{updated_itinerary_json}

Changes made:
{changes_json}

Delay event:
{delay_event_json}

Generate the replanning explanation JSON.
```

---

## 6. Common Pitfalls

1. **`trip_graph` in candidates** — non-serializable dataclass. Strip it before passing any itinerary to an LLM prompt. Safe pattern: `{k: v for k, v in itinerary.items() if k != "trip_graph"}`.

2. **TripState initialization** — every field must have a value in `init_state()`. Missing keys cause LangGraph errors at graph compile time or runtime.

3. **Consecutive same-role messages in LangChain** — both Gemini and Claude require strict user/model alternation. Never call `HumanMessage` twice in a row. If retrying after JSON parse failure, inject the correction as the next human message only after the previous AI response.

4. **Gemini JSON wrapping** — even with `response_mime_type="application/json"`, Gemini Flash Lite sometimes wraps JSON in ` ```json ``` `. Always strip fences before `json.loads()`.

5. **Claude prefill** — when `AIMessage(content="{")` is appended as prefill, prepend `{` to the raw `.content` string before parsing. Don't double-prepend.

6. **`response_mime_type` vs `model_kwargs`** — use `generation_config={"response_mime_type": "application/json"}` as a constructor argument to `ChatGoogleGenerativeAI`. The old `model_kwargs={"response_mime_type": ...}` pattern is deprecated.

7. **`get_llm().with_retry()`** — LangChain retry wraps the chain, not just the LLM object. Call `.with_retry(stop_after_attempt=3)` on the result of `get_llm()`.

8. **`data` keys in `generate_candidates`** — must be exactly: `routes`, `hotels`, `transport`, `activities`, `food`, `waypoints`. The planner will KeyError on any other names.

9. **`destination_type` normalization** — mock data uses lowercase values (`"mountains"`, `"heritage"`). Extracted constraints must be `.lower()` before filtering.

10. **Map points for origin** — origin has no lat/lng in mock route data. Hardcode Gurugram: `{"lat": 28.4595, "lng": 77.0266, "label": "Gurugram", "type": "origin"}` as per spec helper.

11. **`get_llm_json()` bypasses rate limiter if `_wait_for_rate_limit()` is missing** — the Gemini and Claude branches in `get_llm_json()` construct their LLM objects directly without going through `get_llm()`. If `_wait_for_rate_limit()` is only added to `get_llm()` and forgotten in `get_llm_json()`, all JSON-output nodes (chat_parser, explainer, replanner_agent) will ignore the RPM cap and hit API rate limit errors. Both functions need the call at their first line.

---

## 7. Test Plan

### Unit-level (no API key needed)
- Import `TripState` — verify all 26 fields present
- Import `get_llm`, `get_llm_json`, `get_provider`, `get_trace_url`
- Import all 8 prompt constants from `prompts.py`
- Import `run_workflow`, `run_replan_workflow` from `workflow.py`
- Run `constraint_validator_node` with missing/conflicting inputs — check `is_ready_to_plan=False`
- Run `data_retriever_node` with `NEO4J_ENABLED=false` — check mock data returned

### Integration (requires `GOOGLE_API_KEY`)
```bash
PYTHONPATH=. python backend/tests/test_bucket_2.py
```
Expected output:
- Constraints extracted with origin=Gurugram
- Selected itinerary destination present
- Timeline has ≥1 event
- Map points has ≥1 point
- Explanation is a non-empty string

### Replan test (requires `GOOGLE_API_KEY`)
After a successful `run_workflow()` call, pass the returned state to `run_replan_workflow()`:
```python
state = run_workflow(["Weekend trip from Gurugram, mountains, budget 15k"])
delay = {"delay_type": "traffic_jam", "delay_minutes": 90}
replanned = run_replan_workflow(state, delay)
assert replanned["replanned_itinerary"] is not None
assert replanned["replanning_explanation"]
```

### Engine switching
```bash
PIPELINE_MODE=langgraph PYTHONPATH=. python backend/tests/test_bucket_2.py     # LangGraph
PIPELINE_MODE=augmented_llm PYTHONPATH=. python backend/tests/test_bucket_2.py # Bucket 2.1
```

---

## 8. Acceptance Criteria Checklist

Full criteria are in spec **Section H**. Implementation-critical items reproduced here for cross-referencing during build.

### Safety & Rate Limit (most likely to be missed)
- [ ] `_wait_for_rate_limit()` is the first line of **both** `get_llm()` and `get_llm_json()`
- [ ] Rate limiter uses a sliding 60-second window — NOT a fixed reset interval
- [ ] Logs `[RATE LIMIT] Sleeping Xs to stay under N RPM` when throttling
- [ ] LLM failures log `[ERROR] LLM call failed: ...` and re-raise (not `❌`, not `print` and swallow)
- [ ] Invalid JSON retried once before falling back to empty defaults

### Provider
- [ ] `LLM_PROVIDER=gemini` → `ChatGoogleGenerativeAI` via `langchain-google-genai>=2.0`
- [ ] `LLM_PROVIDER=claude` → `ChatAnthropic` with explicit `max_tokens` from `LLM_MAX_TOKENS`
- [ ] JSON-output nodes use `get_llm_json()`: Gemini gets `generation_config={"response_mime_type": "application/json"}`, Claude gets `AIMessage(content="{")`
- [ ] Switching providers requires only `.env` change — zero code changes

### Architecture
- [ ] Only `run_workflow()` and `run_replan_workflow()` are public; Bucket 3 imports from `backend.agents.workflow` only
- [ ] `PIPELINE_MODE=augmented_llm` delegates to `backend.agents_augmented.workflow`
- [ ] No LangChain imports outside `llm_client.py` and node files

### State & Tools
- [ ] `TripState` matches spec Section B.1 exactly — no added/removed/renamed fields
- [ ] Every field initialized in `run_workflow()` (empty list/dict/None as appropriate)
- [ ] `NEO4J_ENABLED=false` runs fully on mock data (no Neo4j connection needed)
- [ ] Mock tool signatures are identical to real tools (Section B.2)

### Normalization
- [ ] `origin`, `destination` → `.strip().title()` in `chat_parser_node` immediately after JSON parse
- [ ] Enum fields → `.strip().lower()` in `constraint_validator_node`
- [ ] `must_include` matching uses case-insensitive substring match on activity `name` and `tags`

### Observability
- [ ] Each node passes `run_name="<node_name>"` to `get_llm()` / `get_llm_json()`
- [ ] `trace_id` populated from `get_trace_url()` when `LANGCHAIN_TRACING_V2=true`, else `None`

### Testing
- [ ] `test_bucket_2.py` passes with `NEO4J_ENABLED=false` (no API key needed for import/schema tests)
- [ ] End-to-end `run_workflow()` completes with all key fields populated
- [ ] `run_replan_workflow()` populates `replanned_itinerary` and `replanning_explanation`
- [ ] `PYTHONPATH=. NEO4J_ENABLED=false python backend/agents/run.py` runs without crashing and prints all TripState fields
- [ ] `backend/agents/run.py` output shows non-empty `explanation` and at least one `timeline` event
- [ ] `backend/agents/run.py` output shows non-empty `replanning_explanation` in the replan section
- [ ] `specs/logs/bucket_2_decisions.md` created and non-empty

---

## 9. File Manifest (Build Output)

```
backend/agents/__init__.py
backend/agents/llm_client.py
backend/agents/state.py
backend/agents/prompts.py
backend/agents/workflow.py
backend/agents/nodes/__init__.py
backend/agents/nodes/mock_tools.py
backend/agents/nodes/chat_parser.py
backend/agents/nodes/constraint_validator.py
backend/agents/nodes/data_retriever.py
backend/agents/nodes/planner_orchestrator.py
backend/agents/nodes/explainer.py
backend/agents/nodes/replanner_agent.py
backend/requirements.txt                        [UPDATED]
backend/tests/__init__.py
backend/tests/test_bucket_2.py
backend/agents/run.py                           [NEW — output inspection script]
specs/logs/bucket_2_decisions.md
```
