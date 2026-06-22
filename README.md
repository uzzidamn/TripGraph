# TripGraph

TripGraph is a GenAI-assisted group travel planning system that converts (group) conversation/chat into structured constraints, builds itineraries, scores and validates plans, and supports delay-aware replanning.

## Architecture overview

### High-level components
- Frontend (React + Vite): chat-first UI to submit trip intent, review extracted constraints, inspect itinerary/timeline/map/cost, and simulate delays.
- Backend (FastAPI): API orchestration layer exposing parse, generate-itinerary, replanning, config, and health endpoints.
- Planning engine (Python modules): candidate generation, scoring, validation, timeline generation, and deterministic replanning.
- Agent pipelines:
  - Agentic pipeline (LangGraph): multi-node workflow with chat parsing, constraint validation, retrieval, planning, enrichment, and explanation.
  - Augmented pipeline (ReAct tool-calling): tool-augmented LLM loop producing a complete TripState.
- Knowledge/data layer:
  - Neo4j graph database
  - Seed JSON datasets for routes/hotels/activities/transport/waypoints/restaurants
  - External APIs (OpenRouteService, Geoapify, OpenWeatherMap)

### Runtime data flow
1. User submits chat messages in frontend.
2. Backend /api/parse-chat extracts constraints and reports missing fields/conflicts.
3. Frontend submits constraints to /api/generate-itinerary.
4. Backend executes selected pipeline mode (agentic or augmented), then planner + enrichment + explanation.
5. Frontend renders itinerary options, timeline/calendar, map points, and cost breakdown.
6. On delay simulation, frontend calls /api/simulate-delay and backend returns replanned itinerary + change summary.

## Backend interfaces

### Core API endpoints
- GET /health: service health probe
- GET /docs: Swagger UI
- GET /redoc: ReDoc API docs
- GET /: interactive backend test console (HTML)
- GET /api/config: get active pipeline mode
- POST /api/config: set pipeline mode (agentic or augmented)
- POST /api/parse-chat: parse chat to extracted constraints
- POST /api/generate-itinerary: generate scored validated itinerary from constraints
- POST /api/simulate-delay: replan selected itinerary for a delay event

### Pipeline mode behavior
- agentic: LangGraph node workflow from parse to explain
- augmented: tool-augmented LLM ReAct loop

## Frontend interfaces

- Main UI (Vite app): http://localhost:5173
- Workflow steps in UI:
  - Plan (chat input)
  - Review (constraints and assumptions)
  - Explore (itinerary, map, timeline, cost, delay simulator)

## Launch guide (local host mode)

### Prerequisites
- Neo4j service installed and available on localhost:7687
- Python 3.9+ virtual environment at .venv
- Node 20+ available (nvm recommended)
- .env configured (especially GOOGLE_API_KEY)

### Start services
1. Neo4j
   - sudo systemctl start neo4j

2. Backend
   - cd /workspace/sw/siddaraj/iisc/deep_learning/TripGraph
   - source .venv/bin/activate
   - no_proxy=localhost,127.0.0.1 uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

3. Frontend
   - export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
   - cd /workspace/sw/siddaraj/iisc/deep_learning/TripGraph/frontend
   - npm run dev -- --host 0.0.0.0

## Test interfaces

### Interactive interfaces
- Frontend UI: http://localhost:5173
- Backend HTML test console: http://localhost:8000/
- Swagger docs + try-it-out: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

### Automated test entry points
- Full API integration suite:
  - python -m pytest backend/tests/test_all_apis.py -v
  - or python backend/tests/test_all_apis.py
- Offline planning engine checks (mock data, no live Neo4j required):
  - python backend/test_runner.py
- Bucket test suites:
  - backend/tests/test_bucket_1.py
  - backend/tests/test_bucket_2.py
  - backend/tests/test_bucket_3.py
  - backend/tests/test_bucket_5.py

## Repository structure (summary)
- backend/: FastAPI APIs, agents, planner, knowledge graph, models, tools, tests
- frontend/: React app, hooks, API client, map/calendar/cost/delay UI components
- specs/: bucket specs, implementation plan, logs
- Agent_Pipeline/: planning/spec notes for the agent pipeline

## Notes for this environment
- If localhost requests are routed through a corporate proxy, set no_proxy=localhost,127.0.0.1 when invoking local service checks.
- If using docker compose networking, set NEO4J_URI=bolt://neo4j:7687. For local Neo4j service, keep NEO4J_URI=bolt://localhost:7687.
