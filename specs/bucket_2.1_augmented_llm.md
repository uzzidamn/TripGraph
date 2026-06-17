# Bucket 2.1: Tool-Augmented LLM

## Goal

Implement a single LLM that can autonomously use TripGraph tools to satisfy a travel planning request.

This bucket is intentionally simpler than Bucket 2 (Agentic LangGraph Architecture).

The objective is to establish a baseline implementation using a single LLM with tool-calling capabilities before introducing multi-agent orchestration.

---

# Architecture

```text
User Chat
    │
    ▼
Tool-Augmented LLM
    │
    ├── get_routes()
    ├── get_hotels()
    ├── get_activities()
    ├── get_transport_options()
    ├── get_restaurants()
    ├── get_waypoints()
    ├── generate_candidates()
    ├── score_itinerary()
    ├── validate_itinerary()
    ├── generate_timeline()
    └── replan_itinerary()
    │
    ▼
TripState
```

The LLM is responsible for:

* Determining which tool to call
* Determining when to call a tool
* Constructing tool arguments
* Gathering information iteratively
* Deciding when sufficient information exists
* Producing the final TripState

Python is responsible only for:

* Executing tools
* Maintaining conversation state
* Managing the execution loop
* Enforcing safety limits

---

# Execution Model

The system follows a ReAct-style execution loop.

```text
Thought
   ↓
Tool Call
   ↓
Observation
   ↓
Thought
   ↓
Tool Call
   ↓
Observation
   ↓
Final Answer
```

The LLM repeatedly reasons over accumulated context and tool outputs until it determines that planning is complete.

---

# Public API

These interfaces must remain compatible with Bucket 2.

```python
def run_workflow(chat_messages: list[str]) -> TripState

def run_replan_workflow(
    state: TripState,
    delay_event: dict
) -> TripState
```

---

# Tool Registry

The following functions are exposed to the LLM as callable tools.

## Travel Retrieval Tools

```python
get_routes
get_hotels
get_activities
get_transport_options
get_restaurants
get_waypoints
```

## Planning Tools

```python
generate_candidates
score_itinerary
validate_itinerary
generate_timeline
```

## Replanning Tools

```python
replan_itinerary
```

### Tool Sources and Fallback Strategy

All 11 tools are already implemented in the codebase. `tool_executor.py` tries real tools first and falls back to mocks when Neo4j is unavailable:

| Tool | Real module | Fallback |
|------|-------------|----------|
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

The retrieval tools (`get_*`) require Neo4j running. When a real tool raises an exception (e.g. Neo4j is down), `execute_tool()` catches it and invokes the corresponding mock automatically — the LLM sees valid data either way and planning can proceed.

`mock_tools.py` must return structurally valid data that matches the real tools' output shapes so the planner functions (`generate_candidates`, `score_itinerary`, etc.) can operate on mock data without modification.

---

# Agent Loop

The LLM controls execution.

```python
while not finished:

    llm_response = llm.invoke()

    if llm_response["type"] == "tool_call":

        result = execute_tool(
            llm_response["tool_name"],
            llm_response["arguments"]
        )

        llm.add_tool_result(
            llm_response["tool_call_id"],
            llm_response["tool_name"],
            result
        )

        continue

    if llm_response["type"] == "final_answer":

        return trip_state
```

Python must never decide which tool to invoke next.

All orchestration decisions belong to the LLM.

---

# LLM Responsibilities

The LLM owns:

## Constraint Extraction

Extract travel constraints directly from user messages.

Examples:

* Budget
* Destination
* Duration
* Group size
* Hotel preferences
* Activities
* Transport preferences
* Risk tolerance

---

## Tool Selection

Determine which tool should be called based on current context.

---

## Data Gathering

Iteratively gather required planning data using available tools.

---

## Planning

Construct itinerary candidates using retrieved information.

---

## Validation

Validate generated itineraries before completion.

The LLM must call:

```python
validate_itinerary()
```

before producing a final TripState.

---

## Timeline Generation

The LLM must call:

```python
generate_timeline()
```

before producing a final TripState.

---

## Explanation Generation

Generate a natural language explanation describing:

* Why the itinerary was selected
* Trade-offs considered
* Budget allocation
* Activity choices
* Route selection

---

# System Prompt

The LLM should receive the following system prompt:

```text
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
```

---

# State Management

The system maintains a message history.

```python
messages = [
    SystemMessage(...),
    UserMessage(...),

    ToolCall(...),
    ToolResult(...),

    ToolCall(...),
    ToolResult(...)
]
```

All reasoning occurs from accumulated conversation history.

No workflow graph or state machine should exist.

---

# Completion Conditions

The LLM may terminate only when all of the following conditions are satisfied:

```python
selected_itinerary is not None
```

```python
validation_report exists
```

```python
timeline exists
```

```python
cost_breakdown exists
```

```python
explanation exists
```

If any condition is missing, the LLM must continue gathering information.

---

# Safety Limits

Three limits must be enforced. Define them in `.env`:

```env
LLM_RATE_LIMIT_RPM=5
MAX_TOOL_CALLS=20
MAX_ITERATIONS=25
```

### Rate Limit (`LLM_RATE_LIMIT_RPM`)

Enforced inside `LLMClient.invoke()` using a sliding-window tracker over the last 60 seconds. If 5 or more calls have been made in the current window, `invoke()` sleeps until the oldest call expires before proceeding. The limit is never breached — execution slows rather than fails.

### Iteration and Tool-Call Limits (`MAX_TOOL_CALLS`, `MAX_ITERATIONS`)

Enforced **reactively** in the agent loop. If either counter is exceeded:

```python
TripState.conflict_report = {
    "error": "execution_limit_exceeded"
}
```

Execution must terminate immediately.

---

# Replanning

Replanning uses the same execution loop.

Additional context supplied to the model:

```python
{
    "existing_trip_state": state,
    "delay_event": delay_event
}
```

The model may invoke:

```python
replan_itinerary()
```

The resulting output must populate:

```python
replanned_itinerary
replanning_explanation
```

---

# LLM Configuration

Create a provider-agnostic LLM client.

## Environment Variables

The `.env` lives at the project root (`TripGraph/`). Required and optional variables:

```env
# Provider selection
LLM_PROVIDER=gemini          # gemini | claude

# Model name (used by both providers; override per-provider below if needed)
LLM_MODEL=gemini-2.5-flash-lite

# Gemini
GOOGLE_API_KEY=<from aistudio.google.com/apikey>

# Claude (optional — only needed when LLM_PROVIDER=claude)
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-6   # overrides LLM_MODEL for Claude if set

# Inference settings
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=4096

# Rate limiting (LLM calls per minute, across all providers)
LLM_RATE_LIMIT_RPM=5

# Agent safety limits
MAX_TOOL_CALLS=20
MAX_ITERATIONS=25
```

Note: `GOOGLE_API_KEY` (not `GEMINI_API_KEY`) is the variable name used in this project.

## llm_client.py Responsibilities

Implement a stateful `LLMClient` class. Each workflow run creates a new instance; the client owns conversation history internally so `workflow.py` stays provider-agnostic.

```python
class LLMClient:
    def add_user_message(self, content: str) -> None: ...
    def add_tool_result(self, tool_call_id: str, tool_name: str, result: dict) -> None: ...
    def invoke(self) -> dict: ...

def create_llm_client(system_prompt: str) -> LLMClient:
    """Factory: reads LLM_PROVIDER and returns GeminiClient or ClaudeClient."""
```

`LLMClient` owns rate limiting. Before every `invoke()` call, the client checks a rolling 60-second call history and sleeps if 5 or more calls have already been made in that window. `LLM_RATE_LIMIT_RPM` (default `5`) controls the cap. This logic lives inside `invoke()` so it is enforced automatically for both providers.

`GeminiClient` must use the `google-genai` SDK. This requires `google-genai>=0.8.0` in `requirements.txt` 

#### Correct initialization

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
```

#### Tool schema format

`get_gemini_tool_schemas()` must return a list of `types.Tool` objects

```python
from google.genai import types

[
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        k: types.Schema(type=v["type"].upper(), description=v.get("description", ""))
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

Note: `types.Schema` requires `type` values in uppercase (`"OBJECT"`, `"STRING"`, `"ARRAY"`, `"INTEGER"`)
#### Message history (stateless API)

`GeminiClient` must maintain a `contents: list` internally and pass the full history on every call:

```python
response = client.models.generate_content(
    model=model_name,
    contents=self._contents,          # full conversation history
    config=types.GenerateContentConfig(
        tools=self._tools,
        system_instruction=system_prompt,
        temperature=temperature,
    ),
)
# Append the model's response turn to maintain history
self._contents.append(response.candidates[0].content)
```

#### System instruction placement

The system instruction is set in `GenerateContentConfig.system_instruction`, not in a model constructor. 

#### Tool result format

Use `types.Part` and `types.FunctionResponse` from `google.genai.types`
```python
from google.genai import types
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

`GeminiClient.invoke()` must check for `finish_reason == "MALFORMED_FUNCTION_CALL"` and retry up to 2 times before raising (see Decision 20).

`invoke()` returns one of two normalized shapes:

```python
# LLM wants to call a tool
{"type": "tool_call", "tool_call_id": "...", "tool_name": "...", "arguments": {...}}

# LLM is done — content is a JSON string of the complete TripState
{"type": "final_answer", "content": "{ ... }"}
```

The `content` in `final_answer` is the raw text from the LLM. `workflow.py` parses it with `_parse_final_answer()`, stripping any markdown fences before `json.loads()`.

---

# run.py

A simple executable script to manually test the Tool-Augmented LLM without requiring API endpoints or external services.

Run from the project root:

```bash
PYTHONPATH=. python backend/agents_augmented/run.py
```

Purpose:

- Load `.env` from project root
- Initialize the selected LLM provider via `create_llm_client()`
- Execute `run_workflow()` with a sample planning request
- Execute `run_replan_workflow()` with a sample delay event
- Print the resulting TripState and replanned state

---

# Deliverables

```text
backend/
└── agents_augmented/
    ├── __init__.py
    ├── state.py
    ├── prompts.py
    ├── mock_tools.py
    ├── tool_registry.py
    ├── tool_executor.py
    ├── llm_client.py
    ├── workflow.py
    ├── run.py
    └── tests/
        ├── __init__.py
        ├── test_tool_execution.py
        ├── test_llm_response_parsing.py
        ├── test_safety_limits.py
        └── test_e2e.py
```

No workflow-step modules should exist.

Examples:

```text
parse_constraints.py
retrieve_data.py
plan_itinerary.py
validate_constraints.py
explain_plan.py
```

These belong to workflow-based architectures and are intentionally excluded from Bucket 2.1.

---
## Decisions & Defaults (Pre-Made)

| # | Decision | Value |
|---|----------|-------|
| 1 | Default group_size if not extracted | `4` |
| 2 | Default hotel_tier if not extracted | `"comfort"` |
| 3 | Default risk_tolerance if not extracted | `"medium"` |
| 4 | Default origin if not extracted | `"Gurugram"` |
| 5 | Default trip_duration if not extracted | `"2D1N"` |
| 6 | JSON parsing from LLM responses | Always handle: raw JSON, ` ```json ``` ` wrapped, and ` ``` ``` ` wrapped responses. Strip markdown code fences before parsing. |
| 7 | What if LLM returns invalid JSON | Retry once. If still invalid, log error and use empty defaults. Do NOT crash. |
| 8 | What if LLM call fails (network/rate limit) | Catch exception, log with `print(f"[ERROR] LLM call failed: {e}")`, and raise to propagate to the API layer. |
| 9 | LLM temperature | `0` — deterministic output for reproducibility |
| 10 | Rate limit handling | `LLMClient` must enforce `LLM_RATE_LIMIT_RPM=5` (≤ 5 LLM calls per minute) using a sliding-window token-bucket or call-timestamp tracker. Before every `invoke()`, compute elapsed time since the oldest call in the current 60-second window; if the window is full (≥ 5 calls), sleep until the oldest call falls outside the window. This applies to **all providers** (Gemini and Claude). |
| 11 | What does empty `must_include` mean | No activity constraints; accept all activities. |
| 12 | What does `avoid_night_driving: false` mean | Night driving is acceptable; do NOT penalize. |
| 13 | How many alternatives to return | Up to 3 (from lower-scored valid candidates + invalid candidates) |
| 14 | What if no valid candidates exist | Return the highest-scored invalid candidate as `selected_itinerary` with `validation_report.is_valid = False`. |
| 15 | Map points extraction | Extract lat/lng from: route origin, waypoints, destination city, hotel, each activity. Label format: `{"lat": float, "lng": float, "label": str, "type": str}` |
| 16 | `map_points` type values | `"origin"`, `"waypoint"`, `"destination"`, `"hotel"`, `"activity"` |
| 17 | Workflow export function names | `run_workflow(chat_messages)` and `run_replan_workflow(state, delay_event)` — these are the public API called by Bucket 3. |
| 18 | LLM provider packages | `google-genai` for direct Gemini calls (`from google import genai`).  API is incompatible with the `google-genai` SDK. `requirements.txt` must list `google-genai>=0.8.0`;. NO LangChain or LangGraph dependency. |
| 19 | Mock vs real tool imports | Use try/except: try real imports first, fall back to mock if ImportError. This lets the bucket run independently. |
| 20 | What if Gemini returns `MALFORMED_FUNCTION_CALL` | Retry `invoke()` up to 2 times with the same message history. If still `MALFORMED_FUNCTION_CALL` after all retries, raise as an LLM error (handled by Decision 8). Do NOT silently skip or return a partial result. |

---

# Acceptance Criteria

The bucket is considered complete only if all criteria below are satisfied.


## Functional Requirements

* [ ] `run_workflow()` returns a valid TripState
* [ ] `run_replan_workflow()` returns a valid updated TripState
* [ ] The LLM can autonomously invoke tools
* [ ] Tool calls are executed correctly
* [ ] Tool outputs are returned to the LLM
* [ ] The LLM can call multiple tools in sequence
* [ ] The LLM can terminate execution with a valid TripState
* [ ] Replanning works using the same execution loop
* [ ] run.py executes successfully from command line.

## Architecture Requirements

* [ ] No LangGraph dependency
* [ ] No LangChain dependency
* [ ] No workflow graph implementation
* [ ] No multi-agent implementation
* [ ] No fixed pipeline orchestration
* [ ] All orchestration decisions are made by the LLM

## Tool Requirements

* [ ] All 11 tools are registered in `tool_registry.py`
* [ ] `tool_executor.py` tries real tools first, falls back to `mock_tools.py` on exception
* [ ] Mock tools in `mock_tools.py` return data with the same structure as real tools
* [ ] Tool schemas are exposed to the LLM
* [ ] Tool execution is handled through `tool_executor.py`
* [ ] System runs end-to-end with Neo4j down (mock fallback active)

## State Requirements

* [ ] TripState matches Bucket 2 schema exactly
* [ ] Message history is maintained across iterations
* [ ] Tool results are preserved in conversation history

## Safety Requirements

* [ ] MAX_TOOL_CALLS is enforced
* [ ] MAX_ITERATIONS is enforced
* [ ] Execution terminates safely when limits are exceeded
* [ ] LLM calls never exceed `LLM_RATE_LIMIT_RPM` (5) per minute — enforced inside `LLMClient.invoke()`

## Provider Requirements

* [ ] Gemini integration works using `google-genai` SDK (`from google import genai`)
* [ ] Claude integration works
* [ ] Provider selection is controlled through `.env`
* [ ] Both providers expose the same normalized interface

## Testing Requirements

* [ ] Unit tests exist for tool execution
* [ ] Unit tests exist for LLM response parsing
* [ ] Unit tests exist for safety limit enforcement
* [ ] End-to-end planning test passes
* [ ] End-to-end replanning test passes

## Success Condition

A user can provide a travel-planning request and the system autonomously:

1. Determines what information is required.
2. Calls the appropriate tools.
3. Builds and validates itinerary candidates.
4. Generates a timeline.
5. Produces a complete TripState.

Without any hardcoded workflow steps.

## Common Pitfalls

1. **JSON parsing**: Gemini sometimes wraps JSON in markdown code blocks. Always handle both raw JSON and ` ```json ``` ` wrapped responses. Strip fences inside `_parse_final_answer()` in `workflow.py` before calling `json.loads()`.
2. **Rate limits**: `LLMClient.invoke()` enforces `LLM_RATE_LIMIT_RPM=5` automatically via a sliding-window tracker. No manual `time.sleep()` calls are needed. If you change providers or models, ensure `LLM_RATE_LIMIT_RPM` in `.env` reflects the actual quota.
3. **State initialization**: Every field in TripState must have a value (even if empty list/dict/None). Missing keys will cause Bucket 3's Pydantic models to fail validation.
4. **Import cycles**: Tool and planner imports are at the top of `tool_executor.py` and `tool_registry.py`. If circular import issues arise, use late imports inside the function body.
5. **Non-serializable objects**: The `trip_graph` field in candidates contains dataclass instances. Use `default=str` in any `json.dumps()` call. LLM prompts should NOT include the raw `trip_graph` object.
6. **Location name casing**: The LLM may return location names in any casing ("rishikesh", "GURUGRAM", "riShikEsh"). Neo4j string property matches and mock data comparisons are case-sensitive by default. Always normalize location strings with `str.strip().title()` **before** passing them to any tool function or planner. Normalization must happen in `workflow.py` when extracting constraints from the LLM's response, and defensively inside `tool_executor.py` via a `_normalize_location()` helper before forwarding arguments to tool functions. For Neo4j Cypher queries, use `toLower(n.name) = toLower($name)` rather than exact equality.
