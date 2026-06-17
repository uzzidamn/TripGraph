# Bucket 2: Agentic AI Pipeline (LangGraph) — LLM-Ready Spec

> **Generated for**: Distributed LLM execution (Claude / Gemini session)
> **Priority**: P1 — Can start immediately with mock tools
> **Reference**: This spec is self-contained. You may also read `specs/MASTER_SPEC.md` for full project context.

---

## Section A — Project Context

**TripGraph AI** is a GenAI-agentic group travel planner that converts WhatsApp-style group chat into structured, constraint-aware itineraries. It uses a Neo4j knowledge graph, a LangGraph agentic pipeline, a deterministic Python planning engine, and a React frontend.

**Your role (Bucket 2):** Build the **LangGraph-based agentic AI pipeline** that orchestrates the entire planning workflow. You implement 6 agent nodes, connect them in a state graph, design prompt templates, and create a swappable LLM client. The pipeline receives raw chat messages and produces a complete `TripState` containing extracted constraints, itineraries, timelines, map points, cost breakdowns, and explanations.

**Key Principle:** The LLM handles **language** (extraction, explanation). Python handles **math** (cost, timing, validation). The planner handles **optimization** (graph-based itinerary construction). Your agents coordinate these — they do NOT calculate costs or invent data.

---

## Section B — 🔒 Frozen Interface Contracts

### B.1 TripState TypedDict

This is the shared state object passed through all LangGraph nodes. Every field must be initialized in `run_workflow()`.

```python
from typing import TypedDict, List, Dict, Any, Optional

class TripState(TypedDict):
    # Input
    raw_chat: List[str]

    # Constraint extraction (Chat Parser)
    extracted_constraints: Dict[str, Any]
    missing_fields: List[str]
    assumptions: Dict[str, str]

    # Constraint validation
    conflict_report: Dict[str, Any]
    is_ready_to_plan: bool

    # Data retrieval
    route_candidates: List[Dict[str, Any]]
    hotel_candidates: List[Dict[str, Any]]
    transport_candidates: List[Dict[str, Any]]
    activity_candidates: List[Dict[str, Any]]
    food_candidates: List[Dict[str, Any]]
    waypoint_candidates: List[Dict[str, Any]]

    # Planning
    itinerary_candidates: List[Dict[str, Any]]
    selected_itinerary: Optional[Dict[str, Any]]
    alternative_itineraries: List[Dict[str, Any]]
    validation_report: Dict[str, Any]
    score_breakdown: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    map_points: List[Dict[str, Any]]
    cost_breakdown: Dict[str, Any]

    # Explanation
    explanation: str

    # Observability
    trace_id: Optional[str]   # LangSmith run ID, populated by workflow.py if tracing is enabled

    # Replanning
    delay_event: Optional[Dict[str, Any]]
    replanned_itinerary: Optional[Dict[str, Any]]
    replanning_explanation: Optional[str]
```

### B.2 Tool Function Signatures & Import Paths

These tools are implemented by Bucket 5. During development, use mock versions (Section B.4).

```python
# Import paths (frozen):
from backend.tools.route_tool import get_routes
from backend.tools.hotel_tool import get_hotels
from backend.tools.activity_tool import get_activities
from backend.tools.transport_tool import get_transport_options
from backend.tools.restaurant_tool import get_restaurants
from backend.tools.waypoint_tool import get_waypoints
```

**Function signatures and return dict key shapes:**

#### `get_routes(origin: str, destination_type: str | None = None) -> list[dict]`
Each dict contains:
```
route_id: str                    # e.g., "gurugram_rishikesh_2d1n"
origin: str                      # not in Neo4j node — added by query via relationship
destination: str                 # not in Neo4j node — added by query via relationship
destination_type: str            # e.g., "mountains", "heritage"
distance_km: int
base_drive_minutes: int
risk_level: str                  # "low" | "medium" | "high"
scenic_score: int                # 1-10
dest_lat: float                  # destination coordinates
dest_lng: float
```

#### `get_hotels(destination: str, tier: str | None = None) -> list[dict]`
Each dict contains:
```
hotel_id: str
name: str
tier: str                        # "budget" | "comfort" | "expedition"
price_per_night: float           # INR, per room
rooms_required: int
checkin_time: str                # "HH:MM"
checkout_time: str
comfort_score: int               # 1-10
lat: float
lng: float
amenities: list[str]
tags: list[str]
```

#### `get_activities(destination: str, tags: list[str] | None = None) -> list[dict]`
Each dict contains:
```
activity_id: str
name: str
category: str                    # "adventure" | "cultural" | "food" | "nature" | etc.
duration_minutes: int
cost_per_person: float           # INR
available_slots: list[str]       # ["09:00", "12:00"]
risk_level: str
tags: list[str]
lat: float
lng: float
```

#### `get_transport_options(route_id: str, modes: list[str] | None = None) -> list[dict]`
Each dict contains:
```
transport_id: str
mode: str                        # "cab_with_driver" | "self_drive" | "bus" | etc.
tier: str
cost_total: float                # INR, total for vehicle
capacity: int
base_duration_minutes: int
night_driving_allowed: bool
comfort_score: int
fatigue_score: int
tags: list[str]
```

#### `get_restaurants(destination: str, route_id: str | None = None) -> list[dict]`
Each dict contains:
```
restaurant_id: str
name: str
meal_types: list[str]            # ["breakfast", "lunch", "dinner"]
avg_cost_per_person: float       # INR
avg_duration_minutes: int
tags: list[str]
lat: float
lng: float
location_type: str               # "destination" or "highway" (added by query when route_id provided)
```

#### `get_waypoints(route_id: str) -> list[dict]`
Each dict contains:
```
waypoint_id: str
name: str
type: str                        # "breakfast_stop" | "fuel_stop" | "viewpoint"
km_from_origin: int
order: int
lat: float
lng: float
typical_stop_minutes: int
```

### B.3 Planner Function Signatures & Import Paths

```python
from backend.planner.candidate_generator import generate_candidates
from backend.planner.scorer import score_itinerary
from backend.planner.validator import validate_itinerary
from backend.planner.timeline_generator import generate_timeline
from backend.planner.replanner import replan_itinerary
```

**Signatures:**
```python
def generate_candidates(constraints: dict, data: dict) -> list[dict]:
    """
    data keys: "routes", "hotels", "transport", "activities", "food", "waypoints"
    Returns list of candidate dicts, each with: route, transport, hotel,
    activities, restaurants, waypoints, destination, trip_graph,
    cost_breakdown, total_cost_per_person
    """

def score_itinerary(itinerary: dict, constraints: dict) -> dict:
    """Returns: preference_match, budget_efficiency, comfort, scenic,
    fatigue, risk, night_driving_penalty, final_score"""

def validate_itinerary(itinerary: dict, constraints: dict) -> dict:
    """Returns: is_valid, hard_constraint_violations, soft_constraint_warnings,
    budget_used, budget_limit, must_include_satisfied"""

def generate_timeline(itinerary: dict) -> list[dict]:
    """Returns list of: {day, start_time, end_time, title, type, cost?}"""

def replan_itinerary(itinerary: dict, delay_event: dict, constraints: dict) -> dict:
    """Returns: updated_itinerary, changes, delay_absorbed, delay_remaining"""
```

### B.4 Mock Data Blocks

Use these mock implementations while Bucket 5 tools are not available. Place these in each tool file or in a unified mock module.

```python
# === MOCK: get_routes ===
MOCK_ROUTES = [
    {
        "route_id": "gurugram_rishikesh_2d1n",
        "origin": "Gurugram",
        "destination": "Rishikesh",
        "destination_type": "mountains",
        "distance_km": 260,
        "base_drive_minutes": 390,
        "risk_level": "medium",
        "scenic_score": 7,
        "dest_lat": 30.0869,
        "dest_lng": 78.2676,
    },
    {
        "route_id": "gurugram_jaipur_2d1n",
        "origin": "Gurugram",
        "destination": "Jaipur",
        "destination_type": "heritage",
        "distance_km": 240,
        "base_drive_minutes": 300,
        "risk_level": "low",
        "scenic_score": 5,
        "dest_lat": 26.9124,
        "dest_lng": 75.7873,
    },
]

# === MOCK: get_hotels ===
MOCK_HOTELS = [
    {
        "hotel_id": "rishikesh_comfort_01",
        "name": "Riverside Comfort Stay",
        "tier": "comfort",
        "price_per_night": 4200,
        "rooms_required": 1,
        "checkin_time": "14:00",
        "checkout_time": "11:00",
        "comfort_score": 8,
        "lat": 30.0869,
        "lng": 78.2676,
        "amenities": ["wifi", "parking", "restaurant", "river_view"],
        "tags": ["riverside", "central"],
        "destination": "Rishikesh",
    },
]

# === MOCK: get_activities ===
MOCK_ACTIVITIES = [
    {
        "activity_id": "rafting_rishikesh_01",
        "name": "White Water Rafting (16 km)",
        "category": "adventure",
        "duration_minutes": 180,
        "cost_per_person": 1800,
        "available_slots": ["09:00", "12:00"],
        "risk_level": "medium",
        "tags": ["adventure", "rafting", "water", "outdoor"],
        "lat": 30.1159,
        "lng": 78.3127,
        "destination": "Rishikesh",
    },
    {
        "activity_id": "aarti_rishikesh_01",
        "name": "Ganga Aarti at Triveni Ghat",
        "category": "spiritual",
        "duration_minutes": 60,
        "cost_per_person": 0,
        "available_slots": ["18:30"],
        "risk_level": "low",
        "tags": ["spiritual", "cultural", "evening", "free"],
        "lat": 30.1050,
        "lng": 78.2950,
        "destination": "Rishikesh",
    },
]

# === MOCK: get_transport_options ===
MOCK_TRANSPORT = [
    {
        "transport_id": "cab_rishikesh_comfort",
        "mode": "cab_with_driver",
        "tier": "comfort",
        "cost_total": 9500,
        "capacity": 4,
        "base_duration_minutes": 390,
        "night_driving_allowed": False,
        "comfort_score": 8,
        "fatigue_score": 3,
        "tags": ["ac", "sedan", "professional_driver"],
        "route_id": "gurugram_rishikesh_2d1n",
    },
]

# === MOCK: get_restaurants ===
MOCK_RESTAURANTS = [
    {
        "restaurant_id": "rishikesh_cafe_01",
        "name": "Little Buddha Cafe",
        "meal_types": ["lunch", "dinner"],
        "avg_cost_per_person": 600,
        "avg_duration_minutes": 75,
        "tags": ["cafe", "river_view"],
        "lat": 30.1256,
        "lng": 78.3152,
        "destination": "Rishikesh",
    },
]

# === MOCK: get_waypoints ===
MOCK_WAYPOINTS = [
    {
        "waypoint_id": "murthal_stop",
        "name": "Murthal Dhaba Belt",
        "type": "breakfast_stop",
        "km_from_origin": 35,
        "order": 1,
        "lat": 29.0281,
        "lng": 77.0474,
        "typical_stop_minutes": 30,
        "route_id": "gurugram_rishikesh_2d1n",
    },
]
```

### B.5 Extracted Constraints Dict Shape

The Chat Parser agent must output a dict with these exact keys:
```python
{
    "origin": str | None,                    # "Gurugram"
    "destination": str | None,               # specific dest or None
    "destination_type": str | None,          # "mountains" | "heritage" | "nature"
    "budget_per_person": int | None,         # INR
    "dates": str | None,                     # "weekend", "June 20-22"
    "trip_duration": str | None,             # "2D1N", "weekend"
    "transport_preference": list[str],       # ["cab_with_driver"]
    "avoid_night_driving": bool,             # True/False
    "must_include": list[str],               # ["rafting", "cafes"]
    "return_deadline": str | None,           # "Monday morning"
    "hotel_tier": str | None,                # "budget"|"comfort"|"expedition"
    "risk_tolerance": str | None,            # "low"|"medium"|"high"
    "group_size": int | None,                # 4
    "special_requirements": list[str],       # any extras
}
```

### B.6 Environment Variables

```env
# ── LLM Provider ─────────────────────────────────────────────────────
LLM_PROVIDER=gemini          # gemini | claude | openai | ollama

# Gemini
LLM_MODEL=gemini-2.5-flash-lite-preview-06-17
GOOGLE_API_KEY=your_gemini_api_key_here

# Claude (set LLM_PROVIDER=claude to use)
# LLM_MODEL=claude-sonnet-4-5
ANTHROPIC_API_KEY=your_anthropic_api_key_here

LLM_TEMPERATURE=0
LLM_MAX_TOKENS=4096          # Required for Claude; ignored by Gemini
LLM_RATE_LIMIT_RPM=15        # Max LLM calls per minute across all nodes (enforced in llm_client.py)

# ── Workflow Engine ───────────────────────────────────────────────────
PIPELINE_MODE=langgraph    # langgraph | augmented_llm
                             # langgraph  → Bucket 2 (LangGraph multi-node pipeline)
                             # augmented_llm → Bucket 2.1 (single Tool-Augmented LLM)

# ── Data Layer ─────────────────────────────────────────────────────
NEO4J_ENABLED=false          # true | false
                             # false → all tools use mock data from Section B.4
                             # true  → tools attempt real Neo4j queries; fall back to mock on error
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# ── Observability ─────────────────────────────────────────────────────
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=tripgraph-bucket2
```

When `LANGCHAIN_TRACING_V2=true`, every LangChain LLM call is automatically traced to LangSmith with no code changes required. The project name groups all runs under a single LangSmith project for comparison.

---

## Section C — Decisions & Defaults (Pre-Made)

| # | Decision | Value |
|---|----------|-------|
| 1 | Default group_size if not extracted | `4` |
| 2 | Default hotel_tier if not extracted | `"comfort"` |
| 3 | Default risk_tolerance if not extracted | `"medium"` |
| 4 | Default origin if not extracted | `"Gurugram"` |
| 5 | Default trip_duration if not extracted | `"2D1N"` |
| 6 | JSON parsing from LLM responses | Always handle: raw JSON, ` ```json ``` ` wrapped, and ` ``` ``` ` wrapped responses. Strip markdown code fences before parsing. |
| 7 | What if LLM returns invalid JSON | Retry once. If still invalid, log error and use empty defaults. Do NOT crash. |
| 8 | What if LLM call fails (network/rate limit) | Catch exception, log with `print(f"❌ LLM call failed: {e}")`, and raise to propagate to the API layer. |
| 9 | LLM temperature | `0` — deterministic output for reproducibility |
| 10 | Rate limit handling | `llm_client.py` enforces `LLM_RATE_LIMIT_RPM=15` (default) using a sliding-window tracker. Before every `get_llm().invoke()` call, the client checks how many calls have been made in the last 60 seconds; if the count is ≥ `LLM_RATE_LIMIT_RPM`, it sleeps until the oldest call falls outside the window. This is proactive — the limit is never breached, execution slows instead. Applies to all providers (Gemini, Claude, OpenAI, Ollama). `llm.with_retry(stop_after_attempt=3)` is applied on top to handle transient API errors separately from rate limiting. |
| 11 | What does empty `must_include` mean | No activity constraints; accept all activities. |
| 12 | What does `avoid_night_driving: false` mean | Night driving is acceptable; do NOT penalize. |
| 13 | How many alternatives to return | Up to 3 (from lower-scored valid candidates + invalid candidates) |
| 14 | What if no valid candidates exist | Return the highest-scored invalid candidate as `selected_itinerary` with `validation_report.is_valid = False`. |
| 15 | Map points extraction | Extract lat/lng from: route origin, waypoints, destination city, hotel, each activity. Label format: `{"lat": float, "lng": float, "label": str, "type": str}` |
| 16 | `map_points` type values | `"origin"`, `"waypoint"`, `"destination"`, `"hotel"`, `"activity"` |
| 17 | Workflow export function names | `run_workflow(chat_messages)` and `run_replan_workflow(state, delay_event)` — these are the public API called by Bucket 3. |
| 18 | LLM provider packages | `google-genai` (Google's new SDK, replaces deprecated `google-generativeai`) + `langchain-google-genai>=2.0` (LangChain wrapper that uses `google-genai` internally) for Gemini. `langchain-anthropic` for Claude. `langchain-openai` for OpenAI. `langchain-ollama` for Ollama. Only install the provider you need. |
| 19 | Mock vs real tool imports | Use try/except: try real imports first, fall back to mock if ImportError. This lets the bucket run independently. |
| 20 | Constraint Validator: what fields are required to proceed | At minimum: `origin` AND (`budget_per_person` OR `trip_duration`) AND at least one preference (`destination_type`, `must_include`, or `destination`). |
| 21 | Location name normalization | Normalize all location strings extracted from the LLM (`origin`, `destination`, waypoint names) with `str.strip().title()` in `chat_parser_node` immediately after JSON parsing. E.g., `"gurugram"` → `"Gurugram"`, `"RISHIKESH"` → `"Rishikesh"`. Also normalize defensively in `data_retriever_node` before passing to any tool. |
| 22 | Enum field normalization | Normalize enum-like constraint fields to lowercase with `str.strip().lower()` in `constraint_validator_node`. Fields: `hotel_tier`, `risk_tolerance`, `destination_type`, items in `transport_preference`, items in `must_include`. E.g., `"Comfort"` → `"comfort"`, `"Medium Risk"` → `"medium risk"`. |
| 23 | `must_include` matching | Normalize each `must_include` item to lowercase. Match against activity `name` (lowercase) and `tags` (lowercase) using substring matching — any overlap is a match. E.g., `"rafting"` matches `name="White Water Rafting"` and `tags=["rafting", "adventure"]`. |
| 24 | `conflict_report` shape | `{"has_conflicts": bool, "blocking_conflicts": [{"type": str, "field": str, "description": str}], "warnings": [{"type": str, "field": str, "description": str, "suggestion": str}]}`. Blocking conflicts set `is_ready_to_plan=False`. Warnings alone do not block planning. |
| 25 | Destination vs destination_type conflict | If both `destination` and `destination_type` are specified and contradict (e.g., `destination="Jaipur"`, `destination_type="mountains"`), add a blocking conflict: `{"type": "destination_mismatch", "field": "destination_type", "description": "Jaipur is not a mountains destination"}`. |
| 26 | Budget conflict (post-planning) | If `validation_report.is_valid = False` due to budget violation, still return `selected_itinerary` (best invalid candidate) and add a warning to `conflict_report`: `{"type": "budget_exceeded", "field": "budget_per_person", "description": "...", "suggestion": "Increase budget or reduce group size"}`. Do NOT crash or return empty state. |
| 27 | must_include not satisfiable | If no activity matches a `must_include` item after data retrieval, add a warning to `conflict_report`: `{"type": "must_include_unavailable", "field": "must_include", "description": "No activity found matching '{item}' at {destination}", "suggestion": "Consider removing this requirement or choosing a different destination"}`. Planning continues. |
| 28 | LangSmith tracing activation | Tracing is **zero-config** — LangChain automatically sends traces when `LANGCHAIN_TRACING_V2=true` is set in `.env`. No callback or wrapper code needed in nodes. Each node must pass `run_name="<node_name>"` to `get_llm()` so spans are labeled in the LangSmith UI. |
| 29 | What is traced per run | Every `get_llm().invoke()` call produces a span: inputs (prompt), outputs (raw LLM response), token counts, latency, model name, and `run_name` label. The full chain of spans for one `run_workflow()` call is grouped as one LangSmith trace. |
| 30 | `trace_id` in TripState | After `run_workflow()` completes, call `get_trace_url()` from `llm_client.py` and store the result in `state["trace_id"]`. If tracing is disabled, store `None`. Bucket 3 may surface this URL in the API response for debugging. |
| 31 | LangSmith package | Add `langsmith` to project dependencies. It is a lightweight SDK; it does not replace LangChain. Install: `pip install langsmith`. |
| 32 | Claude-specific input pattern: system message | `ChatAnthropic` requires the system prompt to be passed as a `SystemMessage` at index 0 of the messages list, NOT as a constructor argument. LangChain's `ChatPromptTemplate` handles this correctly when you use `SystemMessagePromptTemplate` — no special handling needed in nodes as long as prompts use standard LangChain message types. |
| 33 | Claude-specific input pattern: max tokens | Claude requires `max_tokens` to be set explicitly — it has no default. Set `LLM_MAX_TOKENS=4096` in `.env`. `get_llm()` reads this and passes it only when provider is `claude`. Gemini and others ignore it (they use their own defaults). |
| 34 | Claude-specific input pattern: tool calling | Claude uses the same LangChain `.bind_tools()` interface as Gemini. No node-level code changes needed. However, Claude does not support `anyOf` in tool input schemas — use explicit `type` fields only (e.g., `"type": "string"` not `"type": ["string", "null"]`). Use `Optional` with a default of `None` in Python and flatten to `"type": "string"` with a note in the description instead. |
| 35 | Workflow engine routing | `run_workflow()` and `run_replan_workflow()` read `PIPELINE_MODE` from `.env` and delegate to the appropriate backend. `langgraph` delegates to the LangGraph multi-node pipeline (Bucket 2). `augmented_llm` delegates to `backend.agents_augmented.workflow` (Bucket 2.1). The public function signatures are identical across both engines — the caller (Bucket 3 API) never needs to change. |
| 36 | Tool mock vs real selection | When `NEO4J_ENABLED=false`, `data_retriever_node` imports mock functions directly from `backend.agents.nodes.mock_tools`. When `NEO4J_ENABLED=true`, it imports the real functions from `backend.tools.*` and wraps each call in try/except; on any exception it falls back to the corresponding mock. This keeps tool selection explicit and testable at the node level. |

---

## Section D — Step-by-Step Build Instructions

### Step 1: Create `backend/agents/__init__.py`
```python
# Agents package
```

### Step 2: Create `backend/agents/nodes/__init__.py`
```python
# Agent nodes package
```

### Step 3: Create `backend/agents/llm_client.py`

Swappable LLM factory. Reads `LLM_PROVIDER` and `LLM_MODEL` from environment.

```python
"""
Swappable LLM client. Change LLM_PROVIDER and LLM_MODEL in .env to switch models.
Supported providers: gemini, claude, openai, ollama
Tracing: set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY in .env to enable LangSmith.

Gemini SDK note:
  Uses `google-genai` (new SDK) via `langchain-google-genai>=2.0`.
  Do NOT install or import `google-generativeai` (deprecated).
  Install: pip install google-genai "langchain-google-genai>=2.0"
"""
import os
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()

# LangSmith tracing is activated automatically by LangChain when these env vars are set:
#   LANGCHAIN_TRACING_V2=true
#   LANGCHAIN_API_KEY=...
#   LANGCHAIN_PROJECT=tripgraph-bucket2
# No additional code is required — LangChain reads these at import time.

import time
from collections import deque
from threading import Lock

_rate_limit_rpm: int = int(os.getenv("LLM_RATE_LIMIT_RPM", "15"))
_call_timestamps: deque = deque()   # timestamps of recent LLM calls
_rate_lock: Lock = Lock()


def _wait_for_rate_limit() -> None:
    """Block until making an LLM call would not exceed LLM_RATE_LIMIT_RPM.
    Uses a sliding 60-second window. Thread-safe.
    """
    with _rate_lock:
        now = time.monotonic()
        # Drop timestamps older than 60 seconds
        while _call_timestamps and now - _call_timestamps[0] >= 60.0:
            _call_timestamps.popleft()

        if len(_call_timestamps) >= _rate_limit_rpm:
            # Sleep until the oldest call in the window expires
            sleep_for = 60.0 - (now - _call_timestamps[0])
            if sleep_for > 0:
                print(f"[RATE LIMIT] Sleeping {sleep_for:.1f}s to stay under {_rate_limit_rpm} RPM")
                time.sleep(sleep_for)
            # Re-purge after sleeping
            now = time.monotonic()
            while _call_timestamps and now - _call_timestamps[0] >= 60.0:
                _call_timestamps.popleft()

        _call_timestamps.append(time.monotonic())


def get_llm(run_name: str | None = None) -> BaseChatModel:
    """Create and return an LLM instance based on environment config.

    Enforces LLM_RATE_LIMIT_RPM before returning the LLM — call this
    immediately before every .invoke() call, not at module import time.

    Args:
        run_name: Optional label attached to this LLM call in LangSmith traces.
                  Use the node name, e.g. "chat_parser", "explainer".
    """
    _wait_for_rate_limit()
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite-preview-06-17")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0"))

    config = {}
    if run_name:
        config["run_name"] = run_name

    if provider == "gemini":
        # langchain-google-genai>=2.0 wraps google-genai (new SDK) internally.
        # Do NOT use langchain-google-genai<2.0 — it wraps the deprecated google-generativeai.
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            **config,
        )
    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic
        # Claude requires max_tokens to be set explicitly (no default).
        # Fall back to 4096 if not in .env.
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        return ChatAnthropic(
            model=model or "claude-sonnet-4-5",
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            **config,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature, **config)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature, **config)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: gemini, claude, openai, ollama")


def get_provider() -> str:
    """Return the active provider name. Used by nodes that need provider-specific formatting."""
    return os.getenv("LLM_PROVIDER", "gemini")


def get_trace_url() -> str | None:
    """Return the LangSmith trace URL for the current run, or None if tracing is disabled."""
    if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() != "true":
        return None
    try:
        from langsmith import Client
        client = Client()
        runs = list(client.list_runs(project_name=os.getenv("LANGCHAIN_PROJECT", "default"), limit=1))
        if runs:
            return client.get_run_url(run=runs[0])
    except Exception:
        pass
    return None
```

Each node must call `get_llm(run_name="<node_name>")` so that every LLM call appears as a named span in LangSmith. Example:

```python
# In chat_parser.py
llm = get_llm(run_name="chat_parser")

# In explainer.py
llm = get_llm(run_name="explainer")
```

**Model-specific input patterns nodes must follow:**

| Concern | Gemini | Claude |
|---------|--------|--------|
| System message | Passed as `SystemMessage` in chain — works natively | Same — `SystemMessage` at index 0 is required; Claude ignores system prompt set any other way |
| `max_tokens` | Uses model default; not required | **Required** — must be set explicitly. `get_llm()` reads `LLM_MAX_TOKENS` from `.env` |
| Tool schema `null` types | Accepts `"type": ["string", "null"]` | Rejects `anyOf` / union types — use `"type": "string"` and note optionality in `description` instead |
| JSON output prompting | Use `generation_config={"response_mime_type": "application/json"}` constructor arg (new SDK) to enforce JSON at the API level — do NOT use `model_kwargs` (old SDK pattern) | Prepend the assistant turn with `{` using `AIMessage(content="{")` to force JSON-only output reliably |
| Markdown wrapping | May wrap JSON in ` ```json ``` ` fences even with mime-type set on Flash Lite — always strip fences before `json.loads()` | Does not wrap when prefill is used |
| Multi-turn history | Alternates `user`/`model` roles strictly — consecutive `HumanMessage` objects raise an error; merge them into one | Alternates `user`/`assistant` roles — same constraint; merge consecutive same-role messages |
| Image / multimodal input | Supported natively via `HumanMessage(content=[{"type": "image_url", ...}])` | Supported via same LangChain interface |
| Token counting field | `usage_metadata.input_tokens` | `usage_metadata.input_tokens` (same LangChain interface) |
| Safety filters | New SDK raises `google.genai.errors.ClientError` with status `BLOCKED` when content triggers safety filters — catch `ClientError` and log, do not crash | No equivalent; raises API error on policy violation |
| Thinking / reasoning tokens | Gemini 2.5 models support `thinking_budget` via `model_kwargs={"thinking": {"type": "enabled", "budget_tokens": 1024}}` — do NOT enable for this bucket (adds latency and cost) | Claude 3.7+ supports extended thinking — do NOT enable for this bucket |

**Gemini-specific patterns to apply in nodes:**

```python
# backend/agents/llm_client.py — Gemini branch
# Use generation_config (new google-genai SDK pattern) — NOT model_kwargs (deprecated).
# Only applies to JSON-output nodes (chat_parser, explainer, replanner_agent).

def get_llm_json(run_name: str | None = None) -> BaseChatModel:
    """Variant of get_llm() that enforces JSON output at the model level.
    Use this in chat_parser_node, explainer_node, replanner_agent_node.
    For Claude, the assistant-prefill pattern is applied in _build_messages() instead.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite-preview-06-17")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0"))
    config = {"run_name": run_name} if run_name else {}

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            # generation_config is the correct parameter in google-genai (new SDK).
            # model_kwargs={"response_mime_type": ...} was the old google-generativeai pattern.
            generation_config={"response_mime_type": "application/json"},
            **config,
        )
    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or "claude-sonnet-4-5",
            temperature=temperature,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            **config,
        )
    # For openai/ollama fall back to standard get_llm()
    return get_llm(run_name=run_name)
```

**Shared `_build_messages()` helper (place in each JSON-output node):**

```python
from backend.agents.llm_client import get_provider
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def _build_messages(system_prompt: str, human_prompt: str) -> list:
    msgs = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]
    if get_provider() == "claude":
        # Prefill forces Claude to start the response with `{`, suppressing preamble
        msgs.append(AIMessage(content="{"))
    return msgs
```

When the Claude prefill is active, prepend `{` back to the raw response string before `json.loads()`.

Gemini note: even with `response_mime_type="application/json"`, Gemini Flash Lite may still occasionally wrap output in ` ```json ``` ` fences. Always strip fences before parsing regardless of provider.

`workflow.py` must call `get_trace_url()` after the workflow completes and store the result in `state["trace_id"]`.

### Step 4: Create `backend/agents/state.py`

Copy the `TripState` TypedDict from Section B.1 exactly.

### Step 5: Create `backend/agents/prompts.py`

Create all prompt templates for Chat Parser, Constraint Validator, Explainer, and Replanner Explainer. Use the constraint schema from Section B.5 as the JSON schema in the Chat Parser prompt.

The spec provides complete prompt text — implement `CHAT_PARSER_SYSTEM`, `CHAT_PARSER_HUMAN`, `CONSTRAINT_VALIDATOR_SYSTEM`, `CONSTRAINT_VALIDATOR_HUMAN`, `EXPLAINER_SYSTEM`, `EXPLAINER_HUMAN`, `REPLANNER_EXPLAIN_SYSTEM`, `REPLANNER_EXPLAIN_HUMAN`.

Each prompt must:
- Instruct the LLM to output ONLY valid JSON (no additional text)
- Include the exact expected JSON schema
- Explicitly say "Do NOT invent information"
- Instruct the LLM to use `.title()` casing for location names (`origin`, `destination`): e.g., `"Gurugram"`, `"Rishikesh"`
- Instruct the LLM to use lowercase for all enum fields: `hotel_tier`, `risk_tolerance`, `destination_type`, items in `transport_preference`, items in `must_include`

### Step 6: Create agent nodes

Create all 6 agent nodes following this pattern. Each node:
1. Takes `TripState` as input
2. Does its work (LLM call or Python logic)
3. Returns a `dict` with only the state fields it modifies

**Files to create:**
- `backend/agents/nodes/chat_parser.py` — `chat_parser_node(state) -> dict`
- `backend/agents/nodes/constraint_validator.py` — `constraint_validator_node(state) -> dict`
- `backend/agents/nodes/data_retriever.py` — `data_retriever_node(state) -> dict`
- `backend/agents/nodes/planner_orchestrator.py` — `planner_orchestrator_node(state) -> dict`
- `backend/agents/nodes/explainer.py` — `explainer_node(state) -> dict`
- `backend/agents/nodes/replanner_agent.py` — `replanner_agent_node(state) -> dict`

**`constraint_validator_node` logic (pure Python, no LLM):**
1. Read `extracted_constraints` from state
2. Normalize all string fields: location names with `.strip().title()`, enum fields (`hotel_tier`, `risk_tolerance`, `destination_type`, `transport_preference` items, `must_include` items) with `.strip().lower()`
3. Check for **missing required fields** (Decision 20): if `origin` is missing, OR both `budget_per_person` and `trip_duration` are missing, OR no preference field is set — add each missing field to `missing_fields` and create a blocking conflict
4. Check for **destination vs destination_type mismatch** (Decision 25): if both are present and contradict, add a blocking conflict
5. Check for **invalid values**: `budget_per_person <= 0` or `group_size <= 0` → blocking conflict
6. Build `conflict_report` using shape from Decision 24
7. Set `is_ready_to_plan = True` only if `blocking_conflicts` is empty
8. Return `{"extracted_constraints": normalized_constraints, "conflict_report": conflict_report, "is_ready_to_plan": bool, "missing_fields": list}`

If `is_ready_to_plan = False`, the workflow conditional routes to END. The returned TripState will have `missing_fields` and `conflict_report` populated so the API layer can return a descriptive error to the user.

**`data_retriever_node` logic:**

Tool selection is controlled by `NEO4J_ENABLED` (Decision 36). Use the existing public function signatures from B.2 for both paths — real and mock share the same interface.

```python
import os

NEO4J_ENABLED = os.getenv("NEO4J_ENABLED", "false").lower() == "true"

if NEO4J_ENABLED:
    # Real tools — existing implementations from Bucket 5 (Section B.2)
    from backend.tools.route_tool import get_routes
    from backend.tools.hotel_tool import get_hotels
    from backend.tools.activity_tool import get_activities
    from backend.tools.transport_tool import get_transport_options
    from backend.tools.restaurant_tool import get_restaurants
    from backend.tools.waypoint_tool import get_waypoints
else:
    # Mock tools — same signatures, return data from Section B.4
    from backend.agents.nodes.mock_tools import (
        get_routes, get_hotels, get_activities,
        get_transport_options, get_restaurants, get_waypoints,
    )
```

When `NEO4J_ENABLED=true`, each call is wrapped in try/except; on exception, fall back to the corresponding mock function (same signature, same return shape). Node steps:

1. Read `extracted_constraints` from state; normalize location strings (Decision 21)
2. Call `get_routes(origin, destination_type)` → `route_candidates`
3. For each route call `get_hotels`, `get_activities`, `get_transport_options`, `get_restaurants`, `get_waypoints`
4. Return state fields: `route_candidates`, `hotel_candidates`, `activity_candidates`, `transport_candidates`, `food_candidates`, `waypoint_candidates`

**`planner_orchestrator_node` logic:**
1. Collect retrieved data into a single `data` dict with keys: `routes`, `hotels`, `transport`, `activities`, `food`, `waypoints`
2. Call `generate_candidates(constraints, data)`
3. For each candidate, call `score_itinerary()` and `validate_itinerary()`
4. Sort: valid candidates first (by score descending), then invalid
5. Select best valid candidate (or best invalid if none valid)
6. Call `generate_timeline()` for selected
7. Extract `map_points` from selected itinerary
8. Return `selected_itinerary`, `alternative_itineraries`, `timeline`, `map_points`, `cost_breakdown`, `validation_report`, `score_breakdown`

**`_extract_map_points` helper:**
```python
def _extract_map_points(itinerary: dict) -> list[dict]:
    """Extract lat/lng points from itinerary for Leaflet map display."""
    points = []
    route = itinerary.get("route", {})
    hotel = itinerary.get("hotel", {})
    activities = itinerary.get("activities", [])
    waypoints = itinerary.get("waypoints", [])

    # Origin
    points.append({
        "lat": 28.4595, "lng": 77.0266,
        "label": route.get("origin", "Gurugram"), "type": "origin"
    })
    # Waypoints
    for wp in waypoints:
        if wp.get("lat") and wp.get("lng"):
            points.append({
                "lat": wp["lat"], "lng": wp["lng"],
                "label": wp.get("name", "Waypoint"), "type": "waypoint"
            })
    # Destination
    if route.get("dest_lat") and route.get("dest_lng"):
        points.append({
            "lat": route["dest_lat"], "lng": route["dest_lng"],
            "label": route.get("destination", "Destination"), "type": "destination"
        })
    # Hotel
    if hotel.get("lat") and hotel.get("lng"):
        points.append({
            "lat": hotel["lat"], "lng": hotel["lng"],
            "label": hotel.get("name", "Hotel"), "type": "hotel"
        })
    # Activities
    for act in activities:
        if act.get("lat") and act.get("lng"):
            points.append({
                "lat": act["lat"], "lng": act["lng"],
                "label": act.get("name", "Activity"), "type": "activity"
            })
    return points
```

### Step 7: Create `backend/agents/workflow.py`

Build two LangGraph workflows:
1. **Main workflow**: `parse_chat → validate_constraints → [conditional] → retrieve_data → plan_itinerary → explain_plan → END`
2. **Replan workflow**: `replan → END`

The two **public functions are the single entry point** for all callers (Bucket 3 API). They read `PIPELINE_MODE` and delegate to the correct backend — callers never import from engine-specific modules.

```python
import os
from backend.agents.state import TripState

def run_workflow(chat_messages: list[str]) -> TripState:
    """Public entry point. Engine selected via PIPELINE_MODE env var."""
    engine = os.getenv("PIPELINE_MODE", "langgraph")

    if engine == "augmented_llm":
        from backend.agents_augmented.workflow import run_workflow as _run
        return _run(chat_messages)

    # Default: langgraph
    return _langgraph_run_workflow(chat_messages)


def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    """Public entry point for replanning. Engine selected via PIPELINE_MODE env var."""
    engine = os.getenv("PIPELINE_MODE", "langgraph")

    if engine == "augmented_llm":
        from backend.agents_augmented.workflow import run_replan_workflow as _replan
        return _replan(state, delay_event)

    # Default: langgraph
    return _langgraph_replan_workflow(state, delay_event)


def _langgraph_run_workflow(chat_messages: list[str]) -> TripState:
    """Internal: runs the LangGraph multi-node pipeline."""
    # Build and invoke the LangGraph StateGraph here.
    ...


def _langgraph_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    """Internal: runs the LangGraph replan node."""
    ...
```

The conditional edge after `validate_constraints` checks `is_ready_to_plan`:
- If `True`: proceed to `retrieve_data`
- If `False`: go to `END` (return partial state with `missing_fields`)

---

## Section E — File Manifest

```
backend/agents/__init__.py                     — Package init
backend/agents/llm_client.py                   — Swappable LLM factory
backend/agents/state.py                        — TripState TypedDict
backend/agents/prompts.py                      — All prompt templates
backend/agents/workflow.py                     — LangGraph workflows, exports run_workflow()
backend/agents/nodes/__init__.py               — Nodes package init
backend/agents/nodes/chat_parser.py            — Agent 1: extract constraints from chat
backend/agents/nodes/constraint_validator.py   — Agent 2: validate constraints
backend/agents/nodes/data_retriever.py         — Agent 3: fetch data via tool functions
backend/agents/nodes/planner_orchestrator.py   — Agent 4: run planning engine
backend/agents/nodes/explainer.py              — Agent 5: generate NL explanation
backend/agents/nodes/replanner_agent.py        — Agent 6: handle delay replanning
backend/agents/run.py                          — Output inspection script: runs workflow and prints every TripState field
specs/logs/bucket_2_decisions.md               — Decisions & assumptions log
```

---

## Section F — Integration Verification Checklist & Test Script

### Pre-Commit Checklist
- [ ] All frozen field names in TripState match Section B.1 exactly
- [ ] No `TODO` or `pass` in any node function
- [ ] Import paths are correct: `from backend.tools.route_tool import get_routes`
- [ ] Mock data is present and operational for all 6 tool functions
- [ ] LLM client initializes with Gemini API key
- [ ] Chat parser extracts correct JSON from sample chat
- [ ] Full workflow runs end-to-end: `run_workflow(["Let's go to mountains from Gurugram"])`
- [ ] `specs/logs/bucket_2_decisions.md` is created

### Runnable Test Script

Create `backend/tests/test_bucket_2.py`:

```python
"""
Bucket 2 Validation Script.
Tests the full agentic pipeline end-to-end.
Run: PYTHONPATH=. python backend/tests/test_bucket_2.py
Requires: GOOGLE_API_KEY in .env for LLM calls
"""
import os
import sys

# Check for API key
if not os.getenv("GOOGLE_API_KEY"):
    print("⚠️ GOOGLE_API_KEY not set. Testing with mock mode only.")
    MOCK_MODE = True
else:
    MOCK_MODE = False

print("=" * 60)
print("Bucket 2 — Agentic Pipeline Validation")
print("=" * 60)

# Test 1: State schema
print("\n📋 Test 1: TripState schema")
from backend.agents.state import TripState
print("  ✅ TripState imported successfully")

# Test 2: LLM client
print("\n🤖 Test 2: LLM client")
try:
    from backend.agents.llm_client import get_llm
    if not MOCK_MODE:
        llm = get_llm()
        print(f"  ✅ LLM initialized: {type(llm).__name__}")
    else:
        print("  ⏭️ Skipped (no API key)")
except Exception as e:
    print(f"  ❌ LLM init failed: {e}")

# Test 3: Prompts
print("\n📝 Test 3: Prompts")
from backend.agents.prompts import CHAT_PARSER_SYSTEM, EXPLAINER_SYSTEM
print(f"  ✅ CHAT_PARSER_SYSTEM loaded ({len(CHAT_PARSER_SYSTEM)} chars)")
print(f"  ✅ EXPLAINER_SYSTEM loaded ({len(EXPLAINER_SYSTEM)} chars)")

# Test 4: Workflow
print("\n🔄 Test 4: Workflow")
from backend.agents.workflow import run_workflow, run_replan_workflow
print("  ✅ run_workflow and run_replan_workflow imported")

# Test 5: End-to-end (only with API key)
if not MOCK_MODE:
    print("\n🚀 Test 5: End-to-end workflow")
    try:
        result = run_workflow([
            "Let's do a weekend trip from Gurugram",
            "Budget under 15k per person",
            "Mountains please, not Jaipur",
            "No night driving",
            "Need rafting and good cafes",
        ])
        print(f"  ✅ Workflow completed")
        print(f"  Constraints: {result.get('extracted_constraints', {}).get('origin')}")
        print(f"  Selected: {result.get('selected_itinerary', {}).get('destination', 'N/A')}")
        print(f"  Explanation: {result.get('explanation', 'N/A')[:100]}...")
        print(f"  Timeline events: {len(result.get('timeline', []))}")
        print(f"  Map points: {len(result.get('map_points', []))}")
    except Exception as e:
        print(f"  ❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n⏭️ Test 5: Skipped (no API key)")

print("\n" + "=" * 60)
print("Bucket 2 validation complete.")
```

---

### `backend/agents/run.py` — Bucket 2 Output Inspection Script

Create `backend/agents/run.py`. Run this script to see exactly what the system produces for a given input — extracted constraints, selected itinerary, timeline, map points, cost breakdown, explanation, and replanning output. No pass/fail logic; just raw system output printed clearly so you can read and evaluate it.

```python
"""
backend/agents/run.py — Bucket 2 output inspection script.

Run the full workflow and replanning workflow with sample input and
print every field of the resulting TripState so you can see what the
system actually produces.

Usage (from project root):
    PYTHONPATH=. python backend/agents/run.py
    PYTHONPATH=. NEO4J_ENABLED=false python backend/agents/run.py
    PYTHONPATH=. LLM_PROVIDER=claude ANTHROPIC_API_KEY=... python backend/agents/run.py
"""
import json
import os

from dotenv import load_dotenv
load_dotenv()

from backend.agents.workflow import run_workflow, run_replan_workflow

# ── Sample input ──────────────────────────────────────────────────────────────

SAMPLE_CHAT = [
    "Hey everyone — let's plan a weekend trip from Gurugram!",
    "Budget: around 12k per person",
    "Mountains only please, not Jaipur again",
    "No overnight driving, we're all tired after work",
    "Must have river rafting and good cafes",
]

SAMPLE_DELAY_EVENT = {
    "type": "transport_delay",
    "description": "Return bus delayed by 4 hours due to landslide on Rishikesh route",
    "affected_segment": "return_journey",
    "delay_hours": 4,
}

SEP = "=" * 60

# ── Helpers ───────────────────────────────────────────────────────────────────

def _serializable(obj):
    """Recursively convert non-JSON-serializable objects (e.g. dataclasses) to str."""
    if isinstance(obj, dict):
        return {k: _serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serializable(i) for i in obj]
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _print_section(title: str, value) -> None:
    print(f"\n── {title} {'─' * max(0, 50 - len(title))}")
    if isinstance(value, (dict, list)):
        print(json.dumps(_serializable(value), indent=2, ensure_ascii=False))
    else:
        print(value)


# ── Run 1: full workflow ──────────────────────────────────────────────────────

print(SEP)
print("Bucket 2 — Output Inspection")
print(f"NEO4J_ENABLED : {os.getenv('NEO4J_ENABLED', 'false')}")
print(f"LLM_PROVIDER  : {os.getenv('LLM_PROVIDER', 'gemini')}")
print(f"LLM_MODEL     : {os.getenv('LLM_MODEL', 'gemini-2.5-flash-lite-preview-06-17')}")
print(SEP)

print("\nInput chat:")
for line in SAMPLE_CHAT:
    print(f"  > {line}")

print(f"\n{SEP}")
print("Running run_workflow() ...")
print(SEP)

state = run_workflow(SAMPLE_CHAT)

_print_section("extracted_constraints",   state.get("extracted_constraints"))
_print_section("missing_fields",          state.get("missing_fields"))
_print_section("assumptions",             state.get("assumptions"))
_print_section("conflict_report",         state.get("conflict_report"))
_print_section("is_ready_to_plan",        state.get("is_ready_to_plan"))
_print_section("route_candidates",        state.get("route_candidates"))
_print_section("hotel_candidates",        state.get("hotel_candidates"))
_print_section("transport_candidates",    state.get("transport_candidates"))
_print_section("activity_candidates",     state.get("activity_candidates"))
_print_section("food_candidates",         state.get("food_candidates"))
_print_section("waypoint_candidates",     state.get("waypoint_candidates"))
_print_section("selected_itinerary",      state.get("selected_itinerary"))
_print_section("alternative_itineraries", state.get("alternative_itineraries"))
_print_section("validation_report",       state.get("validation_report"))
_print_section("score_breakdown",         state.get("score_breakdown"))
_print_section("timeline",                state.get("timeline"))
_print_section("map_points",              state.get("map_points"))
_print_section("cost_breakdown",          state.get("cost_breakdown"))
_print_section("explanation",             state.get("explanation"))
_print_section("trace_id",               state.get("trace_id"))

# ── Run 2: replanning workflow ────────────────────────────────────────────────

print(f"\n{SEP}")
print("Running run_replan_workflow() ...")
print(SEP)
print("\nDelay event:")
print(json.dumps(SAMPLE_DELAY_EVENT, indent=2))

replan_state = run_replan_workflow(state, SAMPLE_DELAY_EVENT)

_print_section("replanned_itinerary",    replan_state.get("replanned_itinerary"))
_print_section("replanning_explanation", replan_state.get("replanning_explanation"))
_print_section("timeline (updated)",     replan_state.get("timeline"))
_print_section("map_points (updated)",   replan_state.get("map_points"))
_print_section("trace_id",              replan_state.get("trace_id"))

print(f"\n{SEP}")
print("Done.")
```

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

---

## Section G — 📋 Assumptions & Decisions Log (Output File)

**You MUST create:** `specs/logs/bucket_2_decisions.md`

```markdown
# Bucket 2 — Decisions & Assumptions Log
Generated by: [Model Name] on [Date]

## Pre-Specified Decisions Applied
## Unspecified Decisions Made During Build
## Deviations from Spec
## External Assumptions
## Validation Results
```

---

## Git Commit Protocol

```
1. Stage all files listed in File Manifest (Section E)
2. Stage backend/tests/test_bucket_2.py
3. Stage backend/agents/run.py
4. Stage specs/logs/bucket_2_decisions.md
5. Commit message: "Bucket 2: LangGraph agentic pipeline with 6 agents — [date]"
6. Branch: bucket-2/implementation
7. Push to origin
8. Do NOT merge to main
```

---

## Common Pitfalls

1. **JSON parsing**: Gemini sometimes wraps JSON in markdown code blocks. Always handle both raw JSON and ` ```json ``` ` wrapped responses.
2. **Rate limits**: `get_llm()` enforces `LLM_RATE_LIMIT_RPM=15` via a sliding-window tracker — execution slows automatically, no manual `time.sleep()` needed. Each node should call `get_llm()` once per `invoke()`, not at module load time, so the rate check happens at the right moment.
3. **State initialization**: Every field in TripState must have a value (even if empty list/dict/None). Missing keys cause LangGraph errors.
4. **Import cycles**: Tool and planner imports are at the top of node files. If circular import issues arise, use late imports inside the function body.
5. **Non-serializable objects**: The `trip_graph` field in candidates contains dataclass instances. Use `default=str` in any `json.dumps()` call. LLM prompts should NOT include the raw trip_graph object.
6. **Case mismatch**: The LLM may return location names in any casing (`"rishikesh"`, `"GURUGRAM"`) and enum fields with mixed case (`"Comfort"`, `"Medium"`). Always normalize immediately after JSON parsing in `chat_parser_node` (Decision 21–23). Do not rely on the prompt instruction alone — add code-level normalization as a safety net.
7. **Conflicting constraints not caught early**: `constraint_validator_node` only detects conflicts detectable from the constraints alone (missing fields, destination mismatch, invalid values). Budget vs actual cost and must_include unavailability are detected post-planning in `planner_orchestrator_node`. Always populate `conflict_report` with warnings from `validation_report` before returning final state (Decisions 26–27).

---

## Section H — Acceptance Criteria

The bucket is considered complete only when **all** criteria below are satisfied.

### Functional Requirements
- [ ] `run_workflow(chat_messages)` returns a valid `TripState` with all fields populated
- [ ] `run_replan_workflow(state, delay_event)` returns an updated `TripState` with `replanned_itinerary` and `replanning_explanation`
- [ ] Chat parser extracts all 14 constraint fields from natural language group chat
- [ ] Constraint validator correctly identifies blocking conflicts and sets `is_ready_to_plan=False`
- [ ] Constraint validator correctly identifies non-blocking warnings without blocking planning
- [ ] Data retriever fetches all 6 data types (routes, hotels, activities, transport, restaurants, waypoints)
- [ ] Planner produces at least 1 `selected_itinerary` and up to 3 `alternative_itineraries`
- [ ] `timeline` is populated with at least 2 events
- [ ] `map_points` contains at minimum origin and destination points
- [ ] `cost_breakdown` and `explanation` are non-empty
- [ ] Workflow short-circuits to END when `is_ready_to_plan=False`, returning `missing_fields` and `conflict_report`

### Architecture Requirements
- [ ] No hardcoded workflow steps — all LLM calls go through `get_llm()` in `llm_client.py`
- [ ] `run_workflow()` and `run_replan_workflow()` are the only public entry points; Bucket 3 imports from `backend.agents.workflow` only
- [ ] `PIPELINE_MODE=augmented_llm` correctly delegates to `backend.agents_augmented.workflow` with no code changes in the caller
- [ ] `PIPELINE_MODE=langgraph` (default) correctly runs the LangGraph multi-node pipeline
- [ ] No LangChain imports outside of `llm_client.py` and node files

### Tool Requirements
- [ ] `NEO4J_ENABLED=false` runs end-to-end using only mock data (no Neo4j connection required)
- [ ] `NEO4J_ENABLED=true` attempts real tool calls and falls back to mock on any exception
- [ ] Mock tool functions in `mock_tools.py` have identical signatures to real tools in Section B.2
- [ ] Mock data covers both Gurugram→Rishikesh (mountains) and Gurugram→Jaipur (heritage) routes
- [ ] All 6 planner functions (Section B.3) are called via their existing import paths — not reimplemented

### State Requirements
- [ ] `TripState` matches Section B.1 exactly — no added, removed, or renamed fields
- [ ] Every field is initialized in `run_workflow()` (empty list/dict/None as appropriate)
- [ ] `trace_id` is populated when `LANGCHAIN_TRACING_V2=true`, `None` otherwise

### Safety & Rate Limit Requirements
- [ ] LLM calls never exceed `LLM_RATE_LIMIT_RPM` (default 15) per minute — enforced by `_wait_for_rate_limit()` in `llm_client.py`
- [ ] Rate limiter uses a sliding 60-second window, not a fixed reset interval
- [ ] Rate limiter logs sleep duration when throttling: `[RATE LIMIT] Sleeping Xs`
- [ ] LLM failures are caught, logged with `[ERROR] LLM call failed: ...`, and re-raised (Decision 8)
- [ ] Invalid JSON is retried once before falling back to defaults (Decision 7)

### Provider Requirements
- [ ] `LLM_PROVIDER=gemini` initializes `ChatGoogleGenerativeAI` using `langchain-google-genai>=2.0` (new `google-genai` SDK)
- [ ] `LLM_PROVIDER=claude` initializes `ChatAnthropic` with explicit `max_tokens` from `LLM_MAX_TOKENS`
- [ ] JSON-output nodes use `get_llm_json()`: Gemini gets `generation_config={"response_mime_type": "application/json"}`, Claude gets assistant prefill `{`
- [ ] Switching `LLM_PROVIDER` requires only a `.env` change — no code changes

### Normalization Requirements
- [ ] Location names (`origin`, `destination`) are normalized to `.title()` in `chat_parser_node` immediately after JSON parse
- [ ] Enum fields (`hotel_tier`, `risk_tolerance`, `destination_type`, `transport_preference` items, `must_include` items) are normalized to lowercase in `constraint_validator_node`
- [ ] `must_include` matching uses case-insensitive substring match against activity `name` and `tags`

### Observability Requirements
- [ ] `LANGCHAIN_TRACING_V2=true` sends traces to LangSmith with no code changes beyond setting the env var
- [ ] Each node passes `run_name="<node_name>"` to `get_llm()` so spans are labeled in LangSmith
- [ ] `trace_id` in `TripState` contains the LangSmith run URL when tracing is enabled

### Testing Requirements
- [ ] `backend/tests/test_bucket_2.py` runs without errors when `NEO4J_ENABLED=false`
- [ ] End-to-end test with `run_workflow(["Let's go to mountains from Gurugram"])` completes successfully
- [ ] End-to-end replan test with `run_replan_workflow(state, delay_event)` completes successfully
- [ ] `PYTHONPATH=. NEO4J_ENABLED=false python backend/agents/run.py` runs without crashing and prints all TripState fields
- [ ] `backend/agents/run.py` output shows a non-empty `explanation` and at least one `timeline` event
- [ ] `backend/agents/run.py` output shows a non-empty `replanning_explanation` in the replan section
- [ ] `specs/logs/bucket_2_decisions.md` is created and non-empty

### Success Condition

A user provides a group chat and the system autonomously:

1. Extracts all travel constraints with correct casing and types
2. Validates constraints and reports conflicts clearly
3. Retrieves real or mock travel data
4. Generates, scores, and validates itinerary candidates
5. Produces a complete `TripState` with timeline, map points, cost breakdown, and explanation
6. Stays within the configured LLM rate limit throughout

All of the above must work with `NEO4J_ENABLED=false` using mock data alone.
