# Bucket 3: Backend API & Integration — LLM-Ready Spec

> **Generated for**: Distributed LLM execution (Claude / Gemini session)
> **Priority**: P1 — Can start immediately with stub endpoints
> **Reference**: This spec is self-contained. You may also read `specs/MASTER_SPEC.md` for full project context.

---

## Section A — Project Context

**TripGraph AI** is a GenAI-agentic group travel planner that converts WhatsApp-style group chat into structured, constraint-aware itineraries. It uses a Neo4j knowledge graph, a LangGraph agentic pipeline, a deterministic Python planning engine, and a React frontend.

**Your role (Bucket 3):** Build the **FastAPI backend** that serves as the HTTP bridge between the React frontend (JavaScript, runs in browser) and the Python backend (LangGraph agents, Neo4j, planner). You create REST endpoints, Pydantic request/response models, configuration management, Docker Compose setup, and integration wiring.

React runs in the browser. LangGraph and the planner run in Python on the server. **They cannot communicate directly.** FastAPI provides the HTTP endpoints the frontend calls.

---

## Section B — 🔒 Frozen Interface Contracts

### B.1 TripState TypedDict (from Bucket 2)

This is the complete state object that flows through the agentic pipeline. Your Pydantic response models must map fields FROM this state TO the API response JSON.

```python
from typing import TypedDict, List, Dict, Any, Optional

class TripState(TypedDict):
    # Input
    raw_chat: List[str]

    # Constraint extraction
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

### B.2 Workflow Import Paths (Frozen)

```python
from backend.agents.workflow import run_workflow, run_replan_workflow
```

**Function signatures:**
```python
def run_workflow(chat_messages: list[str]) -> TripState:
    """Run the full planning pipeline. Returns completed TripState."""

def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    """Run replanning after a delay event. Returns updated TripState."""
```

### B.3 API Endpoints (3 Total)

#### POST `/api/parse-chat`
**Request:**
```json
{
  "chat_messages": ["Let's go from Gurugram", "Budget under 15k", "Mountains please"]
}
```

**Response:**
```json
{
  "extracted_constraints": {
    "origin": "Gurugram",
    "destination": null,
    "destination_type": "mountains",
    "budget_per_person": 15000,
    "dates": null,
    "trip_duration": "weekend",
    "transport_preference": [],
    "avoid_night_driving": true,
    "must_include": ["rafting", "cafes"],
    "return_deadline": "Monday morning",
    "hotel_tier": "comfort",
    "risk_tolerance": "medium",
    "group_size": 4,
    "special_requirements": []
  },
  "missing_fields": [],
  "assumptions": {
    "group_size": "4 (default)",
    "risk_tolerance": "medium (default)"
  },
  "conflict_report": {
    "conflicts": []
  }
}
```

#### POST `/api/generate-itinerary`
**Request:**
```json
{
  "constraints": {
    "origin": "Gurugram",
    "destination_type": "mountains",
    "budget_per_person": 15000,
    "avoid_night_driving": true,
    "must_include": ["rafting", "cafes"],
    "return_deadline": "Monday morning",
    "hotel_tier": "comfort",
    "group_size": 4
  }
}
```

**Response:**
```json
{
  "recommended_itinerary": {
    "route": {"route_id": "gurugram_rishikesh_2d1n", "origin": "Gurugram", "destination": "Rishikesh", "distance_km": 260},
    "transport": {"mode": "cab_with_driver", "cost_total": 9500},
    "hotel": {"name": "Riverside Comfort Stay", "price_per_night": 4200},
    "activities": [{"name": "White Water Rafting", "cost_per_person": 1800}],
    "total_cost_per_person": 10275,
    "cost_breakdown": {
      "transport": 2375,
      "hotel": 1050,
      "activities": 1800,
      "food": 1050,
      "miscellaneous": 2000,
      "total": 10275
    }
  },
  "alternatives": [],
  "validation_report": {
    "is_valid": true,
    "hard_constraint_violations": [],
    "soft_constraint_warnings": []
  },
  "score_breakdown": {
    "preference_match": 25,
    "budget_efficiency": 6.3,
    "comfort": 12,
    "scenic": 7,
    "fatigue": 10.5,
    "risk": 6,
    "night_driving_penalty": 0,
    "final_score": 66.8
  },
  "timeline": [
    {"day": 1, "start_time": "06:00", "end_time": "09:00", "title": "Drive from Gurugram", "type": "travel"},
    {"day": 1, "start_time": "09:00", "end_time": "09:45", "title": "Breakfast at Murthal", "type": "meal"},
    {"day": 1, "start_time": "09:45", "end_time": "13:00", "title": "Continue to Rishikesh", "type": "travel"},
    {"day": 1, "start_time": "13:00", "end_time": "14:15", "title": "Lunch at Little Buddha Cafe", "type": "meal", "cost": 600},
    {"day": 1, "start_time": "14:30", "end_time": "16:00", "title": "Check-in at Riverside Comfort Stay", "type": "hotel", "cost": 1050},
    {"day": 1, "start_time": "18:30", "end_time": "19:30", "title": "Ganga Aarti", "type": "activity"},
    {"day": 1, "start_time": "20:00", "end_time": "21:00", "title": "Dinner", "type": "meal"},
    {"day": 2, "start_time": "07:30", "end_time": "08:15", "title": "Breakfast", "type": "meal"},
    {"day": 2, "start_time": "09:00", "end_time": "12:00", "title": "White Water Rafting", "type": "activity", "cost": 1800},
    {"day": 2, "start_time": "12:30", "end_time": "13:30", "title": "Freshen up", "type": "rest"},
    {"day": 2, "start_time": "13:30", "end_time": "14:30", "title": "Lunch", "type": "meal"},
    {"day": 2, "start_time": "15:00", "end_time": "21:30", "title": "Return to Gurugram", "type": "travel"}
  ],
  "map_points": [
    {"lat": 28.4595, "lng": 77.0266, "label": "Gurugram", "type": "origin"},
    {"lat": 29.0281, "lng": 77.0474, "label": "Murthal Dhaba", "type": "waypoint"},
    {"lat": 30.0869, "lng": 78.2676, "label": "Rishikesh", "type": "destination"},
    {"lat": 30.0869, "lng": 78.2676, "label": "Riverside Comfort Stay", "type": "hotel"},
    {"lat": 30.1159, "lng": 78.3127, "label": "White Water Rafting", "type": "activity"}
  ],
  "cost_breakdown": {
    "transport": 2375,
    "hotel": 1050,
    "activities": 1800,
    "food": 1050,
    "miscellaneous": 2000,
    "total": 10275,
    "budget_limit": 15000
  },
  "explanation": "This itinerary was selected because it stays within the ₹15,000 budget, avoids night driving, includes rafting and cafe time near the Ganges, and returns by Sunday evening."
}
```

#### POST `/api/simulate-delay`
**Request:**
```json
{
  "delay_type": "departure_delay",
  "delay_minutes": 90,
  "constraints": {"origin": "Gurugram", "budget_per_person": 15000},
  "selected_itinerary": { "...same structure as recommended_itinerary above..." }
}
```

**Response:**
```json
{
  "updated_itinerary": { "...same structure as recommended_itinerary with adjusted timeline..." },
  "changes": [
    "Breakfast shortened by 22 minutes",
    "Lunch shortened by 15 minutes",
    "Rest period reduced by 30 minutes"
  ],
  "validation_report": {
    "is_valid": true,
    "hard_constraint_violations": [],
    "soft_constraint_warnings": ["Rest time below recommended minimum"]
  },
  "explanation": "The revised plan absorbs the 90-minute delay by compressing flexible events. Rafting and return journey are preserved."
}
```

### B.4 Timeline Event Dict Shape

Each event in the `timeline` array has this structure:
```
day: int              # 1 or 2
start_time: str       # "HH:MM" format
end_time: str         # "HH:MM" format
title: str            # Human-readable event name
type: str             # "travel" | "meal" | "hotel" | "activity" | "rest"
cost: int             # Optional. Per-person cost in INR. Omitted if 0.
```

### B.5 Map Point Dict Shape

Each point in the `map_points` array:
```
lat: float
lng: float
label: str            # Human-readable name
type: str             # "origin" | "waypoint" | "destination" | "hotel" | "activity"
```

### B.6 Environment Variables (from `.env.example`)

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tripgraph123
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_TEMPERATURE=0
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
VITE_API_URL=http://localhost:8000
```

---

## Section C — Decisions & Defaults (Pre-Made)

| # | Decision | Value |
|---|----------|-------|
| 1 | FastAPI port | `8000` |
| 2 | CORS allowed origins | `http://localhost:5173,http://localhost:3000` |
| 3 | API prefix | All routes under `/api/` |
| 4 | Error response format | `{"error": "<message>", "detail": "<stacktrace or context>"}` with HTTP 500 |
| 5 | What if Neo4j is unreachable? | Endpoints return HTTP 503 with `"error": "Service unavailable: database connection failed"` |
| 6 | What if LLM call fails? | Endpoints return HTTP 502 with `"error": "LLM service error"` and the exception message in `detail` |
| 7 | What if workflow raises? | Catch all exceptions, return HTTP 500. Log the full traceback with `import traceback`. |
| 8 | Health check endpoint | `GET /health` returns `{"status": "healthy"}` |
| 9 | Root endpoint | `GET /` returns `{"message": "TripGraph AI API is running", "docs": "/docs"}` |
| 10 | Swagger docs | Auto-generated at `/docs` (FastAPI default) |
| 11 | Response serialization for non-JSON types | Use `default=str` in any `json.dumps()` call to handle datetime, dataclass, etc. |
| 12 | Stub mode | Each endpoint has a commented-out stub response block. Uncomment for frontend dev without Bucket 2. |
| 13 | How `/generate-itinerary` handles constraints | Convert constraints dict to synthetic chat messages, pass to `run_workflow()`. Include a `_constraints_to_chat()` helper. |
| 14 | Docker Neo4j image | `neo4j:5-community` with auth `neo4j/tripgraph123` |
| 15 | Docker Compose version | `version: "3.8"` |
| 16 | Backend Dockerfile | Simple Python 3.11 image, `pip install -r requirements.txt`, `uvicorn backend.main:app` |
| 17 | Pydantic version | v2 (`pydantic>=2.0`) |
| 18 | FastAPI version | `fastapi>=0.115.0` |
| 19 | CORS methods/headers | Allow all (`["*"]`) |
| 20 | SimulateDelay `delay_minutes` range | 15–300 minutes |

---

## Section D — Step-by-Step Build Instructions

### Step 1: Create `backend/config.py`

```python
"""
Central configuration loaded from environment variables.
All env var names match .env.example exactly.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment."""

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "tripgraph123")

    # LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")


settings = Settings()
```

### Step 2: Create `backend/models/requests.py`

Full Pydantic request models with type hints, Field descriptions, and example values:

```python
"""Pydantic models for API request bodies."""
from pydantic import BaseModel, Field
from typing import Optional


class ParseChatRequest(BaseModel):
    """Request body for POST /api/parse-chat."""

    chat_messages: list[str] = Field(
        ...,
        description="List of group chat messages to parse",
        min_length=1,
        json_schema_extra={"examples": [["Let's go from Gurugram", "Budget under 15k", "Mountains please"]]},
    )


class GenerateItineraryRequest(BaseModel):
    """Request body for POST /api/generate-itinerary."""

    constraints: dict = Field(
        ...,
        description="Extracted constraints dict (from /parse-chat or manually provided)",
        json_schema_extra={"examples": [{
            "origin": "Gurugram",
            "destination_type": "mountains",
            "budget_per_person": 15000,
            "avoid_night_driving": True,
            "must_include": ["rafting", "cafes"],
            "hotel_tier": "comfort",
            "group_size": 4,
        }]},
    )


class SimulateDelayRequest(BaseModel):
    """Request body for POST /api/simulate-delay."""

    delay_type: str = Field(
        ...,
        description="Type of delay event",
        json_schema_extra={"examples": ["departure_delay"]},
    )
    delay_minutes: int = Field(
        ...,
        ge=15,
        le=300,
        description="Delay duration in minutes (15-300)",
        json_schema_extra={"examples": [90]},
    )
    constraints: Optional[dict] = Field(
        None,
        description="The trip constraints used for the original itinerary",
    )
    selected_itinerary: Optional[dict] = Field(
        None,
        description="The full selected itinerary object to replan",
    )
```

### Step 3: Create `backend/models/responses.py`

```python
"""Pydantic models for API responses."""
from pydantic import BaseModel, Field
from typing import Optional, Any


class ParseChatResponse(BaseModel):
    """Response for POST /api/parse-chat."""

    extracted_constraints: dict = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: dict = Field(default_factory=dict)
    conflict_report: dict = Field(default_factory=dict)


class ItineraryResponse(BaseModel):
    """Response for POST /api/generate-itinerary."""

    recommended_itinerary: Optional[dict] = None
    alternatives: list[dict] = Field(default_factory=list)
    validation_report: dict = Field(default_factory=dict)
    score_breakdown: dict = Field(default_factory=dict)
    timeline: list[dict] = Field(default_factory=list)
    map_points: list[dict] = Field(default_factory=list)
    cost_breakdown: dict = Field(default_factory=dict)
    explanation: str = ""


class DelaySimulationResponse(BaseModel):
    """Response for POST /api/simulate-delay."""

    updated_itinerary: Optional[dict] = None
    changes: list[str] = Field(default_factory=list)
    validation_report: dict = Field(default_factory=dict)
    explanation: str = ""


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str = ""
```

### Step 4: Create `backend/models/__init__.py`

```python
# Models package
```

### Step 5: Create `backend/api/__init__.py`

```python
# API routes package
```

### Step 6: Create `backend/api/chat_routes.py`

```python
"""POST /api/parse-chat — Parse group chat and extract constraints."""
import traceback
from fastapi import APIRouter, HTTPException
from backend.models.requests import ParseChatRequest
from backend.models.responses import ParseChatResponse

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/parse-chat", response_model=ParseChatResponse)
async def parse_chat(request: ParseChatRequest) -> ParseChatResponse:
    """
    Parse group chat messages and extract structured trip constraints.
    Uses the Chat Parser + Constraint Validator agents from Bucket 2.
    """
    try:
        # --- STUB MODE (uncomment for frontend dev without Bucket 2) ---
        # return ParseChatResponse(
        #     extracted_constraints={
        #         "origin": "Gurugram",
        #         "destination_type": "mountains",
        #         "budget_per_person": 15000,
        #         "avoid_night_driving": True,
        #         "must_include": ["rafting", "cafes"],
        #         "return_deadline": "Monday morning",
        #         "hotel_tier": "comfort",
        #         "group_size": 4,
        #     },
        #     missing_fields=[],
        #     assumptions={"group_size": "4 (default)", "risk_tolerance": "medium (default)"},
        #     conflict_report={"conflicts": []},
        # )

        # --- REAL MODE ---
        from backend.agents.workflow import run_workflow

        result = run_workflow(request.chat_messages)
        return ParseChatResponse(
            extracted_constraints=result.get("extracted_constraints", {}),
            missing_fields=result.get("missing_fields", []),
            assumptions=result.get("assumptions", {}),
            conflict_report=result.get("conflict_report", {}),
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 7: Create `backend/api/itinerary_routes.py`

```python
"""POST /api/generate-itinerary — Generate and score itineraries."""
import traceback
from fastapi import APIRouter, HTTPException
from backend.models.requests import GenerateItineraryRequest
from backend.models.responses import ItineraryResponse

router = APIRouter(prefix="/api", tags=["Itinerary"])


@router.post("/generate-itinerary", response_model=ItineraryResponse)
async def generate_itinerary(request: GenerateItineraryRequest) -> ItineraryResponse:
    """
    Generate candidate itineraries from constraints.
    Runs the full agentic pipeline: data retrieval → planning → scoring → explanation.
    """
    try:
        # --- STUB MODE (uncomment for frontend dev without Bucket 2) ---
        # return ItineraryResponse(
        #     recommended_itinerary={
        #         "route": {"route_id": "gurugram_rishikesh_2d1n", "destination": "Rishikesh"},
        #         "total_cost_per_person": 10275,
        #     },
        #     timeline=[
        #         {"day": 1, "start_time": "06:00", "end_time": "09:00",
        #          "title": "Drive from Gurugram", "type": "travel"},
        #     ],
        #     explanation="Stub response for frontend development.",
        # )

        # --- REAL MODE ---
        from backend.agents.workflow import run_workflow

        chat_summary = _constraints_to_chat(request.constraints)
        result = run_workflow(chat_summary)

        return ItineraryResponse(
            recommended_itinerary=result.get("selected_itinerary"),
            alternatives=result.get("alternative_itineraries", []),
            validation_report=result.get("validation_report", {}),
            score_breakdown=result.get("score_breakdown", {}),
            timeline=result.get("timeline", []),
            map_points=result.get("map_points", []),
            cost_breakdown=result.get("cost_breakdown", {}),
            explanation=result.get("explanation", ""),
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _constraints_to_chat(constraints: dict) -> list[str]:
    """Convert a constraints dict into synthetic chat messages for the workflow."""
    messages: list[str] = []
    if constraints.get("origin"):
        messages.append(f"We want to go from {constraints['origin']}")
    if constraints.get("destination_type"):
        messages.append(f"Prefer {constraints['destination_type']} destinations")
    if constraints.get("budget_per_person"):
        messages.append(f"Budget under {constraints['budget_per_person']} per person")
    if constraints.get("avoid_night_driving"):
        messages.append("No night driving please")
    if constraints.get("must_include"):
        messages.append(f"Must include: {', '.join(constraints['must_include'])}")
    if constraints.get("return_deadline"):
        messages.append(f"Need to return by {constraints['return_deadline']}")
    if constraints.get("hotel_tier"):
        messages.append(f"Hotel preference: {constraints['hotel_tier']}")
    if constraints.get("group_size"):
        messages.append(f"Group of {constraints['group_size']} people")
    return messages or ["Plan a trip"]
```

### Step 8: Create `backend/api/replanner_routes.py`

```python
"""POST /api/simulate-delay — Simulate a delay and replan."""
import traceback
from fastapi import APIRouter, HTTPException
from backend.models.requests import SimulateDelayRequest
from backend.models.responses import DelaySimulationResponse

router = APIRouter(prefix="/api", tags=["Replanning"])


@router.post("/simulate-delay", response_model=DelaySimulationResponse)
async def simulate_delay(request: SimulateDelayRequest) -> DelaySimulationResponse:
    """
    Simulate a delay event and return the updated itinerary.
    """
    try:
        # --- STUB MODE ---
        # return DelaySimulationResponse(
        #     updated_itinerary={"route": "Rishikesh (updated after delay)"},
        #     changes=["Breakfast shortened by 15 min", "Rest reduced by 30 min"],
        #     explanation="The plan was adjusted to accommodate the 90-minute delay.",
        # )

        # --- REAL MODE ---
        from backend.agents.workflow import run_replan_workflow

        # Build a minimal TripState-compatible dict
        state = {
            "raw_chat": [],
            "extracted_constraints": request.constraints or {},
            "missing_fields": [],
            "assumptions": {},
            "conflict_report": {},
            "is_ready_to_plan": True,
            "route_candidates": [],
            "hotel_candidates": [],
            "transport_candidates": [],
            "activity_candidates": [],
            "food_candidates": [],
            "waypoint_candidates": [],
            "itinerary_candidates": [],
            "selected_itinerary": request.selected_itinerary,
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

        delay_event = {
            "delay_type": request.delay_type,
            "delay_minutes": request.delay_minutes,
        }

        result = run_replan_workflow(state, delay_event)

        return DelaySimulationResponse(
            updated_itinerary=result.get("replanned_itinerary"),
            changes=result.get("replanned_itinerary", {}).get("changes", []) if result.get("replanned_itinerary") else [],
            validation_report=result.get("validation_report", {}),
            explanation=result.get("replanning_explanation", ""),
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 9: Create `backend/main.py`

```python
"""
TripGraph AI — FastAPI Backend
Run: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.api.chat_routes import router as chat_router
from backend.api.itinerary_routes import router as itinerary_router
from backend.api.replanner_routes import router as replanner_router

app = FastAPI(
    title="TripGraph AI",
    description="GenAI-Agentic Group Travel Planner API",
    version="0.1.0",
)

# CORS — allow React dev server and other local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(chat_router)
app.include_router(itinerary_router)
app.include_router(replanner_router)


@app.get("/", tags=["Health"])
async def root() -> dict:
    """Root endpoint — confirms API is running."""
    return {"message": "TripGraph AI API is running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
```

### Step 10: Create `docker-compose.yml`

```yaml
version: "3.8"

services:
  neo4j:
    image: neo4j:5-community
    container_name: tripgraph-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/tripgraph123
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD-SHELL", "neo4j status || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: tripgraph-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      neo4j:
        condition: service_healthy
    volumes:
      - ./backend:/app/backend

volumes:
  neo4j_data:
```

### Step 11: Create `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . /app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 12: Update `backend/requirements.txt`

```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.0
python-dotenv>=1.0.0
neo4j>=5.0.0
langgraph>=0.4.0
langchain>=0.3.0
langchain-google-genai>=2.0.0
langchain-core>=0.3.0
```

---

## Section E — File Manifest

```
backend/main.py                        — FastAPI application entry point
backend/config.py                      — Settings loaded from env vars
backend/Dockerfile                     — Docker image for the backend
backend/requirements.txt               — Python dependencies (pinned)
backend/api/__init__.py                — API routes package init
backend/api/chat_routes.py             — POST /api/parse-chat
backend/api/itinerary_routes.py        — POST /api/generate-itinerary
backend/api/replanner_routes.py        — POST /api/simulate-delay
backend/models/__init__.py             — Models package init
backend/models/requests.py             — Pydantic request models
backend/models/responses.py            — Pydantic response models
docker-compose.yml                     — Neo4j + Backend orchestration
specs/logs/bucket_3_decisions.md       — Decisions & assumptions log
```

Note: `.env.example` already exists in the repo root. Do NOT create a new one.

---

## Section F — Integration Verification Checklist & Tests

### Pre-Commit Checklist
- [ ] `uvicorn backend.main:app --reload` starts without import errors
- [ ] `http://localhost:8000/docs` shows Swagger UI with all 3 POST endpoints + 2 GET endpoints
- [ ] `http://localhost:8000/health` returns `{"status": "healthy"}`
- [ ] `http://localhost:8000/` returns `{"message": "TripGraph AI API is running", "docs": "/docs"}`
- [ ] All Pydantic models have type hints (no bare `dict` without explanation)
- [ ] All route functions have docstrings
- [ ] All exceptions are caught with `traceback.print_exc()` before raising HTTPException
- [ ] CORS middleware is configured with origins from `.env.example`
- [ ] Stub responses are present (commented out) in each route file
- [ ] No `TODO` or `pass` in any function that handles requests
- [ ] Import paths are correct: `from backend.agents.workflow import run_workflow`
- [ ] `specs/logs/bucket_3_decisions.md` is created

### Runnable Test (curl commands)

```bash
# Test 1: Health check
curl -s http://localhost:8000/health | python3 -m json.tool
# Expected: {"status": "healthy"}

# Test 2: Root
curl -s http://localhost:8000/ | python3 -m json.tool
# Expected: {"message": "TripGraph AI API is running", "docs": "/docs"}

# Test 3: Parse chat (requires Bucket 2 wired, or use stub mode)
curl -s -X POST http://localhost:8000/api/parse-chat \
  -H "Content-Type: application/json" \
  -d '{"chat_messages": ["Go from Gurugram", "Budget 15k", "Mountains"]}' \
  | python3 -m json.tool

# Test 4: Generate itinerary
curl -s -X POST http://localhost:8000/api/generate-itinerary \
  -H "Content-Type: application/json" \
  -d '{"constraints": {"origin": "Gurugram", "destination_type": "mountains", "budget_per_person": 15000}}' \
  | python3 -m json.tool

# Test 5: Simulate delay
curl -s -X POST http://localhost:8000/api/simulate-delay \
  -H "Content-Type: application/json" \
  -d '{"delay_type": "departure_delay", "delay_minutes": 90}' \
  | python3 -m json.tool
```

---

## Section G — 📋 Assumptions & Decisions Log (Output File)

**You MUST create:** `specs/logs/bucket_3_decisions.md`

```markdown
# Bucket 3 — Decisions & Assumptions Log
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
1. Stage all files listed in the File Manifest (Section E)
2. Stage specs/logs/bucket_3_decisions.md
3. Commit message: "Bucket 3: FastAPI backend with endpoints, models, Docker — [date]"
4. Branch: bucket-3/implementation
5. Push to origin
6. Do NOT merge to main
```
