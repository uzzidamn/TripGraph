# TripGraph AI — Master Project Specification

> **TripGraph AI: A GenAI-Agentic Group Travel Planner with Constraint-Aware Itinerary Optimization**
>
> This document is the single source of truth for the entire project. Every task bucket references this spec.

---

## 1. Executive Summary

TripGraph AI is a GenAI-agentic travel planning prototype that converts messy group travel discussions into structured, deterministic, constraint-aware itineraries. It is **not** a booking platform — it is an **AI planning engine with a chat interface**.

The system:
1. Accepts group travel chat as input (text messages simulating a WhatsApp/Telegram group)
2. Uses an LLM (Google Gemini, free tier) via an agentic LangGraph workflow to extract structured trip constraints
3. Stores all travel domain data in a **Neo4j knowledge graph** (cities, routes, hotels, activities, restaurants, transport options)
4. Uses a **deterministic graph-based planning engine** to generate, score, and validate candidate itineraries
5. Displays results via a **React frontend** with interactive timeline, Leaflet.js map, cost breakdown, and calendar view
6. Supports **delay-aware replanning** — simulating disruptions and adjusting the itinerary in real-time

### Core Design Philosophy

```
DO NOT build another chatbot.
BUILD a planning engine with a chat interface.
```

| Responsibility | Owner |
|---------------|-------|
| Language understanding & explanation | LLM (Gemini) |
| Math, cost, timing, validation | Deterministic Python logic |
| Itinerary construction & optimization | Graph Planning Engine |
| Data storage & retrieval | Neo4j Knowledge Graph |
| Workflow orchestration | LangGraph |
| User interaction | React Frontend |
| HTTP bridge | FastAPI Backend |

---

## 2. Problem Motivation

Group travel planning is messy. People discuss trips in group chats with scattered, conflicting preferences:
- One person wants the cheapest trip
- One wants comfort
- One wants adventure
- One insists on no night driving
- One needs to return before work on Monday

The planning process involves browsing destinations, comparing transport, checking hotels, estimating costs, mapping routes, and manually creating a plan. Existing tools solve parts of this — but none convert **messy group discussion into a deterministic, validated, constraint-aware itinerary**.

TripGraph AI focuses on this specific challenge: extracting structured requirements from natural language, modeling the trip as a graph, and generating optimized plans that satisfy hard constraints while maximizing soft preferences.

---

## 3. Project Scope

### 3.1 What We Build (Current Scope)

| # | Feature |
|---|---------|
| 1 | Group travel chat input |
| 2 | LLM-based constraint extraction via agentic workflow |
| 3 | Neo4j knowledge graph with full travel domain data |
| 4 | Graph-based itinerary planning with candidate generation |
| 5 | Multi-objective scoring (cost, comfort, fatigue, risk, preference match) |
| 6 | Hard constraint validation (budget, return deadline, night driving) |
| 7 | Interactive timeline display |
| 8 | Leaflet.js map with route and POI markers |
| 9 | Cost breakdown per person |
| 10 | Calendar-style schedule view |
| 11 | Delay simulation and replanning |
| 12 | Natural language explanation of itinerary selection |

### 3.2 What We Do NOT Build

| # | Excluded Feature |
|---|-----------------|
| 1 | Real flight/hotel/cab booking |
| 2 | Real payment processing |
| 3 | User authentication |
| 4 | Live traffic/weather data |
| 5 | Production mobile app |
| 6 | Real OTA partnerships |
| 7 | Evaluation benchmarks (deprioritized for MVP) |

### 3.3 Initial Routes

Three routes from Gurugram/Delhi NCR representing different travel styles:

| Route | Type | Distance | Drive Time | Character |
|-------|------|----------|------------|-----------|
| Gurugram → Jaipur | Heritage | 240 km | ~5 hrs | Heritage, food, family-friendly |
| Gurugram → Rishikesh | Adventure | 260 km | ~6.5 hrs | Adventure, rafting, cafes |
| Gurugram → Tirthan/Jibhi | Expedition | 510 km | ~12 hrs | Scenic, nature, long-weekend |

### 3.4 Travel Tiers

Each route supports three tiers:

| Tier | Transport | Hotel | Character |
|------|-----------|-------|-----------|
| Budget | Shared/public transport | Basic stay | Lowest per-person cost |
| Comfort | Cab with driver | Mid-range hotel | Balanced convenience |
| Expedition | Self-drive / bike | Homestay / camping | Maximum adventure |

---

## 4. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React + Vite | Interactive UI, component-based, Leaflet.js for maps |
| **Map** | Leaflet.js + OpenStreetMap | Free, open-source, no API key needed |
| **Backend API** | Python + FastAPI | High-performance, auto-docs, type hints |
| **Agentic Workflow** | LangGraph | Stateful graph-based workflows with State, Nodes, Edges |
| **LLM** | Google Gemini 2.0 Flash (free tier) | 15 RPM, 1M TPM — sufficient for dev/demo. Swappable via LangChain. |
| **Knowledge Graph** | Neo4j Community Edition | Property graph DB, Cypher queries, runs in Docker |
| **Graph Planning** | Custom Python + Neo4j Cypher | Candidate generation, scoring, validation |
| **Containerization** | Docker + Docker Compose | Neo4j + Backend in containers |

### 4.1 LLM Configuration

The LLM client is designed to be **swappable with a single config change**:

```python
# .env file — change these two values to swap LLM
LLM_PROVIDER=gemini          # gemini | openai | ollama
LLM_MODEL=gemini-2.0-flash   # model name for the provider
```

| Provider | Model | Cost | Setup |
|----------|-------|------|-------|
| Gemini Free | gemini-2.0-flash | Free (15 RPM) | API key from Google AI Studio |
| Gemini Paid | gemini-2.5-pro | Pay-per-use | Same API key, higher limits |
| OpenAI | gpt-4o-mini | Pay-per-use | OpenAI API key |
| Local (Ollama) | gemma2:9b | Free | Install Ollama, pull model (~8GB RAM) |

---

## 5. System Architecture

### 5.1 High-Level Data Flow

```
User types group chat messages
    → React Frontend sends HTTP POST to FastAPI
        → FastAPI invokes LangGraph workflow
            → Chat Parser Agent extracts constraints (LLM call)
            → Constraint Validator checks completeness (LLM call)
            → Data Retriever calls Neo4j tool functions
            → Planner Orchestrator invokes Graph Planning Engine
                → Trip Graph Builder queries Neo4j
                → Candidate Generator creates itinerary options
                → Scorer evaluates each candidate
                → Validator checks hard constraints
                → Timeline Generator places events in sequence
            → Explainer generates natural language summary (LLM call)
        → FastAPI returns JSON response
    → React renders Timeline, Map, Cost, Calendar
```

### 5.2 Layer Architecture

```
┌──────────────────────────────────────────────────────┐
│              Frontend (React + Vite + Leaflet)        │
│  ChatRoom | Preferences | Timeline | Map | Cost      │
│  CalendarView | DelaySimulator | ItineraryOptions     │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP POST/GET (JSON)
┌──────────────────────▼───────────────────────────────┐
│              Backend API (FastAPI)                     │
│  /api/parse-chat                                      │
│  /api/generate-itinerary                              │
│  /api/simulate-delay                                  │
└──────────────────────┬───────────────────────────────┘
                       │ invoke workflow
┌──────────────────────▼───────────────────────────────┐
│           Agentic Pipeline (LangGraph)                │
│  Chat Parser → Constraint Validator → Data Retriever  │
│  → Planner Orchestrator → Explainer / Replanner       │
└───────┬──────────────┬───────────────────────────────┘
        │              │
   LLM calls      Tool calls + Planner calls
        │              │
┌───────▼──────┐ ┌─────▼────────────────────────────────┐
│ Gemini API   │ │  Neo4j Knowledge Graph + Planning     │
│ (swappable)  │ │  Tool Functions → Cypher Queries      │
│              │ │  Trip Graph Builder → Candidate Gen    │
│              │ │  Scorer → Validator → Replanner        │
└──────────────┘ └──────────────────────────────────────┘
```

---

## 6. Neo4j Knowledge Graph

### 6.1 Why Neo4j (Option C — Full Knowledge Graph)

All travel domain data is stored as an interconnected knowledge graph in Neo4j. This provides:

1. **Natural relationship modeling** — "this hotel is in this city," "this route connects these cities," "this activity is tagged as adventure" are expressed as graph edges
2. **Powerful queries** — a single Cypher query can traverse multiple relationships (e.g., "find mountain destinations from Gurugram with comfort hotels under ₹5,000/night and adventure activities")
3. **Future-proof** — new data types (flights, weather alerts, user preferences) can be added as new node types without schema migration
4. **Trip graph construction** — the planning engine can build itinerary subgraphs using the same graph infrastructure

### 6.2 Node Labels

| Label | Key Properties |
|-------|---------------|
| `:City` | name, type (mountains/heritage/nature), lat, lng, description |
| `:Route` | route_id, distance_km, base_drive_minutes, risk_level, scenic_score, recommended_for[] |
| `:Hotel` | hotel_id, name, tier, price_per_night, rooms_required, checkin_time, checkout_time, comfort_score, lat, lng |
| `:Activity` | activity_id, name, category, duration_minutes, cost_per_person, available_slots[], risk_level |
| `:Restaurant` | restaurant_id, name, meal_types[], avg_cost_per_person, avg_duration_minutes |
| `:TransportOption` | transport_id, mode, tier, cost_total, capacity, base_duration_minutes, night_driving_allowed, comfort_score, fatigue_score |
| `:Waypoint` | waypoint_id, name, type (breakfast_stop/fuel/viewpoint), km_from_origin, lat, lng |
| `:Tag` | name (adventure, mountains, heritage, culture, food, nature, etc.) |

### 6.3 Relationships

| Relationship | From → To | Properties |
|-------------|-----------|------------|
| `ORIGIN_OF` | City → Route | — |
| `ARRIVES_AT` | Route → City | — |
| `HAS_HOTEL` | City → Hotel | — |
| `HAS_ACTIVITY` | City → Activity | — |
| `HAS_RESTAURANT` | City → Restaurant | — |
| `HAS_TRANSPORT` | Route → TransportOption | — |
| `PASSES_THROUGH` | Route → Waypoint | order, km_from_origin |
| `TAGGED` | City/Activity/Restaurant → Tag | — |
| `NEAR` | Hotel → Activity | distance_km |
| `ON_ROUTE` | Restaurant → Route | km_from_origin |

### 6.4 Example Cypher Queries

```cypher
-- Find all mountain destinations reachable from Gurugram with comfort hotels
MATCH (origin:City {name: "Gurugram"})-[:ORIGIN_OF]->(r:Route)-[:ARRIVES_AT]->(dest:City)
WHERE dest.type = "mountains"
MATCH (dest)-[:HAS_HOTEL]->(h:Hotel {tier: "comfort"})
RETURN dest.name, h.name, h.price_per_night, r.distance_km
ORDER BY h.price_per_night ASC

-- Find activities tagged 'adventure' at a destination
MATCH (dest:City {name: "Rishikesh"})-[:HAS_ACTIVITY]->(a:Activity)-[:TAGGED]->(t:Tag {name: "adventure"})
RETURN a.name, a.cost_per_person, a.duration_minutes

-- Full route data: destination + hotels + activities + transport
MATCH (origin:City {name: "Gurugram"})-[:ORIGIN_OF]->(r:Route)-[:ARRIVES_AT]->(dest:City)
OPTIONAL MATCH (dest)-[:HAS_HOTEL]->(h:Hotel)
OPTIONAL MATCH (dest)-[:HAS_ACTIVITY]->(a:Activity)
OPTIONAL MATCH (r)-[:HAS_TRANSPORT]->(t:TransportOption)
RETURN r, dest, collect(DISTINCT h) as hotels,
       collect(DISTINCT a) as activities, collect(DISTINCT t) as transport

-- Find highway food stops on a route
MATCH (r:Route {route_id: "gurugram_rishikesh_2d1n"})<-[:ON_ROUTE]-(rest:Restaurant)
RETURN rest.name, rest.km_from_origin, rest.avg_cost_per_person
ORDER BY rest.km_from_origin
```

### 6.5 Schema Creation Script

```cypher
// Constraints and indexes for performance
CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:Route) REQUIRE r.route_id IS UNIQUE;
CREATE CONSTRAINT hotel_id IF NOT EXISTS FOR (h:Hotel) REQUIRE h.hotel_id IS UNIQUE;
CREATE CONSTRAINT activity_id IF NOT EXISTS FOR (a:Activity) REQUIRE a.activity_id IS UNIQUE;
CREATE CONSTRAINT restaurant_id IF NOT EXISTS FOR (r:Restaurant) REQUIRE r.restaurant_id IS UNIQUE;
CREATE CONSTRAINT transport_id IF NOT EXISTS FOR (t:TransportOption) REQUIRE t.transport_id IS UNIQUE;
CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE;

CREATE INDEX city_type IF NOT EXISTS FOR (c:City) ON (c.type);
CREATE INDEX hotel_tier IF NOT EXISTS FOR (h:Hotel) ON (h.tier);
CREATE INDEX activity_category IF NOT EXISTS FOR (a:Activity) ON (a.category);
```

---

## 7. Agentic AI Design

### 7.1 Core Principle

| Component | Responsibility |
|-----------|---------------|
| LLM | Understands language, extracts constraints, explains decisions |
| Python | Calculates cost, timing, validates feasibility |
| Graph Planner | Constructs and scores itineraries |
| LangGraph | Orchestrates the multi-step workflow |

The LLM should **never** calculate costs, durations, or validate constraints. It extracts intent and generates explanations. All math is deterministic Python.

### 7.2 Agents

#### Agent 1: Chat Parser
**Purpose**: Extract structured requirements from group chat messages.

**Input**: `List[str]` — raw chat messages
**Output**: Structured constraints dict
```json
{
  "origin": "Gurugram",
  "destination": null,
  "destination_type": "mountains",
  "budget_per_person": 15000,
  "dates": "weekend",
  "transport_preference": ["cab_with_driver"],
  "avoid_night_driving": true,
  "must_include": ["rafting", "cafes"],
  "return_deadline": "Monday morning",
  "hotel_tier": "comfort",
  "risk_tolerance": "medium",
  "group_size": 4
}
```

#### Agent 2: Constraint Validator
**Purpose**: Check if enough information exists to generate a plan.

**Checks**: Origin known? Budget known? Duration known? Transport preference known? Conflicting constraints detected?

**Example conflict**: User wants luxury hotel but budget is ₹5,000/person.

#### Agent 3: Data Retriever
**Purpose**: Call tool functions to fetch data from Neo4j knowledge graph.

**Tools called**: `get_routes()`, `get_hotels()`, `get_activities()`, `get_transport_options()`, `get_restaurants()`, `get_waypoints()`

This agent does NOT invent data — it only returns what exists in the knowledge graph.

#### Agent 4: Planner Orchestrator
**Purpose**: Coordinate itinerary generation by calling the Graph Planning Engine.

**Calls**: `generate_candidates()`, `score_itinerary()`, `validate_itinerary()`, `generate_timeline()`

#### Agent 5: Explainer
**Purpose**: Generate a natural language explanation of why the selected itinerary was chosen.

**Example output**: *"This itinerary was selected because it stays within the ₹15,000 budget, avoids night driving, includes rafting and cafe time, and returns before Monday morning. The Jaipur option was rejected because the group preferred mountains."*

#### Agent 6: Replanner
**Purpose**: Handle delay simulation. Receives a delay event, identifies affected itinerary nodes, adjusts the plan, and explains changes.

### 7.3 LangGraph Workflow

```
START
  ↓
parse_chat (Agent 1)
  ↓
validate_constraints (Agent 2)
  ↓
if missing required fields → ask_clarification → parse_chat
else → retrieve_data (Agent 3)
  ↓
plan_itinerary (Agent 4 → Planning Engine)
  ↓
explain_plan (Agent 5)
  ↓
END
```

**Replanning workflow (triggered separately):**
```
START
  ↓
receive_delay_event
  ↓
replan_itinerary (Agent 6 → Replanner)
  ↓
explain_changes (Agent 5)
  ↓
END
```

### 7.4 State Schema

```python
from typing import TypedDict, List, Dict, Any, Optional

class TripState(TypedDict):
    # Input
    raw_chat: List[str]

    # Constraint extraction
    extracted_constraints: Dict[str, Any]
    missing_fields: List[str]
    conflict_report: Dict[str, Any]

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
    explanation: str

    # Replanning
    delay_event: Optional[Dict[str, Any]]
    replanned_itinerary: Optional[Dict[str, Any]]
    replanning_explanation: Optional[str]
```

---

## 8. Tool Layer

Agents access Neo4j data exclusively through tool functions. Tools abstract the data source — today they query Neo4j; tomorrow they could call real APIs.

### 8.1 Tool Functions

```python
def get_routes(origin: str, destination_type: str | None = None) -> list[dict]:
    """Returns route options matching origin and optional destination type.
    Queries Neo4j: MATCH (c:City)-[:ORIGIN_OF]->(r:Route)-[:ARRIVES_AT]->(d:City)"""

def get_hotels(destination: str, tier: str | None = None) -> list[dict]:
    """Returns hotels at a destination, optionally filtered by tier.
    Queries Neo4j: MATCH (c:City)-[:HAS_HOTEL]->(h:Hotel)"""

def get_activities(destination: str, tags: list[str] | None = None) -> list[dict]:
    """Returns activities at a destination, optionally filtered by tags.
    Queries Neo4j: MATCH (c:City)-[:HAS_ACTIVITY]->(a:Activity)"""

def get_transport_options(route_id: str, modes: list[str] | None = None) -> list[dict]:
    """Returns transport options for a route.
    Queries Neo4j: MATCH (r:Route)-[:HAS_TRANSPORT]->(t:TransportOption)"""

def get_restaurants(destination: str, route_id: str | None = None) -> list[dict]:
    """Returns restaurants at destination or on a route (highway stops).
    Queries Neo4j via city or ON_ROUTE relationship."""

def get_waypoints(route_id: str) -> list[dict]:
    """Returns intermediate stops on a route (breakfast stops, fuel, viewpoints).
    Queries Neo4j: MATCH (r:Route)-[:PASSES_THROUGH]->(w:Waypoint)"""
```

---

## 9. Graph Planning Engine

### 9.1 Trip Graph Model

The trip is modeled as a **directed acyclic graph (DAG)** where:

**Nodes** represent places or events:
- Home/origin, airport, railway station
- Cab pickup, hotel, restaurant
- Activity, viewpoint, fuel stop, rest stop
- Return point

**Node properties**: type, duration_minutes, cost_per_person, time_window, mandatory_or_optional, preference_tags, lat/lng

**Edges** represent transitions between events:
- From one location/event to the next
- Properties: duration_minutes, cost, mode, distance_km, risk_score, fatigue_score, scenic_score, night_driving_required

### 9.2 Candidate Generation

Candidates are generated by combinatorially exploring:
```
route × transport × hotel × activity_set × restaurant_set
```

Example candidate:
```
Route: Gurugram → Rishikesh
Transport: Cab with driver (comfort)
Hotel: Dummy Riverside Comfort Stay
Activities: Rafting + Ganga Aarti
Food: Highway Breakfast + Riverside Cafe lunch + Dinner
```

### 9.3 Scoring Function

```
final_score =
    preference_match_score
  + experience_score
  + comfort_score
  + scenic_score
  - cost_penalty
  - fatigue_penalty
  - risk_penalty
  - delay_penalty
  - constraint_violation_penalty (infinite for hard violations)
```

### 9.4 Hard Constraints (Must Not Be Violated)

| Constraint | Check |
|-----------|-------|
| Budget | total_cost_per_person ≤ budget_per_person |
| Return deadline | return_time ≤ return_deadline |
| Night driving | If avoid_night_driving=true, no travel legs after sunset |
| Mandatory activities | All must_include items present in itinerary |
| Minimum rest | At least N minutes of rest per day |

### 9.5 Soft Constraints (Influence Score)

Preferred cafe, scenic route, comfort hotel, less walking, more free time — these affect the score but don't disqualify a candidate.

### 9.6 Timeline Generation

Events are placed sequentially:
1. Start from departure time
2. Add travel leg duration
3. Add food stop duration
4. Add check-in time
5. Add rest window
6. Add activity windows
7. Add meal times
8. Add return travel

### 9.7 Replanning Logic

**Delay event input:**
```json
{
  "delay_type": "departure_delay",
  "delay_minutes": 90,
  "affected_event_id": "depart_gurugram"
}
```

**Event categories:**
| Category | Behavior | Example |
|----------|----------|---------|
| Locked | Cannot be shifted | Rafting slot, train departure |
| Flexible | Can be shifted | Lunch, cafe, rest window |
| Optional | Can be removed | Extra viewpoint, shopping |
| Mandatory | Must remain | Return journey, required activity |

**Replanning steps:**
1. Identify affected event
2. Shift all dependent events by delay amount
3. Check hard constraints
4. If constraints violated → modify flexible events
5. Drop optional events if needed
6. Shorten meal/rest windows if allowed
7. Recalculate cost and timing
8. Generate explanation of changes

---

## 10. Backend API

### 10.1 Endpoints

#### POST `/api/parse-chat`
```
Request:  { "chat_messages": ["Let's go from Gurugram", "Budget under 15k", ...] }
Response: {
  "extracted_constraints": { "origin": "Gurugram", "budget_per_person": 15000, ... },
  "missing_fields": ["exact_date"],
  "assumptions": { "exact_date": "next available weekend" }
}
```

#### POST `/api/generate-itinerary`
```
Request:  { "constraints": { "origin": "Gurugram", "destination_type": "mountains", ... } }
Response: {
  "recommended_itinerary": {
    "route": "Gurugram to Rishikesh",
    "tier": "comfort",
    "total_cost_per_person": 13750,
    "timeline": [...],
    "map_points": [...],
    "validation_report": {...},
    "score_breakdown": {...},
    "cost_breakdown": {...}
  },
  "alternatives": [...],
  "explanation": "This itinerary was selected because..."
}
```

#### POST `/api/simulate-delay`
```
Request:  { "itinerary_id": "iti_001", "delay_type": "departure_delay", "delay_minutes": 90 }
Response: {
  "updated_itinerary": {...},
  "changes": ["Breakfast shortened by 15 min", "Hotel rest reduced by 60 min", ...],
  "validation_report": {...},
  "explanation": "The revised plan still satisfies the return deadline."
}
```

---

## 11. Frontend Design

### 11.1 Technology

React + Vite for the app, Leaflet.js + OpenStreetMap for maps, Axios for API calls.

### 11.2 Components

| Component | Purpose |
|-----------|---------|
| `ChatRoom` | Paste/simulate group chat, send to API |
| `ExtractedPreferences` | Display parsed constraints |
| `ItineraryOptions` | Show recommended + alternative plans |
| `ItineraryTimeline` | Vertical timeline of events by day |
| `MapView` | Leaflet map with route line + POI markers |
| `CostBreakdown` | Per-person cost table |
| `CalendarView` | Calendar-style day/hour grid |
| `DelaySimulator` | Input delay type + minutes, see updated plan |

### 11.3 Map Integration

Use Leaflet.js with OpenStreetMap tiles (free, no API key):
- Origin marker (Gurugram)
- Destination marker (Rishikesh)
- Waypoint markers (breakfast stop, fuel)
- Hotel marker
- Activity markers
- Route polyline connecting all points
- Popup info on click

---

## 12. Dummy Data Design

All dummy data is in **JSON format** — structured identically to how a real API would return it. This ensures tool functions remain stable when swapping to real APIs.

### 12.1 Data Files

| File | Contents | Approx. Records |
|------|----------|-----------------|
| `seed_cities.json` | 4 cities (Gurugram, Jaipur, Rishikesh, Tirthan) | 4 |
| `seed_routes.json` | 3 routes with distances, drive times, risk | 3 |
| `seed_hotels.json` | 2-3 hotels per destination × 3 tiers | 12-18 |
| `seed_activities.json` | 3-5 activities per destination | 12-15 |
| `seed_restaurants.json` | 2-3 per destination + highway stops | 10-12 |
| `seed_transport.json` | 2-3 options per route × 3 tiers | 9-15 |
| `seed_waypoints.json` | 2-3 per route | 6-9 |

### 12.2 JSON Format Examples

See the mini-spec for Task 1 (`bucket_1_dummy_data.md`) for complete JSON schemas with examples.

---

## 13. Task Division

| Task # | Bucket Name | Files Owned |
|--------|-------------|-------------|
| Task 1 | Dummy Data & Seed Pipeline | `backend/data/*`, `backend/knowledge_graph/seed.py` |
| Task 2 | Agentic AI Pipeline (LangGraph) | `backend/agents/*` |
| Task 3 | Backend API & Integration | `backend/main.py`, `backend/config.py`, `backend/api/*`, `backend/models/*`, `docker-compose.yml` |
| Task 4 | Frontend UI & Visualization | `frontend/*` |
| Task 5 | Neo4j KG + Graph Planning Engine (Mainframe) | `backend/knowledge_graph/` (except seed.py), `backend/tools/*`, `backend/planner/*` |

---

## 14. Directory Structure

```
TripGraph/
├── backend/
│   ├── main.py                      # FastAPI entry         [Task 3]
│   ├── config.py                    # Env config            [Task 3]
│   ├── requirements.txt             # Dependencies          [Shared]
│   ├── api/                         #                       [Task 3]
│   │   ├── __init__.py
│   │   ├── chat_routes.py
│   │   ├── itinerary_routes.py
│   │   └── replanner_routes.py
│   ├── models/                      #                       [Task 3]
│   │   ├── __init__.py
│   │   ├── requests.py
│   │   └── responses.py
│   ├── agents/                      #                       [Task 2]
│   │   ├── __init__.py
│   │   ├── workflow.py
│   │   ├── state.py
│   │   ├── llm_client.py
│   │   ├── prompts.py
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── chat_parser.py
│   │       ├── constraint_validator.py
│   │       ├── data_retriever.py
│   │       ├── planner_orchestrator.py
│   │       ├── explainer.py
│   │       └── replanner_agent.py
│   ├── knowledge_graph/             #                       [Task 5]
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── schema.py
│   │   ├── queries.py
│   │   └── seed.py                  #                       [Task 1]
│   ├── tools/                       #                       [Task 5]
│   │   ├── __init__.py
│   │   ├── route_tool.py
│   │   ├── hotel_tool.py
│   │   ├── activity_tool.py
│   │   ├── transport_tool.py
│   │   ├── restaurant_tool.py
│   │   └── waypoint_tool.py
│   ├── planner/                     #                       [Task 5]
│   │   ├── __init__.py
│   │   ├── trip_graph_builder.py
│   │   ├── candidate_generator.py
│   │   ├── scorer.py
│   │   ├── validator.py
│   │   ├── timeline_generator.py
│   │   └── replanner.py
│   └── data/                        #                       [Task 1]
│       ├── seed_cities.json
│       ├── seed_routes.json
│       ├── seed_hotels.json
│       ├── seed_activities.json
│       ├── seed_restaurants.json
│       ├── seed_transport.json
│       └── seed_waypoints.json
├── frontend/                        #                       [Task 4]
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── api/tripApi.js
│       ├── components/
│       │   ├── layout/
│       │   ├── chat/
│       │   ├── preferences/
│       │   ├── itinerary/
│       │   ├── map/
│       │   ├── cost/
│       │   └── delay/
│       └── hooks/useItinerary.js
├── specs/
│   ├── MASTER_SPEC.md
│   ├── bucket_1_dummy_data.md
│   ├── bucket_2_agentic_pipeline.md
│   ├── bucket_3_backend_api.md
│   ├── bucket_4_frontend_ui.md
│   └── bucket_5_neo4j_planner.md
├── docker-compose.yml               #                       [Task 3]
├── .env.example                     #                       [Task 3]
├── .gitignore
└── README.md
```

---

## 15. Future Scope

After the MVP demo is complete, the system can be extended with:

| Category | Features |
|----------|----------|
| Real APIs | Google Maps, hotel inventory, flight data, cab/rental, weather, calendar export |
| Real-time | Live traffic, real disruptions, WebSocket updates |
| Booking | Deep-links to booking platforms, affiliate booking, payment splitting |
| Personalization | User preference learning, travel history, recommendation model |
| Group Intelligence | Voting on itineraries, conflict detection, compromise plans |
| ML/DL | Preference prediction, itinerary ranking, delay risk prediction, GNN for route scoring |

---

## 16. Example End-to-End Demo Flow

**Input chat:**
```
Ujjwal: We are planning a weekend trip from Gurugram.
Friend 1: Budget should be under ₹15,000 per person.
Friend 2: I want mountains, not Jaipur.
Friend 3: Please avoid night driving.
Friend 4: I want rafting and good cafes.
Ujjwal: We need to return before Monday morning.
```

**Extracted constraints:**
```json
{
  "origin": "Gurugram",
  "destination_type": "mountains",
  "budget_per_person": 15000,
  "avoid_night_driving": true,
  "must_include": ["rafting", "cafes"],
  "return_deadline": "Monday morning",
  "hotel_tier": "comfort",
  "trip_duration": "2D1N"
}
```

**Recommended itinerary (Rishikesh Comfort Plan):**
```
Day 1:
  06:00 — Depart Gurugram by cab
  09:00 — Breakfast at Highway Stop
  09:45 — Continue to Rishikesh
  13:00 — Arrive Rishikesh
  13:15 — Lunch at Riverside Cafe
  14:30 — Hotel check-in
  15:00 — Rest
  16:30 — Cafe/walk
  18:30 — Ganga Aarti
  20:00 — Dinner

Day 2:
  07:30 — Breakfast
  09:00 — River Rafting
  12:30 — Freshen up
  13:30 — Lunch
  15:00 — Depart Rishikesh
  21:30 — Arrive Gurugram ✓ (before Monday morning)
```

**Cost: ₹10,275/person** (within ₹15,000 budget ✓)

**Delay simulation (90-minute departure delay):**
```
07:30 — Depart (was 06:00)
10:30 — Shortened breakfast
14:30 — Arrive Rishikesh
15:00 — Hotel check-in
16:00 — Reduced rest
18:30 — Ganga Aarti ✓ (preserved)
Cafe → moved to Day 2 or removed
Rafting → still feasible ✓
Return deadline → still satisfied ✓
```
