# TripGraph AI — Project Context Summary

## What is This Project?

**TripGraph AI** is a GenAI-agentic **group travel planner** that converts messy WhatsApp-style group chat into structured, constraint-aware travel itineraries. It is a **planning engine with a chat interface** — NOT a chatbot.

### Core Flow
```
Group chat → LLM extracts constraints → Neo4j knowledge graph queried →
Graph planning engine generates/scores/validates itineraries →
React frontend shows Timeline + Map + Cost + Calendar
```

### Design Philosophy
- **LLM** handles language (extraction, explanation)
- **Python** handles math (cost, timing, validation)
- **Graph Planner** handles optimization (itinerary construction)
- **LangGraph** orchestrates the multi-step workflow
- **Neo4j** stores all travel domain data

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Leaflet.js + OpenStreetMap |
| Backend API | Python + FastAPI |
| Agentic Workflow | LangGraph (stateful graph-based workflows) |
| LLM | Google Gemini 2.0 Flash (free tier, swappable) |
| Knowledge Graph | Neo4j Community Edition (Docker) |
| Planning Engine | Custom Python + Neo4j Cypher |
| Containerization | Docker + Docker Compose |

---

## Project Scope

### 3 Travel Routes (from Gurugram/Delhi NCR)
| Route | Type | Distance | Drive Time |
|-------|------|----------|------------|
| Gurugram → Jaipur | Heritage | 240 km | ~5 hrs |
| Gurugram → Rishikesh | Adventure | 260 km | ~6.5 hrs |
| Gurugram → Tirthan/Jibhi | Expedition | 510 km | ~12 hrs |

### 3 Travel Tiers
- **Budget** — Shared/public transport, basic stay
- **Comfort** — Cab with driver, mid-range hotel
- **Expedition** — Self-drive/bike, homestay/camping

### 12 Key Features
1. Group chat input parsing
2. LLM constraint extraction (agentic workflow)
3. Neo4j knowledge graph with travel data
4. Graph-based itinerary planning with candidate generation
5. Multi-objective scoring (cost, comfort, fatigue, risk, preference)
6. Hard constraint validation (budget, deadline, night driving)
7. Interactive timeline display
8. Leaflet.js map with route + POI markers
9. Cost breakdown per person
10. Calendar-style schedule view
11. Delay simulation and replanning
12. Natural language explanation of itinerary

---

## 5 Task Buckets

### Task 1: Dummy Data & Seed Pipeline (P0)
- **Files**: `backend/data/*.json`, `backend/knowledge_graph/seed.py`
- 7 JSON seed files (cities, routes, hotels, activities, restaurants, transport, waypoints)
- Python seed script to load data into Neo4j
- ~60-80 total data records across all files

### Task 2: Agentic AI Pipeline — LangGraph (P1)
- **Files**: `backend/agents/*`
- 6 agent nodes: Chat Parser, Constraint Validator, Data Retriever, Planner Orchestrator, Explainer, Replanner
- Swappable LLM client (Gemini/OpenAI/Ollama)
- TripState schema, prompt templates, LangGraph workflow

### Task 3: Backend API & Integration (P1)
- **Files**: `backend/main.py`, `backend/config.py`, `backend/api/*`, `backend/models/*`, `docker-compose.yml`
- 3 FastAPI endpoints: `/api/parse-chat`, `/api/generate-itinerary`, `/api/simulate-delay`
- Pydantic request/response models, CORS, Docker Compose

### Task 4: Frontend UI & Visualization (P1)
- **Files**: `frontend/*`
- React + Vite app with 8 components: ChatRoom, ExtractedPreferences, ItineraryOptions, ItineraryTimeline, MapView, CostBreakdown, CalendarView, DelaySimulator
- Dark theme design system, Leaflet.js map, responsive layout

### Task 5: Neo4j Knowledge Graph + Graph Planning Engine (P0)
- **Files**: `backend/knowledge_graph/*`, `backend/tools/*`, `backend/planner/*`
- Neo4j connection, schema, Cypher query library
- 6 tool functions (routes, hotels, activities, transport, restaurants, waypoints)
- Planning engine: trip graph builder, candidate generator, scorer, validator, timeline generator, replanner

---

## Current Status

> [!IMPORTANT]
> **Only spec files exist. No implementation code has been written yet.**
> The project contains:
> - 1 Word document (original requirements)
> - 6 spec markdown files (master spec + 5 task bucket specs)
> - **No `backend/` directory**
> - **No `frontend/` directory**
> - **No code at all**

---

## Directory Structure (Target)

```
TripGraph/
├── backend/
│   ├── main.py                      # FastAPI entry
│   ├── config.py                    # Env config
│   ├── requirements.txt
│   ├── api/                         # REST endpoints
│   ├── models/                      # Pydantic models
│   ├── agents/                      # LangGraph pipeline
│   │   └── nodes/                   # 6 agent nodes
│   ├── knowledge_graph/             # Neo4j layer
│   ├── tools/                       # 6 tool functions
│   ├── planner/                     # Planning engine
│   └── data/                        # 7 JSON seed files
├── frontend/                        # React + Vite
│   └── src/
│       ├── api/
│       ├── components/
│       └── hooks/
├── specs/                           # ✅ EXISTS
├── docker-compose.yml
├── .env.example
└── README.md
```
