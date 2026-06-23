# TripGraph AI

TripGraph AI turns a few lines of trip intent ("4-day Goa trip from Chandigarh, ₹40k pp, beaches + seafood, flying") into a **fully-reasoned, map-centric itinerary** — day-by-day, with real road/flight paths, costs, weather-aware gear notes, fatigue pacing, and live place photos & ratings.

It is built around a **multi-agent pipeline** that selects and sequences activities from a curated knowledge graph, grounded by real travel-time, weather, and places data — not invented by a single LLM call.

**Live demo:** https://tripgraph.app

---

## What it does

- **Chat → structured plan**: extracts constraints (origin, destination, days, budget, group, preferences) from natural language.
- **LLM Itinerary Architect**: one reasoned pass that *selects, sequences and clusters* activities per day using a real driving-time matrix — explicit travel legs between every stop, no idle gaps, return-to-hotel, breakfast-at-hotel.
- **Map-centric UI**: everything lives on the map — numbered pins, real ORS road polylines, flight legs, map-anchored detail popovers, a per-day strip, a Google-Calendar-style timeline, and a cost breakdown.
- **Grounded enrichment**: Google Place photos + ratings, weather forecast, flight/train advisories with scraped price ranges, "did you know" facts.
- **Delay-aware replanning**: simulate a delay and get an adjusted itinerary with a change summary.

---

## Architecture

### Components
- **Frontend** — React + Vite. Map-first UI (Leaflet + Google "Uber-style" tiles), map-anchored popovers, day strip, calendar, cost panel, delay simulator.
- **Backend** — FastAPI orchestration exposing parse / generate / refine / replan / config / health endpoints.
- **Agent pipeline** — LangGraph multi-node workflow (see below).
- **Knowledge / data layer** — a curated JSON knowledge store (`backend/data/local_kg_store.json`) of destinations, activities, hotels and transport. Neo4j is **optional**; the app runs fully on the JSON store if Neo4j is unavailable.

### Multi-LLM routing
LLM calls are routed **per agent role** via `.env` (no code changes):
- **Claude** (Anthropic) handles the reasoning-critical agents — the **architect** and the **review** pass.
- **Gemini** (`gemini-3.1-flash-lite`, free tier) handles the lighter, high-volume agents — parser, validator, flights/train advisories, fatigue, explainer, enricher.

Set the global default with `LLM_PROVIDER` / `LLM_MODEL`, and override any agent with `LLM_PROVIDER_<ROLE>` / `LLM_MODEL_<ROLE>` (e.g. `LLM_PROVIDER_ARCHITECT=anthropic`).

### Pipeline (agentic, LangGraph)
`chat_parser → constraint_validator → data_retriever (2-pass KG↔API↔cache) → mode_planner → planner_orchestrator → terminal_resolver → [flights ∥ train] → [weather ∥ insights] → architect (LLM brain) → photo_enricher → segment_router (ORS polylines) → fatigue_adjuster → review → explainer`

Independent agents run concurrently; the architect runs a single pass (configurable critic loop). A `refinement_questioner` powers the optional counter-questions step, and `replanner_agent` powers delay simulation.

### External data sources
| Source | Use |
|---|---|
| **OpenRouteService** | geocoding, driving routes, per-segment road polylines |
| **Google Maps Platform** | Places (photos, ratings, hours), Routes (distance matrix), Map Tiles |
| **OpenWeatherMap** | day-by-day forecast → gear checklist |
| **RailRadar** | alternative rail routes |
| **DuckDuckGo** | destination insights + flight/train price snippets |

---

## API endpoints
- `GET  /health` — health probe
- `GET  /docs` — Swagger UI
- `GET  /api/config` · `POST /api/config` — get/set pipeline mode
- `POST /api/parse-chat` — chat → extracted constraints
- `POST /api/generate-itinerary` — constraints → scored, validated itinerary (timeline, map points, cost)
- `POST /api/refinement-questions` — 1 round of sharpening counter-questions
- `POST /api/simulate-delay` — replan for a delay event
- `GET  /api/maptiles-session` · `GET /api/integrations` — map/config helpers

---

## Running locally

### Prerequisites
- Python 3.9+ (virtualenv at `.venv`)
- Node 20+ (nvm recommended)
- A `.env` file with the required keys (see below). Neo4j is **not** required.

### Environment (`.env`)
```bash
# LLM routing
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.1-flash-lite-preview
LLM_PROVIDER_ARCHITECT=anthropic
LLM_MODEL_ARCHITECT=claude-haiku-4-5-20251001
LLM_PROVIDER_REVIEW=anthropic
LLM_MODEL_REVIEW=claude-haiku-4-5-20251001

# Keys
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...            # Gemini (Generative Language)
GOOGLE_MAPS_API_KEY=...       # Places / Routes / Tiles  (also set VITE_GOOGLE_MAPS_API_KEY)
ORS_API_KEY=...
OPENWEATHERMAP_API_KEY=...
RAILRADAR_API_KEY=...
VITE_GOOGLE_MAPS_API_KEY=...
```
> `.env` is gitignored — never commit it.

### Start the backend
```bash
./.venv/bin/pip install -r backend/requirements.txt
./.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8001 --env-file .env
```
> `--env-file .env` is important — it loads the keys before the app imports, so Google/LLM clients pick them up.

### Start the frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173  (proxies the API via VITE_API_URL=http://localhost:8001)
```

---

## Deployment

Production runs on a DigitalOcean droplet behind nginx + systemd, with HTTPS via Let's Encrypt. The `deploy/` folder has everything:
- `deploy/deploy.sh <DROPLET_IP>` — installs deps, builds the frontend, runs the backend under systemd, fronts it with nginx (serves the SPA + proxies `/api`).
- `deploy/enable_https.sh <domain> <email>` — points nginx at the domain and provisions a Let's Encrypt cert (auto-renew).
- `deploy/DEPLOY.md` — step-by-step guide + troubleshooting.

### Private-preview / maintenance mode
Set `MAINTENANCE_MODE=true` (backend) and build the frontend with `VITE_MAINTENANCE=true` to keep the landing page live while disabling planning endpoints (returns 503) — useful for sharing the site without spending LLM/API credits.

---

## Repository structure
- `backend/` — FastAPI app, agent nodes (`agents/nodes/`), API clients (`api_clients/`), planner, models, curated KG store (`data/`)
- `frontend/` — React + Vite app (map / calendar / cost / delay UI, hooks, API client)
- `deploy/` — droplet deploy + HTTPS scripts and guide
- `specs/`, `Agent_Pipeline/` — design specs and pipeline notes
