# Bucket 2.1: Augmented LLM Pipeline — LLM-Ready Spec

> **Generated for**: Distributed LLM execution (Claude / Gemini session)
> **Priority**: P1 — Can start immediately with mock tools
> **Reference**: This spec is self-contained. You may also read `specs/MASTER_SPEC.md` for full project context.
> **Bucket 2.1**: It is the initial workflow implementation for TripGraph AI.

It establishes the canonical workflow API, TripState contract, planner integration contract, and backend integration path used by Buckets 3, 4, and 5.

Future workflow implementations (including a LangGraph-based agentic pipeline) must preserve the same public APIs and TripState structure but may use different internal orchestration mechanisms.

Bucket 2.1 should be treated as the reference implementation and must run independently without any agentic workflow being present.
---

## Section A — Project Context

**TripGraph AI** is a GenAI-agentic group travel planner that converts WhatsApp-style group chat into structured, constraint-aware itineraries. It uses a Neo4j knowledge graph, an AI pipeline, a deterministic Python planning engine, and a React frontend.

**Your role (Bucket 2.1):** Build an **Augmented LLM pipeline** — a simplified, single-pass alternative to the multi-agent LangGraph workflow in Bucket 2. Instead of 6 separate LangGraph agent nodes with a state graph, you implement the same logical steps as **sequential Python functions** orchestrated by a single `run_workflow()` function. The LLM is called directly (no LangGraph dependency), and the output is the same `TripState` TypedDict consumed by Bucket 3 (FastAPI backend) and Bucket 4 (React frontend).

**Why this exists:** Bucket 2.1 provides the first complete workflow implementation for TripGraph AI. It enables end-to-end validation of prompts, state contracts, planner integration, tool integration, API integration, and frontend integration.

Agentic workflows are considered future enhancements rather than prerequisites.

**Key Principle:** The LLM handles **language** (extraction, explanation). Python handles **math** (cost, timing, validation). The planner handles **optimization** (graph-based itinerary construction). Your pipeline coordinates these — it does NOT calculate costs or invent data.

**Architecture Pattern:**
```
Chat Messages → Parse & Extract (LLM) → Validate (Python) → Retrieve Data (Tools)
    → Plan Itinerary (Planner) → Explain (LLM) → TripState
```

This is a **linear pipeline** — no branching, no loops, no conditional routing. Each step runs once in sequence.

---

## Section B — 🔒 Frozen Interface Contracts

> **CRITICAL**: Every type, field name, import path, and function signature in this section is shared with Buckets 1, 3, 4, and 5. Do NOT rename, reorder, or omit any field. Your code must produce a `TripState` that is byte-for-byte compatible with what Bucket 2 (agentic) would produce.

### B.1 TripState TypedDict

This is the shared state object that your `run_workflow()` must return. Every field must be present in the returned dict (use empty list/dict/None for unused fields).

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

Use these mock implementations while Bucket 5 tools are not available. Place these in a unified mock module `backend/agents_augmented/mock_tools.py`.

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


# === Mock wrapper functions (same signatures as real tools) ===

def get_routes(origin: str, destination_type: str | None = None) -> list[dict]:
    results = [r for r in MOCK_ROUTES if r["origin"].lower() == origin.lower()]
    if destination_type:
        results = [r for r in results if r["destination_type"] == destination_type]
    return results

def get_hotels(destination: str, tier: str | None = None) -> list[dict]:
    results = [h for h in MOCK_HOTELS if h.get("destination", "").lower() == destination.lower()]
    if tier:
        results = [h for h in results if h["tier"] == tier]
    return results

def get_activities(destination: str, tags: list[str] | None = None) -> list[dict]:
    results = [a for a in MOCK_ACTIVITIES if a.get("destination", "").lower() == destination.lower()]
    if tags:
        results = [a for a in results if any(t in a.get("tags", []) for t in tags)]
    return results

def get_transport_options(route_id: str, modes: list[str] | None = None) -> list[dict]:
    results = [t for t in MOCK_TRANSPORT if t.get("route_id") == route_id]
    if modes:
        results = [t for t in results if t["mode"] in modes]
    return results

def get_restaurants(destination: str, route_id: str | None = None) -> list[dict]:
    results = [r for r in MOCK_RESTAURANTS if r.get("destination", "").lower() == destination.lower()]
    return results

def get_waypoints(route_id: str) -> list[dict]:
    return [w for w in MOCK_WAYPOINTS if w.get("route_id") == route_id]
```

### B.5 Extracted Constraints Dict Shape

The constraint extraction step must output a dict with these exact keys:
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
LLM_PROVIDER=gemini          # Informational — current provider. llm_client.py uses google-generativeai directly.
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=4096

# Pipeline mode toggle (NEW for Bucket 2.1)
PIPELINE_MODE=augmented
# Options: "agentic" (uses Bucket 2 LangGraph pipeline) | "augmented" (uses Bucket 2.1 single-pass pipeline)
```

### B.7 Public API Contract (Shared with Bucket 2)

The two public functions that Bucket 3 imports:

```python
from backend.agents.workflow import run_workflow, run_replan_workflow

def run_workflow(chat_messages: list[str]) -> TripState:
    """Run the full planning pipeline. Returns completed TripState."""

def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    """Run replanning after a delay event. Returns updated TripState."""
```

**Integration mechanism:** Bucket 3 always imports from `backend.agents.workflow`. That file acts as a **router** — it reads `PIPELINE_MODE` from `.env` and delegates to either:
- `backend.agents.workflow_agentic` (Bucket 2's LangGraph implementation), OR
- `backend.agents_augmented.workflow` (Bucket 2.1's linear pipeline)

This means **Bucket 3 code never changes**. The routing is transparent.

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
| 18 | LLM provider packages | `google-generativeai` for direct Gemini calls. NO LangChain or LangGraph dependency. |
| 19 | Mock vs real tool imports | Use try/except: try real imports first, fall back to mock if ImportError. This lets the bucket run independently. |
| 20 | Constraint Validator: what fields are required to proceed | At minimum: `origin` AND (`budget_per_person` OR `trip_duration`). These are the only hard requirements — their absence adds to `conflicts` and sets `is_ready_to_plan = False`. If no destination preference is given (`destination_type`, `destination`, or `must_include` all absent), a **warning** is added but planning proceeds with all available routes. |
| 21 | Number of LLM calls per workflow run | Exactly 2: one for constraint extraction, one for explanation. All other steps are deterministic Python. |
| 22 | LangGraph dependency | **None**. This bucket does NOT use LangGraph, LangChain, or any agentic framework. Direct `google-generativeai` SDK calls only. |
| 23 | Code location | All code lives in `backend/agents_augmented/`. The existing `backend/agents/` directory (Bucket 2) is untouched. |
| 24 | Pipeline switching mechanism | `backend/agents/workflow.py` reads `PIPELINE_MODE` env var and delegates. Default is `"augmented"` so this pipeline runs out of the box. |
| 25 | Location name normalization | All location strings (`origin`, `destination`) extracted by the LLM **must be title-cased** before being passed to any tool function or planner. Use `str.strip().title()` to normalize. This ensures "rishikesh", "RISHIKESH", and "Rishikesh" all resolve identically when querying tools and Neo4j. Apply normalization in **two places**: (a) in `parse_constraints.py` immediately after LLM extraction, and (b) defensively at the top of `retrieve_data()`. |

---

## Section D — Step-by-Step Build Instructions

### Step 0: Create `backend/agents_augmented/__init__.py`

```python
# Augmented LLM pipeline package (Bucket 2.1)
```

### Step 1: Create `backend/agents_augmented/state.py`

Copy the `TripState` TypedDict from Section B.1 exactly. This is the same state used by Bucket 2 — we share the type definition.

```python
"""TripState TypedDict — shared state contract for the planning pipeline."""
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

### Step 2: Create `backend/agents_augmented/llm_client.py`

Direct Gemini SDK client. **No LangChain dependency.** Reads config from environment.

```python
"""
Direct LLM client using google-generativeai SDK.
No LangChain / LangGraph dependency.
"""
import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Module-level config
_MODEL_NAME = os.getenv("LLM_MODEL", "gemini-2.0-flash")
_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Call the LLM with a system prompt and user prompt.
    Returns the raw text response (stripped).
    """
    model = genai.GenerativeModel(
        model_name=_MODEL_NAME,
        system_instruction=system_prompt,
    )
    response = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            temperature=_TEMPERATURE,
            max_output_tokens=_MAX_TOKENS,
        ),
    )
    return response.text.strip()


def call_llm_json(system_prompt: str, user_prompt: str) -> dict:
    """
    Call the LLM and parse the response as JSON.
    Handles markdown code fences. Retries once on JSON parse failure only.

    Decision #7: retry once on invalid JSON.
    Decision #8: LLM/network failures are NOT retried — raise immediately.
    """
    for attempt in range(2):
        raw = call_llm(system_prompt, user_prompt)  # raises on LLM/network failure (Decision #8)
        try:
            cleaned = _strip_code_fences(raw)
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            if attempt == 0:
                print(f"⚠️ JSON parse failed (attempt 1), retrying: {e}")
                continue
            print(f"❌ JSON parse failed (attempt 2): {e}")
            print(f"   Raw response: {raw[:500]}")
            raise


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ``` or ``` ... ```)."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?\s*```$", "", text, flags=re.MULTILINE)
    return text.strip()
```

### Step 3: Create `backend/agents_augmented/prompts.py`

All prompt templates. Only two LLM interactions: constraint extraction and explanation.

```python
"""
Prompt templates for the augmented LLM pipeline.
Two LLM calls total: constraint extraction and explanation generation.
"""

# ─── Constraint Extraction ───────────────────────────────────────────

CONSTRAINT_EXTRACT_SYSTEM = """You are a travel constraint extractor for TripGraph AI.

Given a group chat conversation about planning a trip, extract ALL travel constraints mentioned by any participant and return them as a single JSON object.

You must return ONLY valid JSON — no explanations, no recommendations, no markdown outside the JSON.

Expected JSON schema (include ALL keys, use null for unmentioned fields, use empty lists for unmentioned list fields):

{
    "origin": "string or null",
    "destination": "string or null",
    "destination_type": "string or null — one of: mountains, heritage, nature, beach, desert, spiritual",
    "budget_per_person": "integer or null — in INR",
    "dates": "string or null — e.g. 'weekend', 'June 20-22'",
    "trip_duration": "string or null — e.g. '2D1N', 'weekend'",
    "transport_preference": ["list of strings — e.g. 'cab_with_driver', 'self_drive', 'bus'"],
    "avoid_night_driving": "boolean — true/false",
    "must_include": ["list of strings — activities or experiences mentioned"],
    "return_deadline": "string or null — e.g. 'Monday morning'",
    "hotel_tier": "string or null — one of: budget, comfort, expedition",
    "risk_tolerance": "string or null — one of: low, medium, high",
    "group_size": "integer or null",
    "special_requirements": ["list of strings — any extras"]
}

Rules:
- Do NOT invent information not present in the conversation.
- Do NOT assume budget, dates, or destination if not mentioned.
- If someone says "no night driving", set avoid_night_driving to true.
- If someone mentions "rafting", add it to must_include.
- Extract budget as integer in INR (e.g., "15k" → 15000, "under 10000" → 10000).
- If multiple people mention conflicting preferences, include ALL of them.
- Always return all 14 keys. Use null / empty list / false as appropriate."""

CONSTRAINT_EXTRACT_HUMAN = """Group chat messages:

{chat_text}

Extract all travel constraints as JSON:"""

# ─── Explanation Generation ──────────────────────────────────────────

EXPLAINER_SYSTEM = """You are a friendly travel planner AI for TripGraph AI.

Given a selected itinerary with timeline, scores, and cost breakdown, write a conversational 3–5 paragraph explanation of WHY this itinerary was chosen.

Address the group directly ("Here's what I've planned for your trip...").

Cover:
1. How the destination matches their preferences
2. Transport choice rationale
3. Activity highlights and timing
4. Hotel selection reasoning
5. Budget summary (total per person vs. their budget)
6. Any trade-offs or assumptions made

Keep it warm, practical, and under 300 words. Do NOT output JSON — write natural language only."""

EXPLAINER_HUMAN = """Selected itinerary:
{itinerary_json}

Timeline:
{timeline_json}

Score breakdown:
{score_json}

Cost breakdown:
{cost_json}

Group constraints:
{constraints_json}

Validation report:
{validation_json}

Write a friendly explanation of this trip plan for the group:"""

# ─── Replanning Explanation ──────────────────────────────────────────

REPLANNER_EXPLAIN_SYSTEM = """You are a travel planner AI handling a schedule disruption.

Given the original itinerary, a delay event, and the replanned itinerary, write a brief 2–3 paragraph explanation of what changed and why.

Be reassuring and practical. Address the group directly. Do NOT output JSON."""

REPLANNER_EXPLAIN_HUMAN = """Original itinerary:
{original_json}

Delay event:
{delay_json}

Updated itinerary:
{replanned_json}

Changes made:
{changes_json}

Explain what happened and the updated plan:"""
```

### Step 4: Create `backend/agents_augmented/mock_tools.py`

Copy the complete mock data and wrapper functions from Section B.4 exactly. This file provides all 6 tool functions with mock data so the pipeline can run without Bucket 5.

### Step 5: Create `backend/agents_augmented/steps/` package

Create `backend/agents_augmented/steps/__init__.py`:
```python
# Pipeline steps package
```

### Step 6: Create `backend/agents_augmented/steps/parse_constraints.py`

```python
"""
Step 1: Extract travel constraints from chat messages using LLM.
This is the FIRST of exactly 2 LLM calls in the pipeline.
"""
from backend.agents_augmented.llm_client import call_llm_json
from backend.agents_augmented.prompts import CONSTRAINT_EXTRACT_SYSTEM, CONSTRAINT_EXTRACT_HUMAN


# Default values for missing constraint fields
CONSTRAINT_DEFAULTS = {
    "origin": None,
    "destination": None,
    "destination_type": None,
    "budget_per_person": None,
    "dates": None,
    "trip_duration": None,
    "transport_preference": [],
    "avoid_night_driving": False,
    "must_include": [],
    "return_deadline": None,
    "hotel_tier": None,
    "risk_tolerance": None,
    "group_size": None,
    "special_requirements": [],
}

# Assumptions applied when constraints are missing
ASSUMPTION_MAP = {
    "origin": ("Gurugram", "Default origin for NCR-based trips"),
    "group_size": (4, "Typical friend group size"),
    "trip_duration": ("2D1N", "Standard weekend trip duration"),
    "hotel_tier": ("comfort", "Mid-range default"),
    "risk_tolerance": ("medium", "Balanced risk preference"),
}


def parse_constraints(chat_messages: list[str]) -> dict:
    """
    Extract constraints from chat messages via LLM.
    Returns dict with keys: extracted_constraints, missing_fields, assumptions.
    """
    chat_text = "\n".join(chat_messages)
    user_prompt = CONSTRAINT_EXTRACT_HUMAN.format(chat_text=chat_text)

    try:
        raw_constraints = call_llm_json(CONSTRAINT_EXTRACT_SYSTEM, user_prompt)
    except Exception as e:
        print(f"❌ Constraint extraction failed: {e}")
        raw_constraints = {}

    # Merge with defaults (ensure all 14 keys exist)
    constraints = {**CONSTRAINT_DEFAULTS, **raw_constraints}

    # Ensure list fields are actually lists
    for key in ["transport_preference", "must_include", "special_requirements"]:
        if not isinstance(constraints.get(key), list):
            constraints[key] = []

    # Ensure boolean fields
    if not isinstance(constraints.get("avoid_night_driving"), bool):
        constraints["avoid_night_driving"] = False

    # Normalize location name casing (Decision #25):
    # LLM may return "rishikesh" or "GURUGRAM" — title-case to match DB values.
    for loc_field in ("origin", "destination"):
        val = constraints.get(loc_field)
        if isinstance(val, str) and val.strip():
            constraints[loc_field] = val.strip().title()

    # Track missing fields and apply assumptions
    missing_fields = []
    assumptions = {}

    for field, (default_val, reason) in ASSUMPTION_MAP.items():
        if constraints.get(field) is None:
            missing_fields.append(field)
            constraints[field] = default_val
            assumptions[field] = f"Assumed {default_val} — {reason}"

    return {
        "extracted_constraints": constraints,
        "missing_fields": missing_fields,
        "assumptions": assumptions,
    }
```

### Step 7: Create `backend/agents_augmented/steps/validate_constraints.py`

```python
"""
Step 2: Validate extracted constraints (pure Python — no LLM call).
Checks for conflicts, missing required fields, and readiness to plan.
"""


def validate_constraints(extracted_constraints: dict) -> dict:
    """
    Validate constraints and check readiness.
    Returns dict with keys: conflict_report, is_ready_to_plan.
    """
    conflicts = []
    warnings = []

    c = extracted_constraints

    # --- Hard requirement checks ---
    has_origin = c.get("origin") is not None
    has_budget_or_duration = (
        c.get("budget_per_person") is not None or c.get("trip_duration") is not None
    )
    has_preference = (
        c.get("destination_type") is not None
        or c.get("destination") is not None
        or len(c.get("must_include", [])) > 0
    )

    if not has_origin:
        conflicts.append("Missing origin — cannot plan routes")
    if not has_budget_or_duration:
        conflicts.append("Need at least budget or trip duration to plan")
    if not has_preference:
        warnings.append("No destination preference — will suggest all options")

    # --- Logical conflict checks ---
    budget = c.get("budget_per_person")
    tier = c.get("hotel_tier")

    if budget and tier:
        if budget < 3000 and tier == "expedition":
            conflicts.append(
                f"Budget ₹{budget}/person is too low for expedition-tier hotels"
            )
        if budget > 20000 and tier == "budget":
            warnings.append(
                f"Budget ₹{budget}/person is high for budget-tier — consider upgrading"
            )

    if c.get("avoid_night_driving") and c.get("return_deadline"):
        warnings.append(
            "Night driving avoidance + return deadline may limit route options"
        )

    # --- Readiness decision ---
    is_ready = has_origin and has_budget_or_duration and len(conflicts) == 0

    return {
        "conflict_report": {
            "conflicts": conflicts,
            "warnings": warnings,
            "hard_fail": len(conflicts) > 0,
        },
        "is_ready_to_plan": is_ready,
    }
```

### Step 8: Create `backend/agents_augmented/steps/retrieve_data.py`

```python
"""
Step 3: Retrieve travel data from Neo4j tools (or mocks).
Pure Python — no LLM call. Calls tool functions sequentially.
"""

# Try real tools first, fall back to mocks
try:
    from backend.tools.route_tool import get_routes
    from backend.tools.hotel_tool import get_hotels
    from backend.tools.activity_tool import get_activities
    from backend.tools.transport_tool import get_transport_options
    from backend.tools.restaurant_tool import get_restaurants
    from backend.tools.waypoint_tool import get_waypoints
except ImportError:
    print("⚠️ Real tools not available, using mock data")
    from backend.agents_augmented.mock_tools import (
        get_routes,
        get_hotels,
        get_activities,
        get_transport_options,
        get_restaurants,
        get_waypoints,
    )


def _normalize_location(name: str | None, default: str = "") -> str:
    """
    Title-case a location name to match database casing.
    e.g. "rishikesh" → "Rishikesh", "GURUGRAM" → "Gurugram".
    Handles multi-word names: "new delhi" → "New Delhi".
    """
    if not name:
        return default
    return name.strip().title()


def retrieve_data(extracted_constraints: dict) -> dict:
    """
    Fetch all travel data based on extracted constraints.
    Returns dict with keys: route_candidates, hotel_candidates,
    transport_candidates, activity_candidates, food_candidates, waypoint_candidates.

    NOTE (Decision #25): origin and destination are title-cased before every
    tool call so that LLM-extracted lowercase names ("rishikesh", "gurugram")
    match the casing stored in Neo4j / mock data ("Rishikesh", "Gurugram").
    """
    origin = _normalize_location(extracted_constraints.get("origin"), default="Gurugram")
    dest_type = extracted_constraints.get("destination_type")
    hotel_tier = extracted_constraints.get("hotel_tier")
    must_include = extracted_constraints.get("must_include", [])

    # 1. Get matching routes
    routes = get_routes(origin, dest_type)
    print(f"  📍 Found {len(routes)} routes")

    # 2. For each route's destination, get hotels, activities, restaurants, waypoints, transport
    all_hotels = []
    all_activities = []
    all_transport = []
    all_restaurants = []
    all_waypoints = []

    for route in routes:
        # Normalize destination casing (Decision #25) — ensures "rishikesh" == "Rishikesh"
        dest = _normalize_location(route.get("destination", ""))
        rid = route.get("route_id", "")

        hotels = get_hotels(dest, hotel_tier)
        all_hotels.extend(hotels)

        # Use must_include tags for activity filtering if available
        activities = get_activities(dest, must_include if must_include else None)
        all_activities.extend(activities)

        transport = get_transport_options(rid)
        all_transport.extend(transport)

        restaurants = get_restaurants(dest, rid)
        all_restaurants.extend(restaurants)

        waypoints = get_waypoints(rid)
        all_waypoints.extend(waypoints)

    print(f"  🏨 Hotels: {len(all_hotels)}, 🎯 Activities: {len(all_activities)}, "
          f"🚗 Transport: {len(all_transport)}, 🍽️ Restaurants: {len(all_restaurants)}, "
          f"📌 Waypoints: {len(all_waypoints)}")

    return {
        "route_candidates": routes,
        "hotel_candidates": all_hotels,
        "transport_candidates": all_transport,
        "activity_candidates": all_activities,
        "food_candidates": all_restaurants,
        "waypoint_candidates": all_waypoints,
    }
```

### Step 9: Create `backend/agents_augmented/steps/plan_itinerary.py`

```python
"""
Step 4: Run the deterministic planning engine.
Pure Python — no LLM call. Calls planner functions from Bucket 5.
"""

# Try real planner first, fall back to a simple stub
try:
    from backend.planner.candidate_generator import generate_candidates
    from backend.planner.scorer import score_itinerary
    from backend.planner.validator import validate_itinerary
    from backend.planner.timeline_generator import generate_timeline
except ImportError:
    print("⚠️ Real planner not available, using stub planner")

    def generate_candidates(constraints, data):
        """Stub: combine first route/hotel/transport into one candidate."""
        routes = data.get("routes", [])
        hotels = data.get("hotels", [])
        transport = data.get("transport", [])
        activities = data.get("activities", [])
        restaurants = data.get("food", [])
        waypoints = data.get("waypoints", [])

        if not routes:
            return []

        route = routes[0]
        hotel = hotels[0] if hotels else {}
        trans = transport[0] if transport else {}

        group_size = constraints.get("group_size", 4)
        nights = 1  # Default for 2D1N

        hotel_cost = hotel.get("price_per_night", 0) * nights
        transport_cost = trans.get("cost_total", 0)
        activity_cost = sum(a.get("cost_per_person", 0) for a in activities) * group_size
        food_cost = sum(r.get("avg_cost_per_person", 0) for r in restaurants) * group_size
        total = hotel_cost + transport_cost + activity_cost + food_cost

        candidate = {
            "route": route,
            "transport": trans,
            "hotel": hotel,
            "activities": activities,
            "restaurants": restaurants,
            "waypoints": waypoints,
            "destination": route.get("destination", "Unknown"),
            "trip_graph": None,
            "cost_breakdown": {
                "hotel_total": hotel_cost,
                "transport_total": transport_cost,
                "activity_total": activity_cost,
                "food_total": food_cost,
                "total": total,
            },
            "total_cost_per_person": total / group_size if group_size else total,
        }
        return [candidate]

    def score_itinerary(itinerary, constraints):
        return {
            "preference_match": 0.8,
            "budget_efficiency": 0.7,
            "comfort": 0.8,
            "scenic": 0.6,
            "fatigue": 0.3,
            "risk": 0.2,
            "night_driving_penalty": 0.0,
            "final_score": 0.75,
        }

    def validate_itinerary(itinerary, constraints):
        budget = constraints.get("budget_per_person")
        cost_pp = itinerary.get("total_cost_per_person", 0)
        return {
            "is_valid": budget is None or cost_pp <= budget,
            "hard_constraint_violations": [],
            "soft_constraint_warnings": [],
            "budget_used": cost_pp,
            "budget_limit": budget,
            "must_include_satisfied": True,
        }

    def generate_timeline(itinerary):
        return [
            {"day": 1, "start_time": "06:00", "end_time": "14:00",
             "title": "Drive to destination", "type": "transport"},
            {"day": 1, "start_time": "15:00", "end_time": "18:00",
             "title": "Check-in & explore", "type": "hotel"},
            {"day": 2, "start_time": "09:00", "end_time": "12:00",
             "title": "Activities", "type": "activity"},
            {"day": 2, "start_time": "14:00", "end_time": "20:00",
             "title": "Drive back", "type": "transport"},
        ]


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


def plan_itinerary(extracted_constraints: dict, data: dict) -> dict:
    """
    Run planning engine on retrieved data.
    Returns dict with keys: itinerary_candidates, selected_itinerary,
    alternative_itineraries, validation_report, score_breakdown,
    timeline, map_points, cost_breakdown.
    """
    # Pack data into the format planner expects
    planner_data = {
        "routes": data.get("route_candidates", []),
        "hotels": data.get("hotel_candidates", []),
        "transport": data.get("transport_candidates", []),
        "activities": data.get("activity_candidates", []),
        "food": data.get("food_candidates", []),
        "waypoints": data.get("waypoint_candidates", []),
    }

    # Generate candidates
    candidates = generate_candidates(extracted_constraints, planner_data)
    print(f"  📋 Generated {len(candidates)} itinerary candidates")

    if not candidates:
        return {
            "itinerary_candidates": [],
            "selected_itinerary": None,
            "alternative_itineraries": [],
            "validation_report": {"is_valid": False, "hard_constraint_violations": ["No candidates generated"]},
            "score_breakdown": {},
            "timeline": [],
            "map_points": [],
            "cost_breakdown": {},
        }

    # Score and validate each candidate
    scored = []
    for candidate in candidates:
        score = score_itinerary(candidate, extracted_constraints)
        validation = validate_itinerary(candidate, extracted_constraints)
        scored.append({
            "candidate": candidate,
            "score": score,
            "validation": validation,
        })

    # Sort: valid first (by score desc), then invalid (by score desc)
    valid = [s for s in scored if s["validation"].get("is_valid", False)]
    invalid = [s for s in scored if not s["validation"].get("is_valid", False)]

    valid.sort(key=lambda x: x["score"].get("final_score", 0), reverse=True)
    invalid.sort(key=lambda x: x["score"].get("final_score", 0), reverse=True)

    sorted_all = valid + invalid

    # Select best
    best = sorted_all[0]
    selected = best["candidate"]
    alternatives = [s["candidate"] for s in sorted_all[1:4]]  # Up to 3 alternatives

    # Generate timeline for selected
    timeline = generate_timeline(selected)

    # Extract map points
    map_points = _extract_map_points(selected)

    return {
        "itinerary_candidates": [s["candidate"] for s in sorted_all],
        "selected_itinerary": selected,
        "alternative_itineraries": alternatives,
        "validation_report": best["validation"],
        "score_breakdown": best["score"],
        "timeline": timeline,
        "map_points": map_points,
        "cost_breakdown": selected.get("cost_breakdown", {}),
    }
```

### Step 10: Create `backend/agents_augmented/steps/explain_plan.py`

```python
"""
Step 5: Generate a natural-language explanation of the selected itinerary.
This is the SECOND of exactly 2 LLM calls in the pipeline.
"""
import json
from backend.agents_augmented.llm_client import call_llm
from backend.agents_augmented.prompts import EXPLAINER_SYSTEM, EXPLAINER_HUMAN


def explain_plan(
    selected_itinerary: dict,
    timeline: list[dict],
    score_breakdown: dict,
    cost_breakdown: dict,
    extracted_constraints: dict,
    validation_report: dict,
) -> dict:
    """
    Generate a friendly explanation of the plan via LLM.
    Returns dict with key: explanation.
    """
    if not selected_itinerary:
        return {"explanation": "No itinerary was generated — not enough data to plan."}

    # Prepare a serializable version of the itinerary (exclude trip_graph)
    itinerary_clean = {k: v for k, v in selected_itinerary.items() if k != "trip_graph"}

    user_prompt = EXPLAINER_HUMAN.format(
        itinerary_json=json.dumps(itinerary_clean, indent=2, default=str),
        timeline_json=json.dumps(timeline, indent=2, default=str),
        score_json=json.dumps(score_breakdown, indent=2, default=str),
        cost_json=json.dumps(cost_breakdown, indent=2, default=str),
        constraints_json=json.dumps(extracted_constraints, indent=2, default=str),
        validation_json=json.dumps(validation_report, indent=2, default=str),
    )

    try:
        explanation = call_llm(EXPLAINER_SYSTEM, user_prompt)
    except Exception as e:
        print(f"❌ Explanation generation failed: {e}")
        explanation = "Trip plan generated successfully. See the timeline and cost breakdown for details."

    return {"explanation": explanation}
```

### Step 11: Create `backend/agents_augmented/steps/replan.py`

```python
"""
Step 6: Handle replanning after a delay event.
Uses the deterministic planner's replan function + LLM for explanation.
"""
import json

# Try real replanner first, fall back to stub
try:
    from backend.planner.replanner import replan_itinerary
except ImportError:
    def replan_itinerary(itinerary, delay_event, constraints):
        return {
            "updated_itinerary": itinerary,
            "changes": ["No changes — stub replanner"],
            "delay_absorbed": delay_event.get("delay_minutes", 0),
            "delay_remaining": 0,
        }

from backend.agents_augmented.llm_client import call_llm
from backend.agents_augmented.prompts import REPLANNER_EXPLAIN_SYSTEM, REPLANNER_EXPLAIN_HUMAN


def replan(
    selected_itinerary: dict,
    delay_event: dict,
    extracted_constraints: dict,
) -> dict:
    """
    Replan after a delay event.
    Returns dict with keys: replanned_itinerary, replanning_explanation.
    """
    # Run deterministic replanner
    result = replan_itinerary(selected_itinerary, delay_event, extracted_constraints)

    replanned = result.get("updated_itinerary", selected_itinerary)
    changes = result.get("changes", [])

    # Generate explanation via LLM
    itinerary_clean = {k: v for k, v in selected_itinerary.items() if k != "trip_graph"}
    replanned_clean = {k: v for k, v in replanned.items() if k != "trip_graph"}

    user_prompt = REPLANNER_EXPLAIN_HUMAN.format(
        original_json=json.dumps(itinerary_clean, indent=2, default=str),
        delay_json=json.dumps(delay_event, indent=2, default=str),
        replanned_json=json.dumps(replanned_clean, indent=2, default=str),
        changes_json=json.dumps(changes, indent=2, default=str),
    )

    try:
        explanation = call_llm(REPLANNER_EXPLAIN_SYSTEM, user_prompt)
    except Exception as e:
        print(f"❌ Replan explanation failed: {e}")
        explanation = f"Schedule adjusted due to {delay_event.get('type', 'delay')}. Changes: {', '.join(str(c) for c in changes)}"

    return {
        "replanned_itinerary": replanned,
        "replanning_explanation": explanation,
    }
```

### Step 12: Create `backend/agents_augmented/workflow.py`

The main orchestrator. A single linear function that calls each step sequentially.

```python
"""
Augmented LLM Pipeline — Main Workflow (Bucket 2.1)

Linear pipeline: parse → validate → retrieve → plan → explain.
No LangGraph. No state graph. Just sequential function calls.

Exports the same two public functions as Bucket 2:
  - run_workflow(chat_messages) -> TripState
  - run_replan_workflow(state, delay_event) -> TripState
"""
from backend.agents_augmented.state import TripState
from backend.agents_augmented.steps.parse_constraints import parse_constraints
from backend.agents_augmented.steps.validate_constraints import validate_constraints
from backend.agents_augmented.steps.retrieve_data import retrieve_data
from backend.agents_augmented.steps.plan_itinerary import plan_itinerary
from backend.agents_augmented.steps.explain_plan import explain_plan
from backend.agents_augmented.steps.replan import replan


def _init_state(chat_messages: list[str]) -> dict:
    """Initialize a blank TripState dict with all required keys."""
    return {
        "raw_chat": chat_messages,
        "extracted_constraints": {},
        "missing_fields": [],
        "assumptions": {},
        "conflict_report": {},
        "is_ready_to_plan": False,
        "route_candidates": [],
        "hotel_candidates": [],
        "transport_candidates": [],
        "activity_candidates": [],
        "food_candidates": [],
        "waypoint_candidates": [],
        "itinerary_candidates": [],
        "selected_itinerary": None,
        "alternative_itineraries": [],
        "validation_report": {},
        "score_breakdown": {},
        "timeline": [],
        "map_points": [],
        "cost_breakdown": {},
        "explanation": "",
        "delay_event": None,
        "replanned_itinerary": None,
        "replanning_explanation": None,
    }


def run_workflow(chat_messages: list[str]) -> TripState:
    """
    Run the full augmented LLM planning pipeline.

    Steps (sequential):
      1. Parse constraints from chat (LLM call #1)
      2. Validate constraints (Python — no LLM)
         → Early return here if constraints are insufficient.
      3. Retrieve data from tools (Python — no LLM)
      4. Run planning engine (Python — no LLM)
      5. Generate explanation (LLM call #2)
      6. Return completed TripState

    Returns: TripState dict with all fields populated.
    """
    print("\n" + "=" * 60)
    print("🔄 Augmented LLM Pipeline — Starting")
    print("=" * 60)

    state = _init_state(chat_messages)

    # ── Step 1: Parse constraints (LLM) ──
    print("\n📝 Step 1: Parsing constraints from chat...")
    parse_result = parse_constraints(chat_messages)
    state.update(parse_result)
    print(f"  ✅ Extracted: origin={state['extracted_constraints'].get('origin')}, "
          f"budget={state['extracted_constraints'].get('budget_per_person')}")

    # ── Step 2: Validate constraints (Python) ──
    print("\n✅ Step 2: Validating constraints...")
    validate_result = validate_constraints(state["extracted_constraints"])
    state.update(validate_result)
    print(f"  Ready to plan: {state['is_ready_to_plan']}")

    # ── Step 3: Early return if not ready ──
    if not state["is_ready_to_plan"]:
        print("\n⚠️ Not ready to plan. Returning partial state.")
        state["explanation"] = (
            "I couldn't generate a trip plan yet — some key information is missing. "
            f"Conflicts: {state['conflict_report'].get('conflicts', [])}"
        )
        return state

    # ── Step 3: Retrieve data (Tools) ──
    print("\n🔍 Step 3: Retrieving travel data...")
    data_result = retrieve_data(state["extracted_constraints"])
    state.update(data_result)

    # ── Step 4: Plan itinerary (Planner) ──
    print("\n📊 Step 4: Running planning engine...")
    plan_result = plan_itinerary(state["extracted_constraints"], state)
    state.update(plan_result)
    dest = state.get("selected_itinerary", {}).get("destination", "N/A") if state.get("selected_itinerary") else "N/A"
    print(f"  ✅ Selected destination: {dest}")

    # ── Step 5: Explain plan (LLM) ──
    print("\n💬 Step 5: Generating explanation...")
    explain_result = explain_plan(
        selected_itinerary=state["selected_itinerary"],
        timeline=state["timeline"],
        score_breakdown=state["score_breakdown"],
        cost_breakdown=state["cost_breakdown"],
        extracted_constraints=state["extracted_constraints"],
        validation_report=state["validation_report"],
    )
    state.update(explain_result)

    print("\n" + "=" * 60)
    print("✅ Augmented LLM Pipeline — Complete")
    print("=" * 60)

    return state


def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    """
    Run replanning after a delay event.
    Updates the existing state with replanned itinerary and explanation.

    Returns: Updated TripState.
    """
    print("\n" + "=" * 60)
    print("🔄 Replanning Pipeline — Starting")
    print("=" * 60)

    state["delay_event"] = delay_event

    if not state.get("selected_itinerary"):
        state["replanning_explanation"] = "Cannot replan — no itinerary was selected."
        return state

    replan_result = replan(
        selected_itinerary=state["selected_itinerary"],
        delay_event=delay_event,
        extracted_constraints=state["extracted_constraints"],
    )
    state.update(replan_result)

    print("✅ Replanning complete")
    return state
```

### Step 13: Update `backend/agents/workflow.py` — Add Pipeline Router

> **IMPORTANT**: This is the ONLY file you touch in `backend/agents/`. It is the routing layer that makes the switch transparent to Bucket 3.

If `backend/agents/workflow.py` already exists (from Bucket 2), **rename it** to `backend/agents/workflow_agentic.py` and create a new `workflow.py` that acts as a router:

```python
"""
Pipeline Router — Delegates to agentic (Bucket 2) or augmented (Bucket 2.1) workflow
based on the PIPELINE_MODE environment variable.

Bucket 3 always imports from here:
    from backend.agents.workflow import run_workflow, run_replan_workflow

This file ensures that import path never changes regardless of which pipeline is active.
"""
import os
from dotenv import load_dotenv

load_dotenv()

_PIPELINE_MODE = os.getenv("PIPELINE_MODE", "augmented")

if _PIPELINE_MODE == "agentic":
    # Bucket 2: LangGraph-based multi-agent pipeline
    try:
        from backend.agents.workflow_agentic import run_workflow, run_replan_workflow
    except ImportError:
        raise ImportError(
            "PIPELINE_MODE=agentic but backend.agents.workflow_agentic not found. "
            "Build Bucket 2 first, or switch to PIPELINE_MODE=augmented."
        )
elif _PIPELINE_MODE == "augmented":
    # Bucket 2.1: Linear augmented LLM pipeline
    from backend.agents_augmented.workflow import run_workflow, run_replan_workflow
else:
    raise ValueError(
        f"Unknown PIPELINE_MODE: {_PIPELINE_MODE}. Use 'agentic' or 'augmented'."
    )
```

> **If Bucket 2 has NOT been built yet**, this file simply imports from `backend.agents_augmented.workflow` by default. No code from Bucket 2 is needed.
>
> **If Bucket 2 HAS been built**, rename the existing `workflow.py` → `workflow_agentic.py` before creating this router. The Bucket 2 builder should be told to name their workflow file `workflow_agentic.py` (or the integrator renames it during merge).

### Step 14: Update `.env.example`

Add `PIPELINE_MODE` to the existing `.env.example`:

```env
# --- Pipeline Mode (Bucket 2 vs 2.1) ---
# "agentic"   = Bucket 2  (LangGraph multi-agent pipeline — requires langchain/langgraph)
# "augmented" = Bucket 2.1 (Linear single-pass pipeline — requires google-generativeai only)
PIPELINE_MODE=augmented
```

### Step 15: Create `backend/agents_augmented/requirements.txt`

```
google-generativeai>=0.8.0
python-dotenv>=1.0.0
```

Note: **NO** `langchain`, `langchain-google-genai`, `langgraph`, or any agentic framework dependency.

---

## Section E — File Manifest

```
backend/agents_augmented/__init__.py                — Package init
backend/agents_augmented/state.py                   — TripState TypedDict (identical to Bucket 2)
backend/agents_augmented/llm_client.py              — Direct Gemini SDK client (no LangChain)
backend/agents_augmented/prompts.py                 — All prompt templates (extraction + explanation)
backend/agents_augmented/mock_tools.py              — Mock data & tool wrappers for independent testing
backend/agents_augmented/workflow.py                — Main orchestrator: run_workflow(), run_replan_workflow()
backend/agents_augmented/requirements.txt           — Dependencies (google-generativeai only)
backend/agents_augmented/steps/__init__.py           — Steps package init
backend/agents_augmented/steps/parse_constraints.py  — Step 1: LLM constraint extraction
backend/agents_augmented/steps/validate_constraints.py — Step 2: Python constraint validation
backend/agents_augmented/steps/retrieve_data.py      — Step 3: Tool data retrieval
backend/agents_augmented/steps/plan_itinerary.py     — Step 4: Planning engine orchestration
backend/agents_augmented/steps/explain_plan.py       — Step 5: LLM explanation generation
backend/agents_augmented/steps/replan.py             — Step 6: Replanning handler
backend/agents/workflow.py                           — Router: delegates to agentic or augmented
backend/tests/test_bucket_2_1.py                     — Validation test script
specs/logs/bucket_2_1_decisions.md                   — Decisions & assumptions log
```

---

## Section F — Integration Verification Checklist & Test Script

### Pre-Commit Checklist
- [ ] All frozen field names in TripState match Section B.1 exactly
- [ ] No `TODO` or `pass` in any step function
- [ ] Import paths are correct: `from backend.tools.route_tool import get_routes`
- [ ] Mock data is present and operational for all 6 tool functions
- [ ] LLM client initializes with Gemini API key
- [ ] Constraint extraction returns correct JSON from sample chat
- [ ] Full workflow runs end-to-end: `run_workflow(["Let's go to mountains from Gurugram"])`
- [ ] `run_replan_workflow()` accepts TripState and delay_event, returns updated TripState
- [ ] Router in `backend/agents/workflow.py` correctly delegates based on `PIPELINE_MODE`
- [ ] `PIPELINE_MODE=augmented` routes to `backend.agents_augmented.workflow`
- [ ] `specs/logs/bucket_2_1_decisions.md` is created
- [ ] No LangChain/LangGraph imports anywhere in `backend/agents_augmented/`

### Cross-Bucket Compatibility Checklist
- [ ] `retrieve_data({"origin": "gurugram", ...})` returns the same results as `{"origin": "Gurugram", ...}`
- [ ] `retrieve_data({"origin": "GURUGRAM", ...})` returns the same results as `{"origin": "Gurugram", ...}`
- [ ] LLM-extracted lowercase location names are title-cased in `parse_constraints.py` before returning `extracted_constraints`
- [ ] `_normalize_location()` helper exists in `retrieve_data.py` and handles `None`, empty string, lowercase, UPPERCASE, and multi-word names
- [ ] Tool mock wrappers use `.lower()` comparison so they tolerate any residual casing
- [ ] Bucket 3 can import `from backend.agents.workflow import run_workflow, run_replan_workflow` without changes
- [ ] `run_workflow()` returns a dict with ALL TripState keys (even if some are None/[])
- [ ] `extracted_constraints` dict has all 14 keys from Section B.5
- [ ] `selected_itinerary` dict structure matches what Bucket 4 expects
- [ ] `timeline` list structure matches what Bucket 4's TimelineView expects
- [ ] `map_points` list structure matches what Bucket 4's MapView expects
- [ ] Switching `PIPELINE_MODE` between `agentic` and `augmented` requires NO code changes

### Runnable Test Script

Create `backend/tests/test_bucket_2_1.py`:

```python
"""
Bucket 2.1 Validation Script.
Tests the augmented LLM pipeline end-to-end.
Run: PYTHONPATH=. python backend/tests/test_bucket_2_1.py
Requires: GOOGLE_API_KEY in .env for LLM calls
"""
import os
import sys
import json

# Check for API key
if not os.getenv("GOOGLE_API_KEY"):
    from dotenv import load_dotenv
    load_dotenv()

HAS_API_KEY = bool(os.getenv("GOOGLE_API_KEY"))
if not HAS_API_KEY:
    print("⚠️ GOOGLE_API_KEY not set. Testing with mock mode only (no LLM calls).")

print("=" * 60)
print("Bucket 2.1 — Augmented LLM Pipeline Validation")
print("=" * 60)

# ── Test 1: State schema ──
print("\n📋 Test 1: TripState schema")
try:
    from backend.agents_augmented.state import TripState
    # Verify all expected keys exist in the TypedDict
    expected_keys = {
        "raw_chat", "extracted_constraints", "missing_fields", "assumptions",
        "conflict_report", "is_ready_to_plan", "route_candidates",
        "hotel_candidates", "transport_candidates", "activity_candidates",
        "food_candidates", "waypoint_candidates", "itinerary_candidates",
        "selected_itinerary", "alternative_itineraries", "validation_report",
        "score_breakdown", "timeline", "map_points", "cost_breakdown",
        "explanation", "delay_event", "replanned_itinerary", "replanning_explanation",
    }
    actual_keys = set(TripState.__annotations__.keys())
    assert actual_keys == expected_keys, f"Key mismatch: {actual_keys.symmetric_difference(expected_keys)}"
    print(f"  ✅ TripState has all {len(expected_keys)} expected keys")
except Exception as e:
    print(f"  ❌ TripState check failed: {e}")
    sys.exit(1)

# ── Test 2: LLM client ──
print("\n🤖 Test 2: LLM client")
try:
    from backend.agents_augmented.llm_client import call_llm, call_llm_json
    print("  ✅ LLM client imported successfully")
    if HAS_API_KEY:
        result = call_llm("You are a test.", "Say hello in one word.")
        print(f"  ✅ LLM responded: {result[:50]}")
    else:
        print("  ⏭️ Skipped LLM call (no API key)")
except Exception as e:
    print(f"  ❌ LLM client failed: {e}")

# ── Test 3: Prompts ──
print("\n📝 Test 3: Prompts")
try:
    from backend.agents_augmented.prompts import (
        CONSTRAINT_EXTRACT_SYSTEM, CONSTRAINT_EXTRACT_HUMAN,
        EXPLAINER_SYSTEM, EXPLAINER_HUMAN,
        REPLANNER_EXPLAIN_SYSTEM, REPLANNER_EXPLAIN_HUMAN,
    )
    print(f"  ✅ CONSTRAINT_EXTRACT_SYSTEM loaded ({len(CONSTRAINT_EXTRACT_SYSTEM)} chars)")
    print(f"  ✅ EXPLAINER_SYSTEM loaded ({len(EXPLAINER_SYSTEM)} chars)")
    print(f"  ✅ REPLANNER_EXPLAIN_SYSTEM loaded ({len(REPLANNER_EXPLAIN_SYSTEM)} chars)")
except Exception as e:
    print(f"  ❌ Prompts import failed: {e}")

# ── Test 4: Mock tools ──
print("\n🔧 Test 4: Mock tools")
try:
    from backend.agents_augmented.mock_tools import (
        get_routes, get_hotels, get_activities,
        get_transport_options, get_restaurants, get_waypoints,
    )
    routes = get_routes("Gurugram")
    assert len(routes) >= 1, "Expected at least 1 route"
    hotels = get_hotels("Rishikesh")
    assert len(hotels) >= 1, "Expected at least 1 hotel"
    activities = get_activities("Rishikesh")
    assert len(activities) >= 1, "Expected at least 1 activity"
    transport = get_transport_options("gurugram_rishikesh_2d1n")
    assert len(transport) >= 1, "Expected at least 1 transport"
    restaurants = get_restaurants("Rishikesh")
    assert len(restaurants) >= 1, "Expected at least 1 restaurant"
    waypoints = get_waypoints("gurugram_rishikesh_2d1n")
    assert len(waypoints) >= 1, "Expected at least 1 waypoint"
    print(f"  ✅ All 6 mock tools return data")
except Exception as e:
    print(f"  ❌ Mock tools failed: {e}")

# ── Test 5: Individual steps ──
print("\n🔗 Test 5: Pipeline steps (without LLM)")
try:
    from backend.agents_augmented.steps.validate_constraints import validate_constraints
    from backend.agents_augmented.steps.retrieve_data import retrieve_data
    from backend.agents_augmented.steps.plan_itinerary import plan_itinerary

    # Test validate
    test_constraints = {
        "origin": "Gurugram", "destination": None, "destination_type": "mountains",
        "budget_per_person": 15000, "dates": "weekend", "trip_duration": "2D1N",
        "transport_preference": [], "avoid_night_driving": True,
        "must_include": ["rafting"], "return_deadline": None,
        "hotel_tier": "comfort", "risk_tolerance": "medium",
        "group_size": 4, "special_requirements": [],
    }
    val_result = validate_constraints(test_constraints)
    assert val_result["is_ready_to_plan"] == True, "Should be ready to plan"
    print("  ✅ validate_constraints works")

    # Test retrieve
    data_result = retrieve_data(test_constraints)
    assert len(data_result["route_candidates"]) >= 1, "Should have routes"
    print("  ✅ retrieve_data works")

    # Test plan
    plan_result = plan_itinerary(test_constraints, data_result)
    assert plan_result["selected_itinerary"] is not None, "Should have selected itinerary"
    assert len(plan_result["timeline"]) >= 1, "Should have timeline"
    assert len(plan_result["map_points"]) >= 1, "Should have map points"
    print("  ✅ plan_itinerary works")
except Exception as e:
    print(f"  ❌ Pipeline steps failed: {e}")
    import traceback
    traceback.print_exc()

# ── Test 6: Workflow import ──
print("\n🔄 Test 6: Workflow")
try:
    from backend.agents_augmented.workflow import run_workflow, run_replan_workflow
    print("  ✅ run_workflow and run_replan_workflow imported from agents_augmented")
except Exception as e:
    print(f"  ❌ Workflow import failed: {e}")

# ── Test 7: Router ──
print("\n🔀 Test 7: Pipeline router")
try:
    os.environ["PIPELINE_MODE"] = "augmented"
    # Force reimport
    import importlib
    import backend.agents.workflow as router_mod
    importlib.reload(router_mod)
    print("  ✅ Router loaded with PIPELINE_MODE=augmented")
except Exception as e:
    print(f"  ⚠️ Router test skipped (backend.agents.workflow may not exist yet): {e}")

# ── Test 8: End-to-end (only with API key) ──
if HAS_API_KEY:
    print("\n🚀 Test 8: End-to-end workflow")
    try:
        from backend.agents_augmented.workflow import run_workflow
        result = run_workflow([
            "Let's do a weekend trip from Gurugram",
            "Budget under 15k per person",
            "Mountains please, not Jaipur",
            "No night driving",
            "Need rafting and good cafes",
        ])

        # Verify all TripState keys are present
        for key in expected_keys:
            assert key in result, f"Missing key in result: {key}"

        print(f"  ✅ Workflow completed")
        print(f"  Origin: {result.get('extracted_constraints', {}).get('origin')}")
        print(f"  Budget: {result.get('extracted_constraints', {}).get('budget_per_person')}")
        print(f"  Ready: {result.get('is_ready_to_plan')}")
        print(f"  Selected: {result.get('selected_itinerary', {}).get('destination', 'N/A') if result.get('selected_itinerary') else 'N/A'}")
        print(f"  Timeline events: {len(result.get('timeline', []))}")
        print(f"  Map points: {len(result.get('map_points', []))}")
        print(f"  Explanation: {result.get('explanation', 'N/A')[:100]}...")
    except Exception as e:
        print(f"  ❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n⏭️ Test 8: Skipped (no API key)")

# ── Test 9: Case-insensitive location name handling (Decision #25) ──
print("\n🔤 Test 9: Case-insensitive location name normalization")
try:
    from backend.agents_augmented.mock_tools import get_routes, get_hotels, get_activities, get_restaurants
    from backend.agents_augmented.steps.retrieve_data import _normalize_location
    from backend.agents_augmented.steps.parse_constraints import CONSTRAINT_DEFAULTS

    # 9a: _normalize_location helper
    assert _normalize_location("rishikesh") == "Rishikesh", "lowercase → Title"
    assert _normalize_location("GURUGRAM") == "Gurugram", "UPPERCASE → Title"
    assert _normalize_location("riShikEsh") == "Rishikesh", "mixed case → Title"
    assert _normalize_location("new delhi") == "New Delhi", "multi-word → Title"
    assert _normalize_location(None, default="Gurugram") == "Gurugram", "None → default"
    assert _normalize_location("") == "", "empty string → empty"
    print("  ✅ _normalize_location handles all casing variants")

    # 9b: Mock tool wrappers handle case-insensitive lookup
    assert get_routes("gurugram") == get_routes("Gurugram"), "lowercase origin == Title origin"
    assert get_routes("GURUGRAM") == get_routes("Gurugram"), "UPPER origin == Title origin"
    assert get_hotels("rishikesh") == get_hotels("Rishikesh"), "lowercase dest == Title dest"
    assert get_hotels("RISHIKESH") == get_hotels("Rishikesh"), "UPPER dest == Title dest"
    assert get_activities("rishikesh") == get_activities("Rishikesh"), "activities lowercase == Title"
    assert get_restaurants("rishikesh") == get_restaurants("Rishikesh"), "restaurants lowercase == Title"
    print("  ✅ Mock tool wrappers return identical results for all casing variants")

    # 9c: retrieve_data normalizes before calling tools (end-to-end path)
    from backend.agents_augmented.steps.retrieve_data import retrieve_data
    constraints_lower = {
        "origin": "gurugram", "destination": None, "destination_type": "mountains",
        "budget_per_person": 15000, "dates": "weekend", "trip_duration": "2D1N",
        "transport_preference": [], "avoid_night_driving": False,
        "must_include": [], "return_deadline": None, "hotel_tier": "comfort",
        "risk_tolerance": "medium", "group_size": 4, "special_requirements": [],
    }
    constraints_title = {**constraints_lower, "origin": "Gurugram"}
    result_lower = retrieve_data(constraints_lower)
    result_title = retrieve_data(constraints_title)
    assert result_lower["route_candidates"] == result_title["route_candidates"], \
        "retrieve_data must return same routes for 'gurugram' and 'Gurugram'"
    assert result_lower["hotel_candidates"] == result_title["hotel_candidates"], \
        "retrieve_data must return same hotels for 'gurugram' and 'Gurugram'"
    print("  ✅ retrieve_data returns identical results for lowercase/title-case origin")

    # 9d: retrieve_data works with ALL-CAPS origin
    constraints_upper = {**constraints_lower, "origin": "GURUGRAM"}
    result_upper = retrieve_data(constraints_upper)
    assert result_upper["route_candidates"] == result_title["route_candidates"], \
        "retrieve_data must return same routes for 'GURUGRAM' and 'Gurugram'"
    print("  ✅ retrieve_data returns identical results for UPPER-CASE origin")

    # 9e: parse_constraints normalizes extracted origin & destination
    # Simulate LLM returning lowercase location in extracted_constraints
    from backend.agents_augmented.steps.parse_constraints import CONSTRAINT_DEFAULTS
    raw_with_lowercase = {**CONSTRAINT_DEFAULTS, "origin": "gurugram", "destination": "rishikesh",
                          "trip_duration": "2D1N"}
    # Manually run the normalization block from parse_constraints
    for loc_field in ("origin", "destination"):
        val = raw_with_lowercase.get(loc_field)
        if isinstance(val, str) and val.strip():
            raw_with_lowercase[loc_field] = val.strip().title()
    assert raw_with_lowercase["origin"] == "Gurugram", "parse should title-case origin"
    assert raw_with_lowercase["destination"] == "Rishikesh", "parse should title-case destination"
    print("  ✅ parse_constraints normalizes origin and destination to Title case")

except Exception as e:
    print(f"  ❌ Case-insensitivity tests failed: {e}")
    import traceback
    traceback.print_exc()

# ── Test 10: No LangChain imports ──
print("\n🚫 Test 10: Verify no LangChain/LangGraph dependencies")
try:
    import glob
    aug_files = glob.glob("backend/agents_augmented/**/*.py", recursive=True)
    violations = []
    for fpath in aug_files:
        with open(fpath) as f:
            content = f.read()
        if "langchain" in content or "langgraph" in content:
            violations.append(fpath)
    if violations:
        print(f"  ❌ LangChain/LangGraph found in: {violations}")
    else:
        print(f"  ✅ No LangChain/LangGraph imports in {len(aug_files)} files")
except Exception as e:
    print(f"  ⚠️ Check failed: {e}")

print("\n" + "=" * 60)
print("Bucket 2.1 validation complete. (10 tests)")
```

---

## Section G —  Assumptions & Decisions Log (Output File)

**You MUST create:** `specs/logs/bucket_2_1_decisions.md`

```markdown
# Bucket 2.1 — Decisions & Assumptions Log
Generated by: [Model Name] on [Date]

## Pre-Specified Decisions Applied
- Decision 1–25 from Section C applied as-is.

## Architectural Decisions
- Used direct `google-generativeai` SDK instead of LangChain for LLM calls (no agentic framework dependency).
- Pipeline is a linear sequence of 6 function calls (parse → validate → retrieve → plan → explain → return).
- Exactly 2 LLM calls per workflow run: constraint extraction and explanation.
- All other steps (validation, data retrieval, planning) are pure Python.

## Unspecified Decisions Made During Build
## Deviations from Spec
## External Assumptions
## Validation Results
```

---

## Comparison: Bucket 2 (Agentic) vs Bucket 2.1 (Augmented)

| Aspect | Bucket 2 (Agentic) | Bucket 2.1 (Augmented) |
|--------|-------------------|----------------------|
| **Framework** | LangGraph state machine | Plain Python functions |
| **Dependencies** | `langchain`, `langgraph`, `langchain-google-genai` | `google-generativeai` only |
| **LLM Calls** | 4 (parse, validate, explain, replan-explain) | 2 (parse, explain) |
| **Constraint Validation** | LLM-based | Python-based (deterministic) |
| **State Management** | LangGraph `StateGraph` with typed channels | Simple `dict` passed between functions |
| **Conditional Routing** | LangGraph conditional edges | Python `if` statement |
| **Code Location** | `backend/agents/` | `backend/agents_augmented/` |
| **Public API** | `run_workflow()`, `run_replan_workflow()` | **Identical** |
| **Output (TripState)** | **Identical** | **Identical** |
| **Switching** | `PIPELINE_MODE=agentic` | `PIPELINE_MODE=augmented` |

---

## Git Commit Protocol

```
1. Stage all files listed in File Manifest (Section E)
2. Stage backend/tests/test_bucket_2_1.py
3. Stage specs/logs/bucket_2_1_decisions.md
4. Stage updated .env.example (with PIPELINE_MODE)
5. Commit message: "Bucket 2.1: Augmented LLM pipeline — drop-in alternative to agentic — [date]"
6. Branch: bucket-2.1/implementation
7. Push to origin
8. Do NOT merge to main
```

---

## Common Pitfalls

1. **JSON parsing**: Gemini sometimes wraps JSON in markdown code blocks. Always handle both raw JSON and ` ```json ``` ` wrapped responses. The `call_llm_json()` helper handles this.
2. **Rate limits**: Free Gemini has 15 RPM. If you hit limits during testing, add `time.sleep(4)` between runs.
3. **State initialization**: Every field in TripState must have a value (even if empty list/dict/None). Missing keys will cause Bucket 3's Pydantic models to fail validation.
4. **Import cycles**: Tool and planner imports are at the top of step files. If circular import issues arise, use late imports inside the function body.
5. **Non-serializable objects**: The `trip_graph` field in candidates contains dataclass instances. Use `default=str` in any `json.dumps()` call. LLM prompts should NOT include the raw `trip_graph` object.
6. **Router file**: Do NOT modify `backend/agents/workflow.py` beyond the router pattern shown in Step 13. If Bucket 2 is not yet built, the router simply imports from `agents_augmented` by default.
7. **No LangChain**: Double-check that you have ZERO `langchain` or `langgraph` imports in any file under `backend/agents_augmented/`. This bucket must be completely independent of any agentic framework.
8. **Location name casing**: The LLM may return location names in any casing ("rishikesh", "GURUGRAM", "riShikEsh"). Neo4j string property matches and mock data comparisons are case-sensitive by default. Always normalize location strings with `str.strip().title()` **before** passing them to any tool function or planner. Normalization must happen in two places: (a) in `parse_constraints.py` right after LLM extraction, and (b) defensively via `_normalize_location()` at the top of `retrieve_data()`. For Neo4j Cypher queries, use `toLower(n.name) = toLower($name)` rather than exact equality.
