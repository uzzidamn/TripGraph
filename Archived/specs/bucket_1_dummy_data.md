# Bucket 1: Dummy Data & Seed Pipeline — LLM-Ready Spec

> **Generated for**: Distributed LLM execution (Claude / Gemini session)
> **Priority**: P0 — All other buckets depend on this data
> **Reference**: This spec is self-contained. You may also read `specs/MASTER_SPEC.md` for full project context.

---

## Section A — Project Context

**TripGraph AI** is a GenAI-agentic group travel planner that converts WhatsApp-style group chat into structured, constraint-aware itineraries. It uses a Neo4j knowledge graph for travel data, a LangGraph agentic pipeline for orchestration, a deterministic Python planning engine for itinerary generation/scoring, and a React frontend for visualization.

**Your role (Bucket 1):** Create all realistic dummy travel data in JSON format and write a Python seed script that loads this data into the Neo4j knowledge graph. You own **what the data says** (content, values, realism). The Neo4j schema (node labels, relationship types, property names) is defined by Bucket 5 and frozen in Section B below.

The project supports **3 routes from Gurugram/Delhi NCR**: Jaipur (heritage), Rishikesh (adventure), Tirthan Valley (expedition). Each route has **3 travel tiers**: Budget, Comfort, Expedition.

---

## Section B — 🔒 Frozen Interface Contracts

> **CRITICAL**: The following schemas, property names, and relationship types are frozen. Your JSON data files MUST use these exact field names. Do not rename, add, or omit any field listed here.

### B.1 Neo4j Node Schemas

Every node in the knowledge graph has a label and a set of properties. Your JSON files must include **all required properties** for each entity.

#### `:City`
```
name: str              # Unique. "Gurugram", "Jaipur", "Rishikesh", "Tirthan Valley"
type: str              # "origin" | "heritage" | "mountains" | "nature"
lat: float             # Latitude (real coordinates from Google Maps)
lng: float             # Longitude
description: str       # 1-2 sentence description
```

#### `:Route`
```
route_id: str          # Unique. Format: "gurugram_<dest>_2d1n" (e.g., "gurugram_jaipur_2d1n")
distance_km: int       # Kilometers (real distance)
base_drive_minutes: int # Driving time in minutes (without stops)
risk_level: str        # "low" | "medium" | "high"
scenic_score: int      # 1-10 scale
recommended_for: list[str]  # Tags like ["heritage", "food", "family", "weekend"]
```
Note: `origin` and `destination` are NOT stored on the Route node — they are expressed via relationships (`:City -[:ORIGIN_OF]-> :Route -[:ARRIVES_AT]-> :City`). However, your JSON file MUST include `origin` and `destination` string fields so the seed script can create these relationships.

#### `:Hotel`
```
hotel_id: str          # Unique. Format: "<dest>_<tier>_<nn>" (e.g., "rishikesh_comfort_01")
name: str              # Realistic Indian hotel name
tier: str              # "budget" | "comfort" | "expedition"
price_per_night: float # In INR (₹). Per room, not per person.
rooms_required: int    # Number of rooms needed for a group of 4 (typically 1-2)
checkin_time: str      # "HH:MM" format (e.g., "14:00")
checkout_time: str     # "HH:MM" format (e.g., "11:00")
comfort_score: int     # 1-10 scale
lat: float
lng: float
amenities: list[str]   # e.g., ["wifi", "parking", "restaurant", "river_view"]
tags: list[str]        # e.g., ["riverside", "central", "heritage"]
```
Note: `destination` is NOT stored on the Hotel node — it is expressed via `:City -[:HAS_HOTEL]-> :Hotel`. Your JSON MUST include a `destination` string field for the seed script.

#### `:Activity`
```
activity_id: str       # Unique. Format: "<activity>_<dest>_<nn>" (e.g., "rafting_rishikesh_01")
name: str              # Descriptive name
category: str          # "adventure" | "cultural" | "food" | "nature" | "spiritual" | "shopping"
duration_minutes: int  # Typical duration
cost_per_person: float # In INR (₹). 0 for free activities.
available_slots: list[str]  # Time slots like ["09:00", "12:00", "15:00"]
risk_level: str        # "low" | "medium" | "high"
tags: list[str]        # e.g., ["adventure", "rafting", "water", "outdoor"]
lat: float             # Activity location
lng: float
```
Note: `destination` is NOT stored on the node. Your JSON MUST include a `destination` field for the seed script to create `:City -[:HAS_ACTIVITY]-> :Activity`.

#### `:Restaurant`
```
restaurant_id: str     # Unique
name: str
meal_types: list[str]  # ["breakfast", "lunch", "dinner"]
avg_cost_per_person: float  # In INR (₹)
avg_duration_minutes: int
tags: list[str]        # e.g., ["cafe", "river_view", "vegetarian_options"]
lat: float
lng: float
```
**Two types of restaurants exist:**
1. **Destination restaurants**: Located at the destination city. JSON has `destination: str` and `route_id: null`.
2. **Highway restaurants**: Located on the route (pit stops). JSON has `destination: null`, `route_id: str`, and `km_from_origin: int`.

The seed script creates different relationships:
- Destination: `:City -[:HAS_RESTAURANT]-> :Restaurant`
- Highway: `:Restaurant -[:ON_ROUTE]-> :Route` (with `km_from_origin` property)

#### `:TransportOption`
```
transport_id: str      # Unique. Format: "<mode>_<dest>_<tier>"
route_id: str          # Which route this option serves
mode: str              # "cab_with_driver" | "self_drive" | "bus" | "shared_cab" | "tempo_traveller"
tier: str              # "budget" | "comfort" | "expedition"
cost_total: float      # Total cost for the vehicle (not per person). In INR (₹).
capacity: int          # Max passengers (4 for cab, 12 for tempo)
base_duration_minutes: int  # Drive time
night_driving_allowed: bool # true/false
comfort_score: int     # 1-10
fatigue_score: int     # 1-10 (higher = more fatiguing)
tags: list[str]        # e.g., ["ac", "sedan", "professional_driver"]
```
Relationship: `:Route -[:HAS_TRANSPORT]-> :TransportOption`

#### `:Waypoint`
```
waypoint_id: str       # Unique
route_id: str          # Which route this is on
name: str              # e.g., "Murthal Dhaba Belt"
type: str              # "breakfast_stop" | "fuel_stop" | "viewpoint" | "rest_stop"
km_from_origin: int    # Distance from start
order: int             # Sequential order on the route (1, 2, 3...)
lat: float
lng: float
typical_stop_minutes: int  # How long people typically stop here
```
Relationship: `:Route -[:PASSES_THROUGH]-> :Waypoint` (with `order` and `km_from_origin` properties)

#### `:Tag`
```
name: str              # Unique. Lowercase, underscore-separated: "adventure", "river_view", "heritage"
```
Relationship: `:Activity -[:TAGGED]-> :Tag`, `:Restaurant -[:TAGGED]-> :Tag`, `:City -[:TAGGED]-> :Tag`

### B.2 Relationship Types (Complete List)

| Relationship | From → To | Properties |
|-------------|-----------|------------|
| `ORIGIN_OF` | City → Route | — |
| `ARRIVES_AT` | Route → City | — |
| `HAS_HOTEL` | City → Hotel | — |
| `HAS_ACTIVITY` | City → Activity | — |
| `HAS_RESTAURANT` | City → Restaurant | — |
| `HAS_TRANSPORT` | Route → TransportOption | — |
| `PASSES_THROUGH` | Route → Waypoint | order: int, km_from_origin: int |
| `TAGGED` | City/Activity/Restaurant → Tag | — |
| `NEAR` | Hotel → Activity | distance_km: float |
| `ON_ROUTE` | Restaurant → Route | km_from_origin: int |

### B.3 Schema Creation Cypher (Verbatim from MASTER_SPEC 6.5)

```cypher
CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:Route) REQUIRE r.route_id IS UNIQUE;
CREATE CONSTRAINT hotel_id IF NOT EXISTS FOR (h:Hotel) REQUIRE h.hotel_id IS UNIQUE;
CREATE CONSTRAINT activity_id IF NOT EXISTS FOR (a:Activity) REQUIRE a.activity_id IS UNIQUE;
CREATE CONSTRAINT restaurant_id IF NOT EXISTS FOR (r:Restaurant) REQUIRE r.restaurant_id IS UNIQUE;
CREATE CONSTRAINT transport_id IF NOT EXISTS FOR (t:TransportOption) REQUIRE t.transport_id IS UNIQUE;
CREATE CONSTRAINT waypoint_id IF NOT EXISTS FOR (w:Waypoint) REQUIRE w.waypoint_id IS UNIQUE;
CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE;

CREATE INDEX city_type IF NOT EXISTS FOR (c:City) ON (c.type);
CREATE INDEX hotel_tier IF NOT EXISTS FOR (h:Hotel) ON (h.tier);
CREATE INDEX activity_category IF NOT EXISTS FOR (a:Activity) ON (a.category);
```

### B.4 Complete JSON Examples (One Per Seed File)

These are ground truth examples. Every record you create must follow this exact structure.

**seed_cities.json example record:**
```json
{
  "name": "Rishikesh",
  "type": "mountains",
  "lat": 30.0869,
  "lng": 78.2676,
  "description": "Yoga and adventure capital. Rafting, cafes, Ganga Aarti, riverside walks.",
  "tags": ["adventure", "mountains", "spiritual", "nature", "cafes"]
}
```

**seed_routes.json example record:**
```json
{
  "route_id": "gurugram_rishikesh_2d1n",
  "origin": "Gurugram",
  "destination": "Rishikesh",
  "distance_km": 260,
  "base_drive_minutes": 390,
  "risk_level": "medium",
  "scenic_score": 7,
  "recommended_for": ["adventure", "weekend", "friends"]
}
```

**seed_hotels.json example record:**
```json
{
  "hotel_id": "rishikesh_comfort_01",
  "destination": "Rishikesh",
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
  "tags": ["riverside", "central"]
}
```

**seed_activities.json example record:**
```json
{
  "activity_id": "rafting_rishikesh_01",
  "destination": "Rishikesh",
  "name": "White Water Rafting (16 km)",
  "category": "adventure",
  "duration_minutes": 180,
  "cost_per_person": 1800,
  "available_slots": ["09:00", "12:00", "15:00"],
  "risk_level": "medium",
  "tags": ["adventure", "rafting", "water", "outdoor"],
  "lat": 30.1159,
  "lng": 78.3127
}
```

**seed_restaurants.json — destination example:**
```json
{
  "restaurant_id": "rishikesh_cafe_01",
  "destination": "Rishikesh",
  "route_id": null,
  "name": "Little Buddha Cafe",
  "meal_types": ["lunch", "dinner"],
  "avg_cost_per_person": 600,
  "avg_duration_minutes": 75,
  "tags": ["cafe", "river_view", "vegetarian_options", "instagram"],
  "lat": 30.1256,
  "lng": 78.3152
}
```

**seed_restaurants.json — highway example:**
```json
{
  "restaurant_id": "highway_amrik_01",
  "destination": null,
  "route_id": "gurugram_rishikesh_2d1n",
  "name": "Amrik Sukhdev Dhaba",
  "meal_types": ["breakfast", "lunch"],
  "avg_cost_per_person": 250,
  "avg_duration_minutes": 45,
  "km_from_origin": 35,
  "tags": ["dhaba", "highway", "parking", "quick_stop"],
  "lat": 29.2653,
  "lng": 76.8245
}
```

**seed_transport.json example record:**
```json
{
  "transport_id": "cab_rishikesh_comfort",
  "route_id": "gurugram_rishikesh_2d1n",
  "mode": "cab_with_driver",
  "tier": "comfort",
  "cost_total": 9500,
  "capacity": 4,
  "base_duration_minutes": 390,
  "night_driving_allowed": false,
  "comfort_score": 8,
  "fatigue_score": 3,
  "tags": ["ac", "sedan", "professional_driver"]
}
```

**seed_waypoints.json example record:**
```json
{
  "waypoint_id": "murthal_stop",
  "route_id": "gurugram_rishikesh_2d1n",
  "name": "Murthal Dhaba Belt",
  "type": "breakfast_stop",
  "km_from_origin": 35,
  "order": 1,
  "lat": 29.0281,
  "lng": 77.0474,
  "typical_stop_minutes": 30
}
```

### B.5 Import Paths (Frozen)

Your `seed.py` must import from Bucket 5's connection module:
```python
from backend.knowledge_graph.connection import get_driver
```

The schema creation script is already implemented at `backend/knowledge_graph/schema.py` and can be called:
```python
from backend.knowledge_graph.schema import create_schema
```

---

## Section C — Decisions & Defaults (Pre-Made)

Every decision below is final. Do not deviate.

| # | Decision | Value |
|---|----------|-------|
| 1 | Number of cities | 4: Gurugram (origin), Jaipur, Rishikesh, Tirthan Valley |
| 2 | Number of routes | 3: Gurugram→Jaipur, Gurugram→Rishikesh, Gurugram→Tirthan |
| 3 | Hotels per destination per tier | At least 1, ideally 2. Total: 12–18 hotels. |
| 4 | Budget hotel price range | ₹1,500–2,500/night, comfort_score 4–6 |
| 5 | Comfort hotel price range | ₹3,500–5,500/night, comfort_score 7–8 |
| 6 | Expedition hotel price range | ₹2,000–4,000/night (homestays/camps), comfort_score 5–7 |
| 7 | Activities per destination | 3–5. Total: 12–15 activities. |
| 8 | Restaurants per destination | 2–3 destination + 1–2 highway per route. Total: 10–15. |
| 9 | Transport options per route | At least 1 per tier (budget, comfort, expedition). Total: 9–15. |
| 10 | Waypoints per route | 2–3 per route. Total: 6–9. |
| 11 | Currency | All prices in INR (₹). No currency symbols in JSON — just numbers. |
| 12 | Coordinates | Use real lat/lng from Google Maps. Accuracy to 4 decimal places. |
| 13 | Tag format | Lowercase, underscore-separated: `river_view`, NOT `River View`. |
| 14 | ID format | Lowercase, underscore-separated. IDs must be globally unique. |
| 15 | Hotel `rooms_required` | For a group of 4: budget=2, comfort=1, expedition=1–2 |
| 16 | Hotel names | Use realistic-sounding names. NOT prefixed with "Dummy". |
| 17 | What if Neo4j is unreachable during seed? | Log error with `print(f"❌ Neo4j connection failed: {e}")` and `sys.exit(1)`. Do NOT silently continue. |
| 18 | Transport modes | `cab_with_driver`, `self_drive`, `bus`, `shared_cab`, `tempo_traveller` |
| 19 | Activity time slots | Realistic times only. No rafting at midnight. Adventure: morning slots. Cultural: afternoon/evening. |
| 20 | Waypoint `order` | Sequential per route, starting at 1. |
| 21 | Seed script idempotency | Use `MERGE` for all node creation (not `CREATE`). Running seed twice must not create duplicates. |
| 22 | Default group size | 4 (used for `rooms_required` and `capacity` calculations) |
| 23 | JSON format | Each file is a JSON array `[...]` of objects. Pretty-printed with 2-space indentation. |
| 24 | Highway restaurant detection | If `route_id` is not null and `destination` is null → highway restaurant. Otherwise → destination restaurant. |
| 25 | Tag nodes | After seeding all entities, extract ALL unique tags from cities, activities, and restaurants, create `:Tag` nodes, and create `:TAGGED` relationships. |

---

## Section D — Step-by-Step Build Instructions

### Step 1: Create `backend/data/seed_cities.json`

Create exactly 4 city records. Use the example in Section B.4 as a template.

Cities to create:
- **Gurugram**: type="origin", lat=28.4595, lng=77.0266
- **Jaipur**: type="heritage", lat=26.9124, lng=75.7873
- **Rishikesh**: type="mountains", lat=30.0869, lng=78.2676
- **Tirthan Valley**: type="mountains", lat=31.6381, lng=77.4511

Each city must have a `tags` field listing relevant category tags.

### Step 2: Create `backend/data/seed_routes.json`

Create exactly 3 route records:
- `gurugram_jaipur_2d1n`: 240 km, 300 min, risk=low, scenic=5
- `gurugram_rishikesh_2d1n`: 260 km, 390 min, risk=medium, scenic=7
- `gurugram_tirthan_3d2n`: 510 km, 720 min, risk=high, scenic=9

### Step 3: Create `backend/data/seed_hotels.json`

Create 12–18 hotels. For each of the 3 destinations × 3 tiers, create at least 1 hotel (ideally 2). Include realistic Indian hotel names, real coordinates near the destination, and appropriate amenities.

Example Jaipur hotels:
- Budget: "Pink City Hostel" — ₹1,800/night, comfort_score=5
- Comfort: "Heritage Haveli Resort" — ₹4,500/night, comfort_score=8
- Expedition: "Desert Camp Retreat" — ₹3,000/night, comfort_score=6

### Step 4: Create `backend/data/seed_activities.json`

Create 12–15 activities. Distribute across destinations:

| Destination | Suggested Activities |
|-------------|---------------------|
| Jaipur | Amber Fort visit, Nahargarh sunset, old city food walk, bazaar shopping, Jal Mahal boat ride |
| Rishikesh | White water rafting, Ganga Aarti, Beatles Ashram, bungee jumping, riverside cafe hopping |
| Tirthan Valley | Great Himalayan NP trek, trout fishing, waterfall hike, village walk, stargazing |

Each activity must have realistic `cost_per_person`, `duration_minutes`, and `available_slots`.

### Step 5: Create `backend/data/seed_restaurants.json`

Create 10–15 restaurants. Mix of destination restaurants and highway stops.

For each route, include at least 1 highway dhaba/restaurant (with `destination: null`, `route_id: "<id>"`, `km_from_origin: <int>`).

### Step 6: Create `backend/data/seed_transport.json`

Create 9–15 transport options. For each route, provide at least 1 option per tier:
- **Budget**: bus or shared_cab — cost_total ₹1,500–4,000
- **Comfort**: cab_with_driver — cost_total ₹7,000–15,000
- **Expedition**: self_drive — cost_total ₹3,000–8,000

Set `night_driving_allowed: false` for all `cab_with_driver` and `bus` options. Set `night_driving_allowed: true` only for `self_drive`.

### Step 7: Create `backend/data/seed_waypoints.json`

Create 6–9 waypoints. For each route, create 2–3 stops:
- Breakfast/food stop near the start
- Fuel stop midway
- Viewpoint or rest stop (if applicable)

Use real place names and coordinates along the actual highway routes.

### Step 8: Create `backend/knowledge_graph/seed.py`

This script reads all JSON files and loads them into Neo4j. Full implementation:

```python
"""
Seed script: Loads all JSON data into the Neo4j knowledge graph.
Usage: PYTHONPATH=. python -m backend.knowledge_graph.seed
Requires: Neo4j running at bolt://localhost:7687 (see .env.example)
"""
import json
import sys
from pathlib import Path
from backend.knowledge_graph.connection import get_driver
from backend.knowledge_graph.schema import create_schema

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename: str) -> list[dict]:
    """Load a JSON seed file from the data directory."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def seed_cities(tx):
    """Create City nodes and their Tag relationships."""
    cities = load_json("seed_cities.json")
    for city in cities:
        tx.run(
            "MERGE (c:City {name: $name}) "
            "SET c.type = $type, c.lat = $lat, c.lng = $lng, "
            "c.description = $description",
            name=city["name"], type=city["type"],
            lat=city["lat"], lng=city["lng"],
            description=city["description"]
        )
        # Create Tag nodes and TAGGED relationships
        for tag in city.get("tags", []):
            tx.run(
                "MERGE (t:Tag {name: $tag}) "
                "WITH t "
                "MATCH (c:City {name: $city_name}) "
                "MERGE (c)-[:TAGGED]->(t)",
                tag=tag, city_name=city["name"]
            )
    print(f"  ✅ Seeded {len(cities)} cities")


def seed_routes(tx):
    """Create Route nodes and ORIGIN_OF/ARRIVES_AT relationships."""
    routes = load_json("seed_routes.json")
    for route in routes:
        tx.run(
            "MERGE (r:Route {route_id: $route_id}) "
            "SET r.distance_km = $distance_km, "
            "r.base_drive_minutes = $base_drive_minutes, "
            "r.risk_level = $risk_level, "
            "r.scenic_score = $scenic_score, "
            "r.recommended_for = $recommended_for",
            **{k: route[k] for k in ["route_id", "distance_km", "base_drive_minutes",
                                       "risk_level", "scenic_score", "recommended_for"]}
        )
        tx.run(
            "MATCH (origin:City {name: $origin}), (r:Route {route_id: $route_id}) "
            "MERGE (origin)-[:ORIGIN_OF]->(r)",
            origin=route["origin"], route_id=route["route_id"]
        )
        tx.run(
            "MATCH (dest:City {name: $destination}), (r:Route {route_id: $route_id}) "
            "MERGE (r)-[:ARRIVES_AT]->(dest)",
            destination=route["destination"], route_id=route["route_id"]
        )
    print(f"  ✅ Seeded {len(routes)} routes")


def seed_hotels(tx):
    """Create Hotel nodes and HAS_HOTEL relationships."""
    hotels = load_json("seed_hotels.json")
    for hotel in hotels:
        tx.run(
            "MERGE (h:Hotel {hotel_id: $hotel_id}) "
            "SET h.name = $name, h.tier = $tier, "
            "h.price_per_night = $price_per_night, "
            "h.rooms_required = $rooms_required, "
            "h.checkin_time = $checkin_time, "
            "h.checkout_time = $checkout_time, "
            "h.comfort_score = $comfort_score, "
            "h.lat = $lat, h.lng = $lng, "
            "h.amenities = $amenities, h.tags = $tags",
            **{k: hotel[k] for k in ["hotel_id", "name", "tier", "price_per_night",
                                       "rooms_required", "checkin_time", "checkout_time",
                                       "comfort_score", "lat", "lng", "amenities", "tags"]}
        )
        tx.run(
            "MATCH (c:City {name: $destination}), (h:Hotel {hotel_id: $hotel_id}) "
            "MERGE (c)-[:HAS_HOTEL]->(h)",
            destination=hotel["destination"], hotel_id=hotel["hotel_id"]
        )
    print(f"  ✅ Seeded {len(hotels)} hotels")


def seed_activities(tx):
    """Create Activity nodes, HAS_ACTIVITY and TAGGED relationships."""
    activities = load_json("seed_activities.json")
    for act in activities:
        tx.run(
            "MERGE (a:Activity {activity_id: $activity_id}) "
            "SET a.name = $name, a.category = $category, "
            "a.duration_minutes = $duration_minutes, "
            "a.cost_per_person = $cost_per_person, "
            "a.available_slots = $available_slots, "
            "a.risk_level = $risk_level, "
            "a.tags = $tags, a.lat = $lat, a.lng = $lng",
            **{k: act[k] for k in ["activity_id", "name", "category", "duration_minutes",
                                     "cost_per_person", "available_slots", "risk_level",
                                     "tags", "lat", "lng"]}
        )
        tx.run(
            "MATCH (c:City {name: $destination}), (a:Activity {activity_id: $activity_id}) "
            "MERGE (c)-[:HAS_ACTIVITY]->(a)",
            destination=act["destination"], activity_id=act["activity_id"]
        )
        for tag in act.get("tags", []):
            tx.run(
                "MERGE (t:Tag {name: $tag}) "
                "WITH t "
                "MATCH (a:Activity {activity_id: $activity_id}) "
                "MERGE (a)-[:TAGGED]->(t)",
                tag=tag, activity_id=act["activity_id"]
            )
    print(f"  ✅ Seeded {len(activities)} activities")


def seed_restaurants(tx):
    """Create Restaurant nodes with HAS_RESTAURANT or ON_ROUTE relationships."""
    restaurants = load_json("seed_restaurants.json")
    for rest in restaurants:
        tx.run(
            "MERGE (r:Restaurant {restaurant_id: $restaurant_id}) "
            "SET r.name = $name, r.meal_types = $meal_types, "
            "r.avg_cost_per_person = $avg_cost_per_person, "
            "r.avg_duration_minutes = $avg_duration_minutes, "
            "r.tags = $tags, r.lat = $lat, r.lng = $lng",
            **{k: rest[k] for k in ["restaurant_id", "name", "meal_types",
                                      "avg_cost_per_person", "avg_duration_minutes",
                                      "tags", "lat", "lng"]}
        )
        if rest.get("destination"):
            # Destination restaurant
            tx.run(
                "MATCH (c:City {name: $destination}), (r:Restaurant {restaurant_id: $rid}) "
                "MERGE (c)-[:HAS_RESTAURANT]->(r)",
                destination=rest["destination"], rid=rest["restaurant_id"]
            )
        elif rest.get("route_id"):
            # Highway restaurant
            tx.run(
                "MATCH (route:Route {route_id: $route_id}), (r:Restaurant {restaurant_id: $rid}) "
                "MERGE (r)-[:ON_ROUTE {km_from_origin: $km}]->(route)",
                route_id=rest["route_id"], rid=rest["restaurant_id"],
                km=rest.get("km_from_origin", 0)
            )
        for tag in rest.get("tags", []):
            tx.run(
                "MERGE (t:Tag {name: $tag}) "
                "WITH t "
                "MATCH (r:Restaurant {restaurant_id: $rid}) "
                "MERGE (r)-[:TAGGED]->(t)",
                tag=tag, rid=rest["restaurant_id"]
            )
    print(f"  ✅ Seeded {len(restaurants)} restaurants")


def seed_transport(tx):
    """Create TransportOption nodes and HAS_TRANSPORT relationships."""
    transport = load_json("seed_transport.json")
    for t in transport:
        tx.run(
            "MERGE (to:TransportOption {transport_id: $transport_id}) "
            "SET to.mode = $mode, to.tier = $tier, "
            "to.cost_total = $cost_total, to.capacity = $capacity, "
            "to.base_duration_minutes = $base_duration_minutes, "
            "to.night_driving_allowed = $night_driving_allowed, "
            "to.comfort_score = $comfort_score, "
            "to.fatigue_score = $fatigue_score, "
            "to.tags = $tags",
            **{k: t[k] for k in ["transport_id", "mode", "tier", "cost_total",
                                   "capacity", "base_duration_minutes",
                                   "night_driving_allowed", "comfort_score",
                                   "fatigue_score", "tags"]}
        )
        tx.run(
            "MATCH (r:Route {route_id: $route_id}), (to:TransportOption {transport_id: $tid}) "
            "MERGE (r)-[:HAS_TRANSPORT]->(to)",
            route_id=t["route_id"], tid=t["transport_id"]
        )
    print(f"  ✅ Seeded {len(transport)} transport options")


def seed_waypoints(tx):
    """Create Waypoint nodes and PASSES_THROUGH relationships."""
    waypoints = load_json("seed_waypoints.json")
    for wp in waypoints:
        tx.run(
            "MERGE (w:Waypoint {waypoint_id: $waypoint_id}) "
            "SET w.name = $name, w.type = $type, "
            "w.km_from_origin = $km_from_origin, "
            "w.lat = $lat, w.lng = $lng, "
            "w.typical_stop_minutes = $typical_stop_minutes, "
            "w.order = $order",
            **{k: wp[k] for k in ["waypoint_id", "name", "type", "km_from_origin",
                                    "lat", "lng", "typical_stop_minutes", "order"]}
        )
        tx.run(
            "MATCH (r:Route {route_id: $route_id}), (w:Waypoint {waypoint_id: $wid}) "
            "MERGE (r)-[:PASSES_THROUGH {order: $order, km_from_origin: $km}]->(w)",
            route_id=wp["route_id"], wid=wp["waypoint_id"],
            order=wp["order"], km=wp["km_from_origin"]
        )
    print(f"  ✅ Seeded {len(waypoints)} waypoints")


def seed_all():
    """Run complete seed pipeline."""
    try:
        driver = get_driver()
        driver.verify_connectivity()
        print("🔗 Connected to Neo4j")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        sys.exit(1)

    # Create schema first
    create_schema()

    with driver.session() as session:
        session.execute_write(seed_cities)
        session.execute_write(seed_routes)
        session.execute_write(seed_hotels)
        session.execute_write(seed_activities)
        session.execute_write(seed_restaurants)
        session.execute_write(seed_transport)
        session.execute_write(seed_waypoints)

    print("\n✅ All seed data loaded into Neo4j successfully!")


if __name__ == "__main__":
    seed_all()
```

---

## Section E — File Manifest

```
backend/data/seed_cities.json          — 4 city records
backend/data/seed_routes.json          — 3 route records
backend/data/seed_hotels.json          — 12-18 hotel records (all 3 tiers × 3 destinations)
backend/data/seed_activities.json      — 12-15 activity records
backend/data/seed_restaurants.json     — 10-15 restaurant records (destination + highway)
backend/data/seed_transport.json       — 9-15 transport option records
backend/data/seed_waypoints.json       — 6-9 waypoint records
backend/knowledge_graph/seed.py        — Neo4j seed script (imports from Bucket 5's connection.py)
specs/logs/bucket_1_decisions.md       — Decisions & assumptions log (see Section G)
```

---

## Section F — Integration Verification Checklist & Test Script

### Pre-Commit Checklist
- [ ] All 7 JSON files are valid JSON (`python -m json.tool backend/data/<file>.json`)
- [ ] Every entity has a unique ID field matching the format in Section B
- [ ] Every hotel/activity/restaurant has real lat/lng coordinates
- [ ] Every destination has at least 1 hotel per tier (budget, comfort, expedition)
- [ ] Every route has at least 1 transport option per tier
- [ ] All prices are realistic for Indian travel (no ₹100 hotels or ₹50,000 hostels)
- [ ] All drive times match real Google Maps estimates (±15%)
- [ ] Activity `available_slots` have realistic times
- [ ] Highway restaurants have correct `km_from_origin` values
- [ ] Waypoint `order` values are sequential per route (1, 2, 3...)
- [ ] All tags are lowercase, underscore-separated
- [ ] `seed.py` runs without errors against a fresh Neo4j
- [ ] Running `seed.py` twice does not create duplicates (MERGE is idempotent)
- [ ] No `TODO` or `pass` in any function
- [ ] Import paths are correct: `from backend.knowledge_graph.connection import get_driver`
- [ ] `specs/logs/bucket_1_decisions.md` is created and filled

### Runnable Validation Script

Create this file as `backend/tests/test_bucket_1.py`:

```python
"""
Bucket 1 Validation Script.
Validates JSON seed files for schema compliance and data quality.
Run: PYTHONPATH=. python backend/tests/test_bucket_1.py
"""
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PASS = 0
FAIL = 0

def check(condition: bool, msg: str):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {msg}")
    else:
        FAIL += 1
        print(f"  ❌ {msg}")

def load(filename: str) -> list:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)

print("=" * 60)
print("Bucket 1 — Seed Data Validation")
print("=" * 60)

# Cities
print("\n📍 Cities:")
cities = load("seed_cities.json")
check(len(cities) == 4, f"Exactly 4 cities (found {len(cities)})")
check(all("name" in c and "type" in c and "lat" in c and "lng" in c for c in cities), "All cities have required fields")
check(any(c["name"] == "Gurugram" for c in cities), "Gurugram exists as origin")
city_names = {c["name"] for c in cities}

# Routes
print("\n🛣️ Routes:")
routes = load("seed_routes.json")
check(len(routes) == 3, f"Exactly 3 routes (found {len(routes)})")
check(all("route_id" in r and "origin" in r and "destination" in r for r in routes), "All routes have required fields")
check(all(r["origin"] in city_names and r["destination"] in city_names for r in routes), "All route endpoints are valid cities")
route_ids = {r["route_id"] for r in routes}

# Hotels
print("\n🏨 Hotels:")
hotels = load("seed_hotels.json")
check(len(hotels) >= 9, f"At least 9 hotels (found {len(hotels)})")
check(all("hotel_id" in h and "destination" in h and "tier" in h for h in hotels), "All hotels have required fields")
for dest in ["Jaipur", "Rishikesh", "Tirthan Valley"]:
    dest_hotels = [h for h in hotels if h["destination"] == dest]
    tiers = {h["tier"] for h in dest_hotels}
    check({"budget", "comfort", "expedition"}.issubset(tiers), f"{dest} has all 3 tiers")

# Activities
print("\n🎯 Activities:")
activities = load("seed_activities.json")
check(len(activities) >= 9, f"At least 9 activities (found {len(activities)})")
check(all("activity_id" in a and "destination" in a for a in activities), "All activities have required fields")

# Restaurants
print("\n🍽️ Restaurants:")
restaurants = load("seed_restaurants.json")
check(len(restaurants) >= 9, f"At least 9 restaurants (found {len(restaurants)})")
highway = [r for r in restaurants if r.get("route_id") and not r.get("destination")]
check(len(highway) >= 3, f"At least 3 highway restaurants (found {len(highway)})")

# Transport
print("\n🚗 Transport:")
transport = load("seed_transport.json")
check(len(transport) >= 9, f"At least 9 transport options (found {len(transport)})")
for rid in route_ids:
    rt = [t for t in transport if t["route_id"] == rid]
    tiers = {t["tier"] for t in rt}
    check({"budget", "comfort", "expedition"}.issubset(tiers), f"Route {rid} has all 3 tiers")

# Waypoints
print("\n📌 Waypoints:")
waypoints = load("seed_waypoints.json")
check(len(waypoints) >= 6, f"At least 6 waypoints (found {len(waypoints)})")
check(all("order" in w and "route_id" in w for w in waypoints), "All waypoints have order and route_id")

# Unique IDs
print("\n🔑 Uniqueness:")
all_ids = (
    [h["hotel_id"] for h in hotels] +
    [a["activity_id"] for a in activities] +
    [r["restaurant_id"] for r in restaurants] +
    [t["transport_id"] for t in transport] +
    [w["waypoint_id"] for w in waypoints] +
    [r["route_id"] for r in routes]
)
check(len(all_ids) == len(set(all_ids)), "All IDs are globally unique")

# Summary
print("\n" + "=" * 60)
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("🎉 ALL CHECKS PASSED!")
else:
    print("⚠️ Some checks failed. Review the output above.")
    sys.exit(1)
```

---

## Section G — 📋 Assumptions & Decisions Log (Output File)

**You MUST create this file as part of your output:**

```
specs/logs/bucket_1_decisions.md
```

Use this template:

```markdown
# Bucket 1 — Decisions & Assumptions Log
Generated by: [Model Name, e.g., "Claude Opus 4"] on [Date, e.g., "2026-06-14"]

## Pre-Specified Decisions Applied
[List every decision from Section C that was applied, with the actual value used]

## Unspecified Decisions Made During Build
[List every decision the spec did not cover, what you decided, and why]

## Deviations from Spec
[Any case where the spec said X but you built Y, with justification]

## External Assumptions
[Anything assumed about the environment, other buckets, or runtime]

## Validation Results
[Paste the output of running backend/tests/test_bucket_1.py]
```

---

## Git Commit Protocol

```
1. Stage all files listed in the File Manifest (Section E)
2. Stage specs/logs/bucket_1_decisions.md
3. Stage backend/tests/test_bucket_1.py
4. Commit message: "Bucket 1: Dummy data seed files and Neo4j seed script — [date]"
5. Branch: bucket-1/implementation
6. Push to origin
7. Do NOT merge to main — push to the feature branch only
```

---

## Data Quality Bar

- All Python code must be typed (no bare `dict` — use type hints on function signatures)
- All functions must have docstrings
- Error handling: every Neo4j call in `seed.py` must handle connection failures gracefully
- `requirements.txt` is NOT your responsibility (Bucket 5 already created it with `neo4j` and `python-dotenv`)
- The bucket must be runnable in isolation: `PYTHONPATH=. python backend/tests/test_bucket_1.py` must pass without Neo4j running
- The decisions log is mandatory. A bucket without `specs/logs/bucket_1_decisions.md` is incomplete.
