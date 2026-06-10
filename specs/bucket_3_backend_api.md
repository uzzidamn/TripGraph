# Task 3: Backend API & Integration — Mini Spec

> **Owner**: Task 3 assignee
> **Priority**: P1 — Can start Day 1 with stub endpoints; wire to real workflow later
> **Estimated effort**: 7-10 days
> **Reference**: Read `MASTER_SPEC.md` (same folder) for full project context

---

## Overview

Your job is to build the **FastAPI backend** that serves as the HTTP bridge between the React frontend (JavaScript, runs in browser) and the Python backend (LangGraph agents, Neo4j, planner). You create the REST endpoints, Pydantic request/response models, configuration management, Docker Compose setup, and integration wiring.

### Why This Layer Exists
React runs in the browser. LangGraph, agents, and the planner run in Python on the server. **They cannot communicate directly.** FastAPI provides the HTTP endpoints the frontend calls. Without it, the frontend has no way to trigger the planning pipeline.

---

## What You Deliver

| # | Deliverable | File |
|---|------------|------|
| 1 | FastAPI main app | `backend/main.py` |
| 2 | Configuration | `backend/config.py` |
| 3 | Chat route | `backend/api/chat_routes.py` |
| 4 | Itinerary route | `backend/api/itinerary_routes.py` |
| 5 | Replanner route | `backend/api/replanner_routes.py` |
| 6 | Request models | `backend/models/requests.py` |
| 7 | Response models | `backend/models/responses.py` |
| 8 | Docker Compose | `docker-compose.yml` |
| 9 | Environment template | `.env.example` |
| 10 | Requirements file | `backend/requirements.txt` |
| 11 | `__init__.py` files | `backend/api/__init__.py`, `backend/models/__init__.py` |

---

## Step-by-Step Instructions

### Step 1: Set Up the Project

```bash
cd backend
python -m venv venv
source venv/bin/activate

pip install fastapi uvicorn[standard] pydantic python-dotenv
```

### Step 2: Create `config.py` — Configuration Management

```python
"""
Central configuration loaded from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "tripgraph123")

    # LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

settings = Settings()
```

### Step 3: Create `models/requests.py` — Request Schemas

```python
"""Pydantic models for API request bodies."""
from pydantic import BaseModel, Field
from typing import Optional


class ParseChatRequest(BaseModel):
    chat_messages: list[str] = Field(
        ...,
        description="List of group chat messages to parse",
        min_length=1,
        examples=[["Let's go from Gurugram", "Budget under 15k", "Mountains please"]],
    )


class GenerateItineraryRequest(BaseModel):
    constraints: dict = Field(
        ...,
        description="Extracted constraints (from /parse-chat or manually provided)",
        examples=[{
            "origin": "Gurugram",
            "destination_type": "mountains",
            "budget_per_person": 15000,
            "avoid_night_driving": True,
            "must_include": ["rafting", "cafes"],
            "return_deadline": "Monday morning",
            "hotel_tier": "comfort",
        }],
    )


class SimulateDelayRequest(BaseModel):
    itinerary_id: Optional[str] = Field(None, description="ID of the itinerary to modify")
    delay_type: str = Field(
        ...,
        description="Type of delay",
        examples=["departure_delay", "traffic_delay", "activity_delay"],
    )
    delay_minutes: int = Field(
        ...,
        ge=15,
        le=300,
        description="Delay duration in minutes",
        examples=[90],
    )
    # The full itinerary state will be passed in the session/state
    # For MVP, we can pass the full state
    constraints: Optional[dict] = None
    selected_itinerary: Optional[dict] = None
```

### Step 4: Create `models/responses.py` — Response Schemas

```python
"""Pydantic models for API responses."""
from pydantic import BaseModel
from typing import Optional, Any


class ParseChatResponse(BaseModel):
    extracted_constraints: dict
    missing_fields: list[str]
    assumptions: dict
    conflict_report: dict


class ItineraryResponse(BaseModel):
    recommended_itinerary: Optional[dict] = None
    alternatives: list[dict] = []
    validation_report: dict = {}
    score_breakdown: dict = {}
    timeline: list[dict] = []
    map_points: list[dict] = []
    cost_breakdown: dict = {}
    explanation: str = ""


class DelaySimulationResponse(BaseModel):
    updated_itinerary: Optional[dict] = None
    changes: list[str] = []
    validation_report: dict = {}
    explanation: str = ""


class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
```

### Step 5: Create API Route Files

#### `api/chat_routes.py`
```python
"""POST /api/parse-chat — Parse group chat and extract constraints."""
from fastapi import APIRouter, HTTPException
from backend.models.requests import ParseChatRequest
from backend.models.responses import ParseChatResponse

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/parse-chat", response_model=ParseChatResponse)
async def parse_chat(request: ParseChatRequest):
    """
    Parse group chat messages and extract structured trip constraints.
    Uses the Chat Parser + Constraint Validator agents.
    """
    try:
        # --- STUB MODE (start with this) ---
        # Return hardcoded response for frontend development
        # return ParseChatResponse(
        #     extracted_constraints={
        #         "origin": "Gurugram",
        #         "destination_type": "mountains",
        #         "budget_per_person": 15000,
        #         "avoid_night_driving": True,
        #         "must_include": ["rafting", "cafes"],
        #         "return_deadline": "Monday morning",
        #         "hotel_tier": "comfort",
        #     },
        #     missing_fields=[],
        #     assumptions={"group_size": "4 (default)"},
        #     conflict_report={"conflicts": []},
        # )

        # --- REAL MODE (wire when Task 2 is ready) ---
        from backend.agents.workflow import run_workflow
        result = run_workflow(request.chat_messages)

        return ParseChatResponse(
            extracted_constraints=result.get("extracted_constraints", {}),
            missing_fields=result.get("missing_fields", []),
            assumptions=result.get("assumptions", {}),
            conflict_report=result.get("conflict_report", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### `api/itinerary_routes.py`
```python
"""POST /api/generate-itinerary — Generate and score itineraries."""
from fastapi import APIRouter, HTTPException
from backend.models.requests import GenerateItineraryRequest
from backend.models.responses import ItineraryResponse

router = APIRouter(prefix="/api", tags=["Itinerary"])


@router.post("/generate-itinerary", response_model=ItineraryResponse)
async def generate_itinerary(request: GenerateItineraryRequest):
    """
    Generate candidate itineraries from constraints.
    Runs the full agentic pipeline: data retrieval → planning → scoring → explanation.
    """
    try:
        # --- STUB MODE ---
        # return ItineraryResponse(
        #     recommended_itinerary={
        #         "route": "Gurugram to Rishikesh",
        #         "tier": "comfort",
        #         "total_cost_per_person": 13750,
        #     },
        #     alternatives=[],
        #     timeline=[
        #         {"day": 1, "start_time": "06:00", "end_time": "09:00",
        #          "title": "Drive to breakfast stop", "type": "travel"},
        #     ],
        #     explanation="This plan was selected because...",
        # )

        # --- REAL MODE ---
        from backend.agents.workflow import run_workflow

        # Build chat messages from constraints for the workflow
        # OR refactor workflow to accept constraints directly
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
        raise HTTPException(status_code=500, detail=str(e))


def _constraints_to_chat(constraints: dict) -> list[str]:
    """Convert constraints dict to synthetic chat messages for the workflow."""
    messages = []
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
    return messages or ["Plan a trip"]
```

#### `api/replanner_routes.py`
```python
"""POST /api/simulate-delay — Simulate a delay and replan."""
from fastapi import APIRouter, HTTPException
from backend.models.requests import SimulateDelayRequest
from backend.models.responses import DelaySimulationResponse

router = APIRouter(prefix="/api", tags=["Replanning"])


@router.post("/simulate-delay", response_model=DelaySimulationResponse)
async def simulate_delay(request: SimulateDelayRequest):
    """
    Simulate a delay event and return the updated itinerary.
    """
    try:
        # --- STUB MODE ---
        # return DelaySimulationResponse(
        #     updated_itinerary={"route": "Rishikesh (updated)"},
        #     changes=["Breakfast shortened by 15 min", "Cafe moved to Day 2"],
        #     explanation="The plan was adjusted to accommodate the delay.",
        # )

        # --- REAL MODE ---
        from backend.agents.workflow import run_replan_workflow
        from backend.agents.state import TripState

        # Build state from request
        state = TripState(
            raw_chat=[],
            extracted_constraints=request.constraints or {},
            selected_itinerary=request.selected_itinerary,
            # ... fill other fields
        )

        delay_event = {
            "delay_type": request.delay_type,
            "delay_minutes": request.delay_minutes,
        }

        result = run_replan_workflow(state, delay_event)

        return DelaySimulationResponse(
            updated_itinerary=result.get("replanned_itinerary"),
            changes=result.get("replanned_itinerary", {}).get("changes", []),
            explanation=result.get("replanning_explanation", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 6: Create `main.py` — FastAPI Application

```python
"""
TripGraph AI — FastAPI Backend
Run: uvicorn backend.main:app --reload --port 8000
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

# CORS — allow React dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router)
app.include_router(itinerary_router)
app.include_router(replanner_router)


@app.get("/")
async def root():
    return {"message": "TripGraph AI API is running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Step 7: Create `docker-compose.yml`

```yaml
version: "3.8"

services:
  neo4j:
    image: neo4j:5-community
    container_name: tripgraph-neo4j
    ports:
      - "7474:7474"    # Browser UI
      - "7687:7687"    # Bolt protocol
    environment:
      - NEO4J_AUTH=neo4j/tripgraph123
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD-SHELL", "neo4j status || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: tripgraph-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      neo4j:
        condition: service_healthy
    volumes:
      - ./backend:/app

volumes:
  neo4j_data:
```

### Step 8: Create `.env.example`

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tripgraph123

# LLM
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_TEMPERATURE=0

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Step 9: Create `backend/requirements.txt`

```
fastapi==0.115.*
uvicorn[standard]==0.34.*
pydantic==2.*
python-dotenv==1.*
neo4j==5.*
langgraph==0.4.*
langchain==0.3.*
langchain-google-genai==2.*
langchain-core==0.3.*
```

---

## Testing Checklist

- [ ] `uvicorn backend.main:app --reload` starts without errors
- [ ] `http://localhost:8000/docs` shows Swagger UI with all 3 endpoints
- [ ] `http://localhost:8000/health` returns `{"status": "healthy"}`
- [ ] Stub endpoints return hardcoded JSON responses
- [ ] React frontend can call stub endpoints (CORS works)
- [ ] Docker Compose starts Neo4j + Backend together
- [ ] Real workflow integration works (after Task 2 is ready)

### Quick Test with curl
```bash
# Test parse-chat (stub)
curl -X POST http://localhost:8000/api/parse-chat \
  -H "Content-Type: application/json" \
  -d '{"chat_messages": ["Go from Gurugram", "Budget 15k", "Mountains"]}'

# Test generate-itinerary (stub)
curl -X POST http://localhost:8000/api/generate-itinerary \
  -H "Content-Type: application/json" \
  -d '{"constraints": {"origin": "Gurugram", "destination_type": "mountains"}}'
```

---

## Coordination with Other Tasks

| You need from | What |
|--------------|------|
| Task 2 | `run_workflow()` and `run_replan_workflow()` functions |
| Task 2 | `TripState` type definition |

| Others need from you | What |
|---------------------|------|
| Task 4 (Frontend) | API endpoint URLs and response JSON shapes |
| Task 4 (Frontend) | CORS configuration so frontend can call API |

> **Tip**: Deliver stub endpoints ASAP so Task 4 (Frontend) can start building against real HTTP responses.

---

## Git Workflow

```bash
git checkout -b bucket-3/fastapi-setup
# Create main.py, config.py, requirements.txt
git commit -m "Task 3: FastAPI app setup with CORS and health check"

git checkout -b bucket-3/api-endpoints
# Create routes, models
git commit -m "Task 3: Add all API endpoints with stub responses"

git checkout -b bucket-3/docker-compose
# Create docker-compose.yml, .env.example
git commit -m "Task 3: Add Docker Compose for Neo4j + Backend"
```
