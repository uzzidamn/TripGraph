# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TripGraph AI is a GenAI-agentic group travel planner. It converts messy group chat messages into structured, constraint-aware itineraries. It is a **planning engine with a chat interface** — not a booking platform.

Core design rule: **LLM handles language. Python handles math. Graph planner handles optimization.**

## Running the Stack

### Neo4j (must be running before backend)
```bash
docker run -d \
  --name tripgraph-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/tripgraph123 \
  neo4j:5-community
# Browser UI: http://localhost:7474  (neo4j / tripgraph123)
```

Or via Docker Compose (when `docker-compose.yml` exists):
```bash
docker compose up -d
```

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### Initialize Neo4j schema + seed data (first-time setup)
```bash
python -m backend.knowledge_graph.schema   # creates constraints/indexes
python -m backend.knowledge_graph.seed     # loads JSON data into graph
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## Environment Configuration

Copy `.env.example` to `.env` in the project root (or `backend/`). Required variables:

```env
LLM_PROVIDER=gemini          # gemini | openai | ollama
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=<from aistudio.google.com/apikey>

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tripgraph123

CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

Swapping LLMs requires only changing `LLM_PROVIDER` and `LLM_MODEL` — `backend/agents/llm_client.py` handles the factory pattern.

## Architecture

```
React Frontend  →  FastAPI (/api/parse-chat, /generate-itinerary, /simulate-delay)
                       ↓
               LangGraph Workflow (6 agent nodes in TripState)
                  ↙              ↘
           Gemini LLM         Neo4j + Graph Planning Engine
        (language only)       (math, scoring, validation)
```

### LangGraph Workflow (backend/agents/)

Six nodes run sequentially on a shared `TripState` (TypedDict):

1. **chat_parser** — LLM extracts structured constraints from raw messages
2. **constraint_validator** — LLM checks completeness; loops back if missing fields
3. **data_retriever** — calls tool functions to fetch matching data from Neo4j (no invention)
4. **planner_orchestrator** — calls the Graph Planning Engine to generate/score/validate candidates
5. **explainer** — LLM generates a natural language rationale for the selected itinerary
6. **replanner_agent** — handles delay simulation; shifts/removes events, then re-explains

State flows from node to node via `TripState`; agents must not calculate costs or invent data.

### Neo4j Knowledge Graph (backend/knowledge_graph/ + backend/tools/)

All travel domain data lives in Neo4j as a property graph. The **tool layer** (`backend/tools/*.py`) provides the only interface agents use to read data — each tool wraps a Cypher query from `backend/knowledge_graph/queries.py`.

Key node types: `:City` `:Route` `:Hotel` `:Activity` `:Restaurant` `:TransportOption` `:Waypoint` `:Tag`

Key relationships: `ORIGIN_OF`, `ARRIVES_AT`, `HAS_HOTEL`, `HAS_ACTIVITY`, `HAS_TRANSPORT`, `PASSES_THROUGH`, `TAGGED`, `ON_ROUTE`

### Graph Planning Engine (backend/planner/)

Generates itinerary candidates by exploring `route × transport × hotel × activity_set × restaurant_set`, then:
- **scorer.py** — multi-objective score: preference_match + experience + comfort + scenic − cost_penalty − fatigue − risk
- **validator.py** — hard constraint checks (budget, return deadline, night driving, mandatory activities)
- **timeline_generator.py** — places events sequentially from departure time
- **replanner.py** — on delay event, shifts flexible events, removes optional ones, re-validates

Hard constraints cause infinite penalty (candidate disqualified). Soft constraints only reduce score.

### Seed Data (backend/data/)

Seven JSON files (`seed_cities.json`, `seed_routes.json`, `seed_hotels.json`, `seed_activities.json`, `seed_restaurants.json`, `seed_transport.json`, `seed_waypoints.json`) cover 3 routes from Gurugram:
- Gurugram → Jaipur (heritage, low risk)
- Gurugram → Rishikesh (adventure, medium risk)
- Gurugram → Tirthan Valley (expedition, high risk)

Each route supports 3 tiers: **budget / comfort / expedition**. JSON format mirrors what a real travel API would return so tool functions stay stable when real APIs are added.

### Frontend (frontend/src/)

Key components under `src/components/`:
- `chat/ChatRoom` — paste group messages, send to `/api/parse-chat`
- `preferences/ExtractedPreferences` — displays parsed constraints
- `itinerary/ItineraryOptions`, `ItineraryTimeline`, `CalendarView` — itinerary display
- `map/MapView` — Leaflet.js + OpenStreetMap (no API key needed), route polyline + POI markers
- `cost/CostBreakdown` — per-person cost table
- `delay/DelaySimulator` — input delay type + minutes, calls `/api/simulate-delay`

State management is in `src/hooks/useItinerary.js`. API calls go through `src/api/tripApi.js`.

## Task Ownership

| Task | Files |
|------|-------|
| 1 — Dummy Data & Seed | `backend/data/*.json`, `backend/knowledge_graph/seed.py` |
| 2 — Agentic Pipeline | `backend/agents/` |
| 3 — Backend API | `backend/main.py`, `backend/config.py`, `backend/api/`, `backend/models/`, `docker-compose.yml` |
| 4 — Frontend | `frontend/` |
| 5 — Neo4j + Planner | `backend/knowledge_graph/` (except seed.py), `backend/tools/`, `backend/planner/` |

## Validate JSON Seed Files
```bash
python -m json.tool backend/data/seed_cities.json
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/parse-chat` | Extract constraints from chat messages |
| POST | `/api/generate-itinerary` | Generate itinerary from constraints |
| POST | `/api/simulate-delay` | Replan given a delay event |
