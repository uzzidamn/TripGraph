# Bucket 2.1: Tool-Augmented LLM — Execution Plan

Source spec: `specs/bucket_2.1_augmented_llm.md`

---

## Root Directory

All paths in this plan are relative to the TripGraph project root:

```
/home/celadon/workspace/naveen/DeepLearning/TripGraph/TripGraph/
```

Run all commands from this directory with `PYTHONPATH=.`.

---

## What This Is

A single LLM that autonomously decides which tools to call in a ReAct-style loop until it has enough data to produce a complete `TripState`. Python only runs tools and enforces safety limits — all orchestration decisions belong to the LLM.

This is **not** a linear pipeline. There are no fixed workflow steps, no hardcoded retrieval sequences.

---

## Architecture Summary

```
run_workflow(chat_messages)
    │
    ▼
LLMClient (Gemini or Claude, selected via LLM_PROVIDER env var)
    │
    ▼
ReAct Agent Loop
    ├── llm.invoke() → normalized_response
    │
    ├── if tool_call:
    │       result = execute_tool(tool_name, arguments)
    │       llm.add_tool_result(tool_call_id, tool_name, result)
    │       continue
    │
    └── if final_answer:
            parse TripState from response content
            return TripState
```

---

## Files to Build

All files go inside `backend/agents_augmented/` (relative to project root):

```
backend/
└── agents_augmented/
    ├── __init__.py                       Step 0 — package init
    ├── state.py                          Step 1 — TripState TypedDict + init_state()
    ├── prompts.py                        Step 2 — SYSTEM_PROMPT + REPLAN_CONTEXT_TEMPLATE
    ├── mock_tools.py                     Step 3 — mock implementations (runtime fallback for Neo4j)
    ├── tool_registry.py                  Step 4 — TOOLS list + Gemini/Claude schema converters
    ├── tool_executor.py                  Step 5 — execute_tool(): real tools → mock fallback on error
    ├── llm_client.py                     Step 6 — LLMClient class (Gemini + Claude providers)
    ├── workflow.py                       Step 7 — run_workflow() + run_replan_workflow()
    ├── run.py                            Step 8 — CLI test harness
    └── tests/
        ├── __init__.py
        ├── test_tool_execution.py        Step 9a — real tools (Neo4j) or mocks; no API key needed
        ├── test_llm_response_parsing.py  Step 9b — no external dependencies
        ├── test_safety_limits.py         Step 9c — no external dependencies
        ├── test_malformed_call.py        Step 9d — MALFORMED_FUNCTION_CALL recovery; no API key needed
        └── test_e2e.py                   Step 9e — opt-in only: requires RUN_E2E=true + API key
```

**Also update:** `.env` (project root) — add `MAX_TOOL_CALLS`, `MAX_ITERATIONS`, `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`; `backend/agents_augmented/requirements.txt` — swap `google-generativeai` for `google-genai`

**Do not touch:** `backend/tools/`, `backend/planner/`, `backend/knowledge_graph/` — real tools live here, imported directly by `tool_executor.py`.

---

## Existing `.env` (project root)

The `.env` at the project root already contains:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=<already set>
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=4096
PIPELINE_MODE=augmented
```

New entries to add in Step 10:

```env
MAX_TOOL_CALLS=20
MAX_ITERATIONS=25
LLM_RATE_LIMIT_RPM=5
ANTHROPIC_API_KEY=       # fill in to use LLM_PROVIDER=claude
CLAUDE_MODEL=claude-sonnet-4-6
```

---

## Decisions & Defaults (from spec)

These are pre-made decisions that must be coded exactly as specified. Do not deviate.

| # | Decision | Value / Rule |
|---|----------|-------------|
| 1 | Default `group_size` if not extracted | `4` |
| 2 | Default `hotel_tier` if not extracted | `"comfort"` |
| 3 | Default `risk_tolerance` if not extracted | `"medium"` |
| 4 | Default `origin` if not extracted | `"Gurugram"` |
| 5 | Default `trip_duration` if not extracted | `"2D1N"` |
| 6 | JSON parsing from LLM | Handle raw JSON, ` ```json ``` `, and ` ``` ``` ` wrapping. Strip fences before `json.loads()`. |
| 7 | LLM returns invalid JSON | Retry once. If still invalid, log and use empty defaults. Never crash. |
| 8 | LLM call fails (network / rate limit) | Catch, log `[LLM ERROR] {e}`, re-raise to propagate to API layer. |
| 9 | LLM temperature | `0` — deterministic output. |
| 10 | Rate limit handling | `LLMClient.invoke()` enforces `LLM_RATE_LIMIT_RPM=5` (≤ 5 LLM calls per minute) using a sliding-window tracker over call timestamps in the last 60 seconds. If the window is full (≥ 5 calls), sleep until the oldest call expires. Applies to **all providers**. No manual `time.sleep()` in `run.py` or `workflow.py`. |
| 11 | Empty `must_include` | No activity constraints; accept all activities. |
| 12 | `avoid_night_driving: false` | Night driving acceptable; do NOT penalize. |
| 13 | Alternative itineraries count | Up to 3 (lower-scored valid candidates + invalid candidates). |
| 14 | No valid candidates exist | Return highest-scored invalid candidate as `selected_itinerary` with `validation_report.is_valid = False`. |
| 15 | `map_points` extraction | lat/lng from: route origin, waypoints, destination city, hotel, each activity. Format: `{"lat": float, "lng": float, "label": str, "type": str}`. |
| 16 | `map_points` type values | `"origin"`, `"waypoint"`, `"destination"`, `"hotel"`, `"activity"` |
| 17 | Workflow export names | `run_workflow(chat_messages)` and `run_replan_workflow(state, delay_event)` — public API for Bucket 3. |
| 18 | LLM provider packages | `google-genai` for direct Gemini calls (`from google import genai`). The old `google-generativeai` package is deprecated and must NOT be used. No LangChain, no LangGraph. |
| 19 | Mock vs real tool imports | Try real imports at module level; `tool_executor.py` falls back to mocks at call time on exception. |
| 20 | What if Gemini returns `MALFORMED_FUNCTION_CALL` | Retry `invoke()` up to 2 times with the same message history. If still `MALFORMED_FUNCTION_CALL` after all retries, raise as an LLM error (handled by Decision 8). Do NOT silently skip or return a partial result. |

---

## Step 0 — `backend/agents_augmented/__init__.py`

Empty file. Marks directory as a Python package.

---

## Step 1 — `backend/agents_augmented/state.py`

Define `TripState` as a `TypedDict`. All 24 fields must be present — missing keys break downstream Bucket 3 Pydantic validation.

```python
from typing import TypedDict, Optional

class TripState(TypedDict):
    # Input
    raw_chat: list[str]
    # Constraint extraction
    extracted_constraints: Optional[dict]
    missing_fields: list[str]
    assumptions: dict
    # Constraint validation
    conflict_report: Optional[dict]
    is_ready_to_plan: bool
    # Data retrieval
    route_candidates: list[dict]
    hotel_candidates: list[dict]
    transport_candidates: list[dict]
    activity_candidates: list[dict]
    food_candidates: list[dict]
    waypoint_candidates: list[dict]
    # Planning
    itinerary_candidates: list[dict]
    selected_itinerary: Optional[dict]
    alternative_itineraries: list[dict]
    validation_report: Optional[dict]
    score_breakdown: Optional[dict]
    timeline: list[dict]
    map_points: list[dict]
    cost_breakdown: Optional[dict]
    # Explanation
    explanation: Optional[str]
    # Replanning
    delay_event: Optional[dict]
    replanned_itinerary: Optional[dict]
    replanning_explanation: Optional[str]
```

Also provide `init_state(chat_messages: list[str]) -> TripState` that sets every key to its empty default (`None`, `[]`, `{}`, `False`).

> **Pitfall**: Every field must be present even if empty. Missing keys cause Bucket 3 Pydantic validation to fail. Use `init_state()` as the baseline before merging any LLM output.

---

## Step 2 — `backend/agents_augmented/prompts.py`

Two constants:

**`SYSTEM_PROMPT`** — verbatim text from spec, plus a JSON schema reminder telling the LLM what TripState structure to return as its final answer (all 24 keys, no markdown fences):

```
You are TripGraph AI.
Your goal is to build a valid TripState.
You may use tools.
Rules:
1. Gather missing information through tools.
2. Never invent routes, hotels, activities, restaurants, transport options, or costs.
3. Use tool outputs as the source of truth.
4. Call validate_itinerary before finalizing.
5. Call generate_timeline before finalizing.
6. Return a complete TripState.
7. Stop only when TripState is complete.

When done, return ONLY valid JSON with all 24 TripState keys. No markdown fences.
```

**`REPLAN_CONTEXT_TEMPLATE`** — string template with `{existing_trip_state}` and `{delay_event}` placeholders used in `run_replan_workflow()`:

```
You are handling a replanning request.
Existing trip state: {existing_trip_state}
Delay event: {delay_event}
Call replan_itinerary() with the selected_itinerary, delay_event, and extracted_constraints.
Return an updated TripState JSON with replanned_itinerary and replanning_explanation populated.
```

---

## Step 3 — `backend/agents_augmented/mock_tools.py`

Runtime fallback for when Neo4j is unavailable. All 11 mock functions must use the exact same signatures as the real tools so `tool_executor.py` can swap them transparently.

```python
# Retrieval mocks — match backend/tools/ signatures
def get_routes(origin: str, destination_type: str | None = None) -> list[dict]: ...
def get_hotels(destination: str, tier: str | None = None) -> list[dict]: ...
def get_activities(destination: str, tags: list[str] | None = None) -> list[dict]: ...
def get_transport_options(route_id: str, modes: list[str] | None = None) -> list[dict]: ...
def get_restaurants(destination: str, route_id: str | None = None) -> list[dict]: ...
def get_waypoints(route_id: str) -> list[dict]: ...

# Planner mocks — match backend/planner/ signatures
def generate_candidates(constraints: dict, data: dict) -> list[dict]: ...
def score_itinerary(itinerary: dict, constraints: dict) -> dict: ...
def validate_itinerary(itinerary: dict, constraints: dict) -> dict: ...
def generate_timeline(itinerary: dict) -> list[dict]: ...
def replan_itinerary(itinerary: dict, delay_event: dict, constraints: dict) -> dict: ...
```

Each mock returns structurally valid, non-empty data for a **Gurugram → Rishikesh** trip. Field names must match the real tool outputs exactly so `generate_candidates()` (real or mock) can process the data without modification.

---

## Step 4 — `backend/agents_augmented/tool_registry.py`

Defines the tool schemas the LLM sees and exports helpers to convert them to provider-native format.

### `TOOLS` list (neutral format — unchanged)

One entry per tool, 11 total. Stays as plain dicts with lowercase `type` values — it's the source-of-truth; the converters below transform it per-provider.

```python
TOOLS = [
    {
        "name": "get_routes",
        "description": "...",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Departure city name"},
                "destination_type": {"type": "string", "description": "Optional filter: adventure, heritage, nature"}
            },
            "required": ["origin"]
        }
    },
    # ... all 11 tools ...
]

TOOL_NAMES: set[str] = {t["name"] for t in TOOLS}
```

### Provider schema converters

**`get_gemini_tool_schemas()`** — must return a **list of `types.Tool` objects** (not dicts) for the `google-genai` SDK. `types.Schema` requires `type` values in uppercase (`"OBJECT"`, `"STRING"`, `"ARRAY"`, `"INTEGER"`). The old `_sanitize_schema_for_gemini()` dict-based helper is replaced by a typed builder:

```python
from google.genai import types

def _build_gemini_schema(prop: dict) -> types.Schema:
    """Convert a neutral parameter property dict to a types.Schema object."""
    t = prop.get("type", "string").upper()
    kwargs = {"type": t, "description": prop.get("description", "")}
    if t == "ARRAY" and "items" in prop:
        kwargs["items"] = _build_gemini_schema(prop["items"])
    if t == "OBJECT" and "properties" in prop:
        kwargs["properties"] = {
            k: _build_gemini_schema(v) for k, v in prop["properties"].items()
        }
    return types.Schema(**kwargs)

def get_gemini_tool_schemas() -> list[types.Tool]:
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            k: _build_gemini_schema(v)
                            for k, v in t["parameters"].get("properties", {}).items()
                        },
                        required=t["parameters"].get("required", []),
                    ),
                )
                for t in TOOLS
            ]
        )
    ]
```

**`get_claude_tool_schemas()`** — unchanged:

```python
def get_claude_tool_schemas() -> list[dict]:
    return [
        {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
        for t in TOOLS
    ]
```

> **Note**: `_sanitize_schema_for_gemini()` is no longer needed — the strongly-typed `types.Schema` builder handles all schema correctness. Remove it if present.

---

## Step 5 — `backend/agents_augmented/tool_executor.py`

Imports real tools at the top level (they exist). At call time, if a real tool raises an exception (Neo4j down, connection error, etc.), `execute_tool()` automatically retries with the corresponding mock so the LLM always receives usable data.

```python
from backend.tools.route_tool import get_routes as _real_get_routes
# ... all 11 real imports ...

from backend.agents_augmented import mock_tools as _mocks

_REAL = {
    "get_routes": _real_get_routes,
    "get_hotels": _real_get_hotels,
    # ... all 11
}

_MOCK = {
    "get_routes": _mocks.get_routes,
    "get_hotels": _mocks.get_hotels,
    # ... all 11
}

def execute_tool(tool_name: str, arguments: dict) -> dict:
    if tool_name not in _REAL:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        result = _REAL[tool_name](**arguments)
        return {"result": result}
    except Exception:
        # Real tool failed (e.g. Neo4j unavailable) — use mock
        try:
            result = _MOCK[tool_name](**arguments)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}
```

This keeps the LLM loop unblocked even when the backend is not fully running.

### Location normalization (Pitfall 6)

Add a private helper at the top of `tool_executor.py`:

```python
def _normalize_location(value) -> str:
    """Normalize city/location strings to title case before tool dispatch."""
    if isinstance(value, str):
        return value.strip().title()
    return value
```

Apply it defensively in `execute_tool()` before forwarding arguments to any retrieval tool that takes a location parameter (`origin`, `destination`):

```python
if tool_name in {"get_routes", "get_hotels", "get_activities",
                 "get_restaurants", "get_waypoints"}:
    if "origin" in arguments:
        arguments = {**arguments, "origin": _normalize_location(arguments["origin"])}
    if "destination" in arguments:
        arguments = {**arguments, "destination": _normalize_location(arguments["destination"])}
```

This ensures "rishikesh", "GURUGRAM", and "riShikEsh" all hit Neo4j and mock comparisons correctly regardless of how the LLM formatted them.

---

## Step 6 — `backend/agents_augmented/llm_client.py`

Stateful `LLMClient` class. Each `run_workflow()` call creates a new instance. The client owns conversation history internally so `workflow.py` stays provider-agnostic.

### Environment variables

```python
LLM_PROVIDER       # "gemini" | "claude"   (default: "gemini")
LLM_MODEL          # model name            (default: "gemini-2.5-flash")
LLM_TEMPERATURE    # float                 (default: 0)
LLM_MAX_TOKENS     # int                   (default: 4096)
LLM_RATE_LIMIT_RPM # int                   (default: 5) — max LLM calls per 60s
GOOGLE_API_KEY     # required for Gemini
ANTHROPIC_API_KEY  # required for Claude
CLAUDE_MODEL       # overrides LLM_MODEL for Claude if set
```

### Rate limiting (base `LLMClient` — applies to all providers)

The base class owns a `self._call_timestamps: list[float]` and `self._rate_limit: int = LLM_RATE_LIMIT_RPM`.

At the **start of every `invoke()`** (before provider-specific code):
1. Prune timestamps older than 60 seconds from `self._call_timestamps`.
2. If `len(self._call_timestamps) >= self._rate_limit`, compute `sleep_secs = 60.0 - (now - self._call_timestamps[0])` and `time.sleep(sleep_secs)`.
3. After the API call returns, append `time.time()` to `self._call_timestamps`.

This must be implemented as a `_rate_limit_wait()` helper called from the base class's `invoke()` (or from the start of each provider's `invoke()` via `super()`). Both `GeminiClient` and `ClaudeClient` inherit this automatically.

### Public interface (provider-agnostic)

```python
class LLMClient:
    def add_user_message(self, content: str) -> None:
        """Enqueue a user message to send on next invoke()."""

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: dict) -> None:
        """Enqueue a tool result to send on next invoke()."""

    def invoke(self) -> dict:
        """
        Send pending message/result to the LLM, return normalized response:
          {"type": "tool_call", "tool_call_id": str, "tool_name": str, "arguments": dict}
          {"type": "final_answer", "content": str}
        """

def create_llm_client(system_prompt: str) -> LLMClient:
    """Factory: reads LLM_PROVIDER and returns GeminiClient or ClaudeClient."""
```

### GeminiClient implementation

Uses the `google-genai` SDK (`pip install google-genai`), NOT the deprecated `google-generativeai` package.

```python
from google import genai
from google.genai import types
```

The new SDK is **stateless** — there is no persistent chat object. The full conversation history must be passed on every call inside `self._contents`.

- **`__init__`**:
  ```python
  self._client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
  self._config = types.GenerateContentConfig(
      tools=get_gemini_tool_schemas(),
      system_instruction=system_prompt,
      temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
  )
  self._model = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
  self._contents: list = []   # full conversation history
  ```
  Note: system instruction goes in `GenerateContentConfig`, NOT in a model constructor.

- **`add_user_message(content)`**:
  ```python
  self._contents.append(
      types.Content(role="user", parts=[types.Part(text=content)])
  )
  ```

- **`add_tool_result(tool_call_id, tool_name, result)`**:
  ```python
  self._contents.append(
      types.Content(
          role="user",
          parts=[
              types.Part(
                  function_response=types.FunctionResponse(
                      name=tool_name,
                      response={"result": json.dumps(result, default=str)},
                  )
              )
          ],
      )
  )
  ```

- **`invoke()`** (after `_rate_limit_wait()`):
  ```python
  response = self._client.models.generate_content(
      model=self._model,
      contents=self._contents,
      config=self._config,
  )
  # Append model turn to maintain history
  self._contents.append(response.candidates[0].content)
  ```
  Then inspect response parts:
  - If any part has a `function_call` with a non-empty `.name` → return `{"type": "tool_call", "tool_call_id": str(uuid4()), "tool_name": fc.name, "arguments": dict(fc.args)}`
  - Otherwise → return `{"type": "final_answer", "content": response.text}`

### ClaudeClient implementation

- `__init__`: create `anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)`, store `system_prompt`, `tools=get_claude_tool_schemas()`, `self.messages = []`
- `add_user_message(content)`: append `{"role": "user", "content": content}` to `self.messages`
- `add_tool_result(tool_call_id, tool_name, result)`: append `{"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_call_id, "content": json.dumps(result)}]}` to `self.messages`
- `invoke()`: call `client.messages.create(model=CLAUDE_MODEL, max_tokens=LLM_MAX_TOKENS, system=system_prompt, tools=tools, messages=self.messages)`, append assistant response to `self.messages`:
  - If `response.stop_reason == "tool_use"` → find `type == "tool_use"` block → return `{"type": "tool_call", "tool_call_id": block.id, "tool_name": block.name, "arguments": block.input}`
  - Otherwise → find text block → return `{"type": "final_answer", "content": block.text}`

### Error handling

**Normal API/network errors** (auth, quota, connection): log `[LLM ERROR] {e}` and re-raise to `workflow.py`.

**MALFORMED_FUNCTION_CALL** (Gemini-specific, Decision 20):

```python
_malformed_retries = 0
MAX_MALFORMED_RETRIES = 2

while True:
    try:
        response = self._client.models.generate_content(
            model=self._model, contents=self._contents, config=self._config
        )
    except Exception as e:
        if "MALFORMED_FUNCTION_CALL" in str(e):
            _malformed_retries += 1
            if _malformed_retries >= MAX_MALFORMED_RETRIES:
                raise  # Decision 8: propagate to API layer
            self._contents.append(types.Content(
                role="user",
                parts=[types.Part(text=(
                    "Your previous function call had invalid arguments. "
                    "Retry with only simple values: strings, numbers, flat lists. "
                    "Avoid nested objects."
                ))]
            ))
            continue
        raise  # non-MALFORMED errors always re-raise immediately

    # Check finish_reason in response
    finish = response.candidates[0].finish_reason
    if getattr(finish, "name", str(finish)) == "MALFORMED_FUNCTION_CALL":
        _malformed_retries += 1
        if _malformed_retries >= MAX_MALFORMED_RETRIES:
            raise RuntimeError(f"MALFORMED_FUNCTION_CALL after {MAX_MALFORMED_RETRIES} retries")
        self._contents.append(types.Content(
            role="user",
            parts=[types.Part(text="Retry with simpler, flat arguments.")]
        ))
        continue

    break  # success — fall through to extract tool_call or final_answer
```

The primary prevention is strongly-typed `types.Schema` in `tool_registry.py`; this retry loop is the safety net.

**Empty / unrecognizable response**: return `{"type": "final_answer", "content": str(response)}`.

**Rate limit handling** (Decision 10): `LLMClient.invoke()` must enforce `LLM_RATE_LIMIT_RPM` (default `5`) using a **sliding-window timestamp tracker**:
- Before every `invoke()`, inspect the list of call timestamps from the last 60 seconds.
- If the count is ≥ `LLM_RATE_LIMIT_RPM`, compute how long until the oldest call falls outside the window and `time.sleep()` exactly that duration.
- Record the current timestamp immediately before the actual API call.
- This logic must live in the **base `LLMClient`** class so it applies to both `GeminiClient` and `ClaudeClient` without duplication.
- `LLM_RATE_LIMIT_RPM=5` (set in `.env`). No manual `time.sleep()` in `run.py` or `workflow.py`.

---

## Step 7 — `backend/agents_augmented/workflow.py`

Main orchestrator. Exports the two public API functions.

### Imports and safety limits

```python
import os, json
from dotenv import load_dotenv
load_dotenv()   # loads .env from project root

from backend.agents_augmented.state import TripState, init_state
from backend.agents_augmented.prompts import SYSTEM_PROMPT, REPLAN_CONTEXT_TEMPLATE
from backend.agents_augmented.tool_executor import execute_tool
from backend.agents_augmented.llm_client import create_llm_client
# No imports from mock_tools — real tools are used directly via tool_executor

MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", "20"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "25"))
```

### `run_workflow(chat_messages: list[str]) -> TripState`

```python
def run_workflow(chat_messages: list[str]) -> TripState:
    state = init_state(chat_messages)
    llm = create_llm_client(SYSTEM_PROMPT)
    llm.add_user_message(_format_user_request(chat_messages))

    tool_call_count = 0
    iteration_count = 0

    while True:
        if tool_call_count >= MAX_TOOL_CALLS or iteration_count >= MAX_ITERATIONS:
            state["conflict_report"] = {"error": "execution_limit_exceeded"}
            return state

        iteration_count += 1
        response = llm.invoke()

        if response["type"] == "tool_call":
            tool_call_count += 1
            result = execute_tool(response["tool_name"], response["arguments"])
            llm.add_tool_result(response["tool_call_id"], response["tool_name"], result)

        elif response["type"] == "final_answer":
            state = _parse_final_answer(response["content"], state)
            return state
```

**`_format_user_request(chat_messages)`** — joins messages with newlines, appends a reminder to produce complete TripState JSON using only tool-provided data.

**`_parse_final_answer(content, state)`** (Decision 6, 7):
1. Strip leading/trailing whitespace
2. If content starts with ` ``` ` → strip the fence (handle ` ```json ` and bare ` ``` `)
3. `json.loads(stripped)` → on success, merge all 24 TripState keys from parsed dict into state; unknown keys are silently ignored
4. On `json.JSONDecodeError` → set `state["explanation"] = content`, return partial state (never raise, never crash)

> **Note on map_points** (Decisions 15, 16): the LLM is instructed to populate `map_points` in the final TripState JSON. Each entry: `{"lat": float, "lng": float, "label": str, "type": "origin"|"waypoint"|"destination"|"hotel"|"activity"}`. Python does not compute these — the LLM extracts lat/lng from tool results.

> **Note on alternatives** (Decision 13): the LLM is instructed to populate `alternative_itineraries` with up to 3 lower-scored or invalid candidates.

> **Note on no valid candidates** (Decision 14): if `validation_report.is_valid == False` for all candidates, the LLM should set `selected_itinerary` to the highest-scored invalid one and set `validation_report.is_valid = False`.

> **Pitfall**: Use `json.dumps(result, default=str)` whenever tool results or state dicts are serialized to strings for LLM context. Planner dataclass instances are not JSON-serializable otherwise.

### `run_replan_workflow(state: TripState, delay_event: dict) -> TripState`

```python
def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    state["delay_event"] = delay_event

    if not state.get("selected_itinerary"):
        state["replanning_explanation"] = "No itinerary available to replan."
        return state

    context = REPLAN_CONTEXT_TEMPLATE.format(
        existing_trip_state=json.dumps(state, default=str),
        delay_event=json.dumps(delay_event),
    )

    llm = create_llm_client(SYSTEM_PROMPT)
    llm.add_user_message(context)

    tool_call_count = 0
    iteration_count = 0

    while True:
        if tool_call_count >= MAX_TOOL_CALLS or iteration_count >= MAX_ITERATIONS:
            state["conflict_report"] = {"error": "execution_limit_exceeded"}
            return state

        iteration_count += 1
        response = llm.invoke()

        if response["type"] == "tool_call":
            tool_call_count += 1
            result = execute_tool(response["tool_name"], response["arguments"])
            llm.add_tool_result(response["tool_call_id"], response["tool_name"], result)

        elif response["type"] == "final_answer":
            updated = _parse_final_answer(response["content"], dict(state))
            state["replanned_itinerary"] = updated.get("replanned_itinerary")
            state["replanning_explanation"] = updated.get("replanning_explanation")
            return state
```

---

## Step 8 — `backend/agents_augmented/run.py`

CLI harness. Run from project root:

```bash
PYTHONPATH=. python backend/agents_augmented/run.py
```

```python
#!/usr/bin/env python3
import json
from dotenv import load_dotenv
load_dotenv()  # finds .env in current working directory (project root)

from backend.agents_augmented.workflow import run_workflow, run_replan_workflow

SAMPLE_CHAT = [
    "Guys let's plan a trip from Gurugram",
    "Maybe Rishikesh? I want to do rafting",
    "Budget around 5000 per person",
    "Weekend trip, 4 of us",
]

def main():
    print("=== run_workflow ===")
    state = run_workflow(SAMPLE_CHAT)
    print(json.dumps(state, indent=2, default=str))

    print("\n=== run_replan_workflow ===")
    delay_event = {"delay_type": "departure_delay", "delay_minutes": 90}
    updated = run_replan_workflow(state, delay_event)
    print("replanned_itinerary:", json.dumps(updated.get("replanned_itinerary"), indent=2, default=str))
    print("replanning_explanation:", updated.get("replanning_explanation"))

if __name__ == "__main__":
    main()
```

---

## Step 9 — `backend/agents_augmented/tests/`

Run all tests from project root:

```bash
PYTHONPATH=. python -m pytest backend/agents_augmented/tests/ -v
```

### `tests/__init__.py`

Empty file.

### `tests/test_tool_execution.py` _(no external dependencies — uses mock fallback)_

Tests `execute_tool()` end-to-end. With Neo4j down the real tools will fail and the mock fallback kicks in — either way the result shape must be correct.

- `execute_tool("get_routes", {"origin": "Gurugram"})` → `{"result": [...]}` (non-empty list, never `{"error": ...}`)
- All 6 retrieval tools return `{"result": <non-empty list>}`
- `execute_tool("score_itinerary", {"itinerary": {...}, "constraints": {...}})` → `{"result": {"final_score": ...}}`
- `execute_tool("validate_itinerary", {"itinerary": {...}, "constraints": {...}})` → `{"result": {"is_valid": ...}}`
- `execute_tool("generate_timeline", {"itinerary": {...}})` → `{"result": [...]}`
- `execute_tool("nonexistent_tool", {})` → `{"error": ...}`

### `tests/test_llm_response_parsing.py` _(no external dependencies)_

Tests for `_parse_final_answer()` imported from `workflow.py`:

- Clean JSON string with TripState keys → all known keys merged into state
- JSON wrapped in ` ```json ... ``` ` → stripped and parsed correctly
- JSON wrapped in bare ` ``` ... ``` ` → stripped and parsed correctly
- Invalid JSON string → `state["explanation"]` set to raw content, no exception raised
- Partial JSON (only some TripState keys) → known keys merged, others retain `init_state` defaults

### `tests/test_safety_limits.py` _(no external dependencies)_

Tests that the loop exits when limits are hit (patch `create_llm_client`, no real LLM needed):

- Mock `LLMClient.invoke()` to always return `{"type": "tool_call", "tool_call_id": "x", "tool_name": "get_routes", "arguments": {"origin": "Gurugram"}}`
- With `MAX_TOOL_CALLS=3` override: after 3 tool calls, `state["conflict_report"]["error"] == "execution_limit_exceeded"`
- With `MAX_ITERATIONS=3` override: after 3 iterations, same result
- Verify execution terminates — no infinite loop
- Same limits apply to `run_replan_workflow()`

### `tests/test_malformed_call.py` _(no external dependencies — genai fully mocked)_

Tests `GeminiClient.invoke()` MALFORMED_FUNCTION_CALL recovery (Decision 20). The stub must mock the `google-genai` SDK (`from google import genai`) — NOT the deprecated `google.generativeai` package. Inject a minimal stub into `sys.modules["google.genai"]` and `sys.modules["google"]`.

**Exception path** — `generate_content()` raises `ValueError("finish_reason: MALFORMED_FUNCTION_CALL")`:
- First failure → retry #1; if retry #1 succeeds with a text response → result is `{"type": "final_answer", "content": <text>}`
- First failure → retry #1; if retry #1 succeeds with a tool call → result is `{"type": "tool_call", ...}`
- First failure → retry #1 → retry #2 → if retry #2 also raises MALFORMED → exception is **re-raised** (not swallowed)
- Non-MALFORMED exceptions (e.g. `ConnectionError`) are re-raised immediately without any retry

**Finish_reason path** — `generate_content()` succeeds but response `finish_reason` is `"MALFORMED_FUNCTION_CALL"`:
- Verify a correction message triggers a second `generate_content` call
- Verify the recovery response is returned normally
- Verify that 2 consecutive MALFORMED finish_reasons ultimately raise

### `tests/test_e2e.py` _(opt-in — requires `RUN_E2E=true` and a live API key)_

These tests make real LLM API calls and consume quota. They are **skipped by default** and must be explicitly enabled:

```bash
RUN_E2E=true PYTHONPATH=. pytest backend/agents_augmented/tests/test_e2e.py -v
```

```python
import os, pytest
_run_e2e = os.getenv("RUN_E2E", "").lower() in ("1", "true", "yes")
pytestmark = pytest.mark.skipif(
    not _run_e2e,
    reason="Set RUN_E2E=true to run end-to-end tests (they consume real API quota)"
)
```

- `run_workflow(SAMPLE_CHAT)` returns state where `state["selected_itinerary"] is not None`
- `state["timeline"]` is a non-empty list
- `state["validation_report"]` is not None
- No `langchain` or `langgraph` modules in `sys.modules`
- `run_replan_workflow(state, delay_event)` returns state where `state["replanned_itinerary"] is not None`

Neo4j is not required — mock fallback covers all tool calls if Neo4j is down.

---

## Step 10 — Update `.env` and `requirements.txt`

### `backend/agents_augmented/requirements.txt`

Replace `google-generativeai` with `google-genai`:

```
google-genai>=0.8.0        # was: google-generativeai>=0.8.0
anthropic>=0.25.0
python-dotenv>=1.0.0
pytest>=7.0.0
```

### `.env` (project root)

All required values are already present. Only `LLM_MODEL` needs updating from `gemini-2.5-flash` to `gemini-2.5-flash-lite` (spec default):

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash-lite   # updated from gemini-2.5-flash
GOOGLE_API_KEY=<already set>
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=4096
PIPELINE_MODE=augmented
MAX_TOOL_CALLS=20
MAX_ITERATIONS=25
LLM_RATE_LIMIT_RPM=5
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-6
```

---

## Build Order Summary

Files marked **DONE** are already implemented and passing tests. Files marked **CHANGE** need modification per the spec update.

| Step | File (relative to project root) | Status | Depends On |
|------|----------------------------------|--------|-----------|
| 0 | `backend/agents_augmented/__init__.py` | DONE | — |
| 1 | `backend/agents_augmented/state.py` | DONE | — |
| 2 | `backend/agents_augmented/prompts.py` | DONE | — |
| 3 | `backend/agents_augmented/mock_tools.py` | DONE | — |
| 4 | `backend/agents_augmented/tool_registry.py` | **CHANGE** — rewrite `get_gemini_tool_schemas()` using `types.Tool`/`types.Schema`; remove `_sanitize_schema_for_gemini()` | — |
| 5 | `backend/agents_augmented/tool_executor.py` | DONE | Steps 3, 4 |
| 6 | `backend/agents_augmented/llm_client.py` | **CHANGE** — rewrite `GeminiClient` for `google-genai` stateless API; 2-retry MALFORMED + raise | Step 4 |
| 7 | `backend/agents_augmented/workflow.py` | DONE | Steps 1, 2, 4, 5, 6 |
| 8 | `backend/agents_augmented/run.py` | DONE | Step 7 |
| 9a | `backend/agents_augmented/tests/__init__.py` | DONE | — |
| 9b | `backend/agents_augmented/tests/test_tool_execution.py` | DONE | Step 5 |
| 9c | `backend/agents_augmented/tests/test_llm_response_parsing.py` | DONE | Step 7 |
| 9d | `backend/agents_augmented/tests/test_safety_limits.py` | DONE | Step 7 |
| 9e | `backend/agents_augmented/tests/test_malformed_call.py` | **CHANGE** — update genai stub to mock `google.genai`; update double-failure test to expect raise not empty | Step 6 |
| 9f | `backend/agents_augmented/tests/test_e2e.py` | DONE | Steps 7, `.env` |
| 10 | `backend/agents_augmented/requirements.txt` | **CHANGE** — swap `google-generativeai` → `google-genai` | — |
| 10 | `.env` (project root) | **CHANGE** — update `LLM_MODEL=gemini-2.5-flash-lite` | — |

**Execution order for outstanding changes**: Step 10 (requirements.txt) → Step 4 (tool_registry) → Step 6 (llm_client) → Step 9e (test_malformed_call) → run `pip install -r requirements.txt` → run full test suite.

---

## Key Constraints (from spec)

- No LangGraph, LangChain, or any agentic framework dependency (Decision 18); use `google-genai` SDK (`from google import genai`) — not the deprecated `google-generativeai` package
- Python never decides which tool to invoke — only the LLM does
- `validate_itinerary()` and `generate_timeline()` must be called before LLM produces final TripState
- Both `LLM_PROVIDER=gemini` and `LLM_PROVIDER=claude` must work
- Safety limits (`MAX_TOOL_CALLS`, `MAX_ITERATIONS`) are enforced by Python, not the LLM
- Rate limit (`LLM_RATE_LIMIT_RPM=5`) is enforced proactively inside `LLMClient.invoke()` via sliding-window tracker — no manual sleeps elsewhere
- No files outside `backend/agents_augmented/` are created or modified (except `.env`)
- LLM temperature = 0 for deterministic output (Decision 9)
- All `json.dumps()` calls on tool results or state use `default=str` to handle non-serializable planner objects
- Location names normalized to title case in `tool_executor.py` before any retrieval tool call (Pitfall 6)

---

## Tool Sources

Real tools already exist — do not recreate them. `mock_tools.py` provides the fallback data when they fail at runtime.

| Tool | Real module (primary) | Fallback |
|------|-----------------------|----------|
| `get_routes` | `backend/tools/route_tool.py` | `mock_tools.py` |
| `get_hotels` | `backend/tools/hotel_tool.py` | `mock_tools.py` |
| `get_activities` | `backend/tools/activity_tool.py` | `mock_tools.py` |
| `get_transport_options` | `backend/tools/transport_tool.py` | `mock_tools.py` |
| `get_restaurants` | `backend/tools/restaurant_tool.py` | `mock_tools.py` |
| `get_waypoints` | `backend/tools/waypoint_tool.py` | `mock_tools.py` |
| `generate_candidates` | `backend/planner/candidate_generator.py` | `mock_tools.py` |
| `score_itinerary` | `backend/planner/scorer.py` | `mock_tools.py` |
| `validate_itinerary` | `backend/planner/validator.py` | `mock_tools.py` |
| `generate_timeline` | `backend/planner/timeline_generator.py` | `mock_tools.py` |
| `replan_itinerary` | `backend/planner/replanner.py` | `mock_tools.py` |

Retrieval tools require Neo4j. All other tools are pure Python and always succeed.

---

## Common Pitfalls (from spec — mapped to implementation)

1. **JSON parsing** (Decision 6): `_parse_final_answer()` must handle three formats: raw JSON, ` ```json ... ``` `, bare ` ``` ... ``` `. Strip fences before `json.loads()`. Already implemented in `workflow.py`.

2. **Rate limits** (Decision 10): `LLMClient.invoke()` enforces `LLM_RATE_LIMIT_RPM=5` automatically via a sliding-window timestamp tracker in the base class. No manual `time.sleep()` calls needed in `run.py` or `workflow.py`. If changing providers or models, update `LLM_RATE_LIMIT_RPM` in `.env` to match the actual quota.

3. **`MALFORMED_FUNCTION_CALL`** (Decision 20): `GeminiClient.invoke()` retries up to **2 times**; on persistent failure it **raises** (does not swallow the error). The primary prevention is strongly-typed `types.Tool`/`types.Schema` in `get_gemini_tool_schemas()` — the new `google-genai` SDK handles schema validation at the type level, replacing the old `_sanitize_schema_for_gemini()` dict-patching approach.

4. **State initialization** (Decision 1–5): Every TripState field must be present with an empty default from `init_state()`. The LLM's final JSON is merged ON TOP of `init_state()` — never replace the entire state dict.

5. **Import cycles**: All real tool imports are at the top of `tool_executor.py`. If a circular import arises, move the import inside the function body rather than at module level.

6. **Non-serializable objects**: Planner functions may return dataclass instances. Use `default=str` in all `json.dumps()` calls. Never pass the raw `trip_graph` object or dataclass instances in LLM prompt text.

7. **Location name casing**: The LLM may return names in any casing ("rishikesh", "GURUGRAM", "riShikEsh"). Neo4j matches and mock comparisons are case-sensitive. Two-layer defence:
   - `SYSTEM_PROMPT` instructs the LLM to use title case (already done in `prompts.py`).
   - `tool_executor.py` applies `_normalize_location()` (`.strip().title()`) to every `origin` / `destination` argument before forwarding to any retrieval tool. This is the safety net that catches whatever the LLM sends.
   - For Neo4j Cypher queries inside real tools, use `toLower(n.name) = toLower($name)` rather than exact equality.

---

## Acceptance Checklist

- [ ] `PYTHONPATH=. python backend/agents_augmented/run.py` runs end-to-end without error
- [ ] `run_workflow()` returns a `TripState` with all 24 keys present
- [ ] `run_replan_workflow()` returns updated state with `replanned_itinerary` set
- [ ] The LLM calls tools autonomously — no hardcoded tool invocation sequence in Python
- [ ] `MAX_TOOL_CALLS` and `MAX_ITERATIONS` terminate the loop when exceeded
- [ ] `LLM_RATE_LIMIT_RPM=5` is enforced inside `LLMClient.invoke()` — no API call exceeds 5/min
- [ ] Both `LLM_PROVIDER=gemini` and `LLM_PROVIDER=claude` produce valid output
- [ ] `grep -r "langchain\|langgraph" backend/agents_augmented/` returns no matches
- [ ] Tests 9a–9e pass without any external dependencies (no API key, no Neo4j)
- [ ] Test 9a also passes with Neo4j down (mock fallback active)
- [ ] Test 9e (MALFORMED_FUNCTION_CALL) passes using a fully mocked `google-genai` stub; persistent MALFORMED raises, not returns empty string
- [ ] Test 9f (e2e) is skipped by default; runs only when `RUN_E2E=true` is set
