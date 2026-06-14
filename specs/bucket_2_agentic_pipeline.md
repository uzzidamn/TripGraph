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
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_TEMPERATURE=0
```

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
| 10 | Rate limit handling for Gemini Free | Add `import time; time.sleep(4)` between LLM calls if rate limits are hit during testing. |
| 11 | What does empty `must_include` mean | No activity constraints; accept all activities. |
| 12 | What does `avoid_night_driving: false` mean | Night driving is acceptable; do NOT penalize. |
| 13 | How many alternatives to return | Up to 3 (from lower-scored valid candidates + invalid candidates) |
| 14 | What if no valid candidates exist | Return the highest-scored invalid candidate as `selected_itinerary` with `validation_report.is_valid = False`. |
| 15 | Map points extraction | Extract lat/lng from: route origin, waypoints, destination city, hotel, each activity. Label format: `{"lat": float, "lng": float, "label": str, "type": str}` |
| 16 | `map_points` type values | `"origin"`, `"waypoint"`, `"destination"`, `"hotel"`, `"activity"` |
| 17 | Workflow export function names | `run_workflow(chat_messages)` and `run_replan_workflow(state, delay_event)` — these are the public API called by Bucket 3. |
| 18 | LLM provider packages | `langchain-google-genai` for Gemini, `langchain-openai` for OpenAI, `langchain-ollama` for Ollama. Only install the one you need. |
| 19 | Mock vs real tool imports | Use try/except: try real imports first, fall back to mock if ImportError. This lets the bucket run independently. |
| 20 | Constraint Validator: what fields are required to proceed | At minimum: `origin` AND (`budget_per_person` OR `trip_duration`) AND at least one preference (`destination_type`, `must_include`, or `destination`). |

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
Supported providers: gemini, openai, ollama
"""
import os
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()


def get_llm() -> BaseChatModel:
    """Create and return an LLM instance based on environment config."""
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0"))

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: gemini, openai, ollama")
```

### Step 4: Create `backend/agents/state.py`

Copy the `TripState` TypedDict from Section B.1 exactly.

### Step 5: Create `backend/agents/prompts.py`

Create all prompt templates for Chat Parser, Constraint Validator, Explainer, and Replanner Explainer. Use the constraint schema from Section B.5 as the JSON schema in the Chat Parser prompt.

The spec provides complete prompt text — implement `CHAT_PARSER_SYSTEM`, `CHAT_PARSER_HUMAN`, `CONSTRAINT_VALIDATOR_SYSTEM`, `CONSTRAINT_VALIDATOR_HUMAN`, `EXPLAINER_SYSTEM`, `EXPLAINER_HUMAN`, `REPLANNER_EXPLAIN_SYSTEM`, `REPLANNER_EXPLAIN_HUMAN`.

Each prompt must:
- Instruct the LLM to output ONLY valid JSON (no additional text)
- Include the exact expected JSON schema
- Explicitly say "Do NOT invent information"

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

**`data_retriever_node` logic:**
1. Read `extracted_constraints` from state
2. Call `get_routes(origin, destination_type)`
3. For each route, call `get_hotels`, `get_activities`, `get_transport_options`, `get_restaurants`, `get_waypoints`
4. Return all results in state fields

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

Export two public functions:
- `run_workflow(chat_messages: list[str]) -> TripState`
- `run_replan_workflow(state: TripState, delay_event: dict) -> TripState`

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
3. Stage specs/logs/bucket_2_decisions.md
4. Commit message: "Bucket 2: LangGraph agentic pipeline with 6 agents — [date]"
5. Branch: bucket-2/implementation
6. Push to origin
7. Do NOT merge to main
```

---

## Common Pitfalls

1. **JSON parsing**: Gemini sometimes wraps JSON in markdown code blocks. Always handle both raw JSON and ` ```json ``` ` wrapped responses.
2. **Rate limits**: Free Gemini has 15 RPM. If you hit limits during testing, add `time.sleep(4)` between workflow runs.
3. **State initialization**: Every field in TripState must have a value (even if empty list/dict/None). Missing keys cause LangGraph errors.
4. **Import cycles**: Tool and planner imports are at the top of node files. If circular import issues arise, use late imports inside the function body.
5. **Non-serializable objects**: The `trip_graph` field in candidates contains dataclass instances. Use `default=str` in any `json.dumps()` call. LLM prompts should NOT include the raw trip_graph object.
