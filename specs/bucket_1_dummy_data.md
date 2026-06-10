# Task 1: Dummy Data & Seed Pipeline — Mini Spec

> **Owner**: Task 1 assignee
> **Priority**: P0 — Start immediately (other tasks depend on this data)
> **Estimated effort**: 8-10 days
> **Reference**: Read `MASTER_SPEC.md` (same folder) for full project context

---

## Overview

Your job is to create **realistic dummy travel data** in JSON format and write a Python script that seeds this data into the Neo4j knowledge graph. The data should look exactly like what a real travel API would return — because when the project eventually swaps to real APIs, the tool functions should not need to change.

You own **what the data says** (content, values, realism). The Mainframe (Task 5) owns **how the data is stored** (Neo4j schema, node labels, relationships).

---

## What You Deliver

| # | Deliverable | File |
|---|------------|------|
| 1 | Cities seed data | `backend/data/seed_cities.json` |
| 2 | Routes seed data | `backend/data/seed_routes.json` |
| 3 | Hotels seed data | `backend/data/seed_hotels.json` |
| 4 | Activities seed data | `backend/data/seed_activities.json` |
| 5 | Restaurants seed data | `backend/data/seed_restaurants.json` |
| 6 | Transport options seed data | `backend/data/seed_transport.json` |
| 7 | Waypoints seed data | `backend/data/seed_waypoints.json` |
| 8 | Neo4j seed script | `backend/knowledge_graph/seed.py` |

---

## Step-by-Step Instructions

### Step 1: Understand the Data Domain

The project supports **3 routes from Gurugram/Delhi NCR**:

| Route | Destination Type | Character |
|-------|-----------------|-----------|
| Gurugram → Jaipur | Heritage | Heritage sites, food, family-friendly, ~5hr drive |
| Gurugram → Rishikesh | Adventure | Rafting, cafes, spiritual, ~6.5hr drive |
| Gurugram → Tirthan/Jibhi | Expedition | Scenic mountains, nature, ~12hr drive |

Each route has **3 tiers**: Budget, Comfort, Expedition.

### Step 2: Create `seed_cities.json`

Create 4 city entries. Each city must have coordinates (look up real lat/lng on Google Maps).

```json
[
  {
    "name": "Gurugram",
    "type": "origin",
    "lat": 28.4595,
    "lng": 77.0266,
    "description": "Starting point in Delhi NCR. Major IT hub with easy highway access."
  },
  {
    "name": "Jaipur",
    "type": "heritage",
    "lat": 26.9124,
    "lng": 75.7873,
    "description": "The Pink City. Known for forts, palaces, food, and heritage walks."
  },
  {
    "name": "Rishikesh",
    "type": "mountains",
    "lat": 30.0869,
    "lng": 78.2676,
    "description": "Yoga and adventure capital. Rafting, cafes, Ganga Aarti, riverside walks."
  },
  {
    "name": "Tirthan Valley",
    "type": "mountains",
    "lat": 31.6381,
    "lng": 77.4511,
    "description": "Remote Himalayan valley. Pristine nature, trout fishing, scenic trails."
  }
]
```

### Step 3: Create `seed_routes.json`

Each route connects an origin city to a destination city. Research realistic distances and drive times.

```json
[
  {
    "route_id": "gurugram_jaipur_2d1n",
    "origin": "Gurugram",
    "destination": "Jaipur",
    "distance_km": 240,
    "base_drive_minutes": 300,
    "risk_level": "low",
    "scenic_score": 5,
    "recommended_for": ["heritage", "food", "family", "weekend"]
  },
  {
    "route_id": "gurugram_rishikesh_2d1n",
    "origin": "Gurugram",
    "destination": "Rishikesh",
    "distance_km": 260,
    "base_drive_minutes": 390,
    "risk_level": "medium",
    "scenic_score": 7,
    "recommended_for": ["adventure", "weekend", "friends"]
  },
  {
    "route_id": "gurugram_tirthan_3d2n",
    "origin": "Gurugram",
    "destination": "Tirthan Valley",
    "distance_km": 510,
    "base_drive_minutes": 720,
    "risk_level": "high",
    "scenic_score": 9,
    "recommended_for": ["expedition", "nature", "long_weekend"]
  }
]
```

### Step 4: Create `seed_hotels.json`

Create **2-3 hotels per destination × 3 tiers** = 12-18 total entries. Use realistic Indian hotel prices. Every hotel needs lat/lng coordinates.

**Required fields per hotel:**
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

**Guidelines:**
- Budget tier: ₹1,500-2,500/night, comfort_score 4-6
- Comfort tier: ₹3,500-5,500/night, comfort_score 7-8
- Expedition tier: ₹2,000-4,000/night (homestays/camps), comfort_score 5-7
- Use names that sound realistic but clearly fictional (prefix with "Dummy" is NOT needed — use real-sounding names)
- Include variety: some with river views, some with parking, some with restaurant

### Step 5: Create `seed_activities.json`

Create **3-5 activities per destination** = 12-15 total. Mix of adventure, cultural, food, nature categories.

**Required fields:**
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
  "tags": ["adventure", "rafting", "water", "outdoor"]
}
```

**Example activities by destination:**

| Destination | Activities to include |
|-------------|----------------------|
| Jaipur | Amber Fort visit, Nahargarh sunset, food walk in old city, bazaar shopping, Jal Mahal boat ride |
| Rishikesh | White water rafting, Ganga Aarti, Beatles Ashram, bungee jumping, riverside cafe hopping |
| Tirthan | Great Himalayan NP trek, trout fishing, waterfall hike, village walk, stargazing |

### Step 6: Create `seed_restaurants.json`

Create **2-3 per destination + 1-2 highway stops per route** = 10-12 total.

**Two types of restaurants:**

**1. Destination restaurants** (at the destination city):
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

**2. Highway restaurants** (on the route, for pit stops):
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

### Step 7: Create `seed_transport.json`

Create **2-3 transport options per route × 3 tiers** = 9-15 total.

**Required fields:**
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

**Transport modes to include:**
- `cab_with_driver` — comfort tier, professional driver, no night driving concern
- `self_drive` — expedition tier, rental car, driver fatigue matters
- `bus` — budget tier, ISBT/Volvo, fixed schedules
- `shared_cab` — budget tier, shared cost
- `tempo_traveller` — comfort/budget for larger groups (8-12 people)

### Step 8: Create `seed_waypoints.json`

Create **2-3 intermediate stops per route** = 6-9 total. These are highway stops for food, fuel, or scenic viewpoints.

```json
[
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
  },
  {
    "waypoint_id": "roorkee_fuel",
    "route_id": "gurugram_rishikesh_2d1n",
    "name": "Roorkee Fuel Station",
    "type": "fuel_stop",
    "km_from_origin": 180,
    "order": 2,
    "lat": 29.8543,
    "lng": 77.8880,
    "typical_stop_minutes": 10
  }
]
```

### Step 9: Write `seed.py` — Neo4j Seed Script

This script reads all JSON files and loads them into Neo4j. Coordinate with the Mainframe (Task 5) for the Neo4j connection details.

```python
"""
Seed script: Loads all JSON data into the Neo4j knowledge graph.
Usage: python -m backend.knowledge_graph.seed
"""
import json
from pathlib import Path
from backend.knowledge_graph.connection import get_driver

DATA_DIR = Path(__file__).parent.parent / "data"

def load_json(filename: str) -> list[dict]:
    with open(DATA_DIR / filename) as f:
        return json.load(f)

def seed_cities(tx):
    cities = load_json("seed_cities.json")
    for city in cities:
        tx.run(
            "MERGE (c:City {name: $name}) "
            "SET c.type = $type, c.lat = $lat, c.lng = $lng, "
            "c.description = $description",
            **city
        )

def seed_routes(tx):
    routes = load_json("seed_routes.json")
    for route in routes:
        tx.run(
            "MERGE (r:Route {route_id: $route_id}) "
            "SET r.distance_km = $distance_km, "
            "r.base_drive_minutes = $base_drive_minutes, "
            "r.risk_level = $risk_level, r.scenic_score = $scenic_score, "
            "r.recommended_for = $recommended_for",
            **route
        )
        # Create relationships
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

def seed_hotels(tx):
    hotels = load_json("seed_hotels.json")
    for hotel in hotels:
        tx.run(
            "MERGE (h:Hotel {hotel_id: $hotel_id}) "
            "SET h.name = $name, h.tier = $tier, "
            "h.price_per_night = $price_per_night, "
            "h.comfort_score = $comfort_score, "
            "h.checkin_time = $checkin_time, h.checkout_time = $checkout_time, "
            "h.lat = $lat, h.lng = $lng, h.amenities = $amenities",
            **hotel
        )
        tx.run(
            "MATCH (c:City {name: $destination}), (h:Hotel {hotel_id: $hotel_id}) "
            "MERGE (c)-[:HAS_HOTEL]->(h)",
            destination=hotel["destination"], hotel_id=hotel["hotel_id"]
        )

# Similar functions for activities, restaurants, transport, waypoints...
# Follow the same pattern: MERGE node, then create relationships

def seed_all():
    driver = get_driver()
    with driver.session() as session:
        session.execute_write(seed_cities)
        session.execute_write(seed_routes)
        session.execute_write(seed_hotels)
        # ... seed_activities, seed_restaurants, seed_transport, seed_waypoints
        # ... seed_tags and TAGGED relationships
    print("✅ All seed data loaded into Neo4j")

if __name__ == "__main__":
    seed_all()
```

> **Important**: After seeding, also create `Tag` nodes and `TAGGED` relationships. For example, if an activity has `tags: ["adventure", "rafting"]`, create `(:Tag {name: "adventure"})` and `(:Activity)-[:TAGGED]->(:Tag)`.

---

## Data Quality Checklist

Before submitting your PR, verify:

- [ ] All JSON files are valid JSON (use `python -m json.tool filename.json`)
- [ ] Every entity has a unique ID field
- [ ] Every hotel/activity/restaurant has lat/lng coordinates (real ones from Google Maps)
- [ ] Every hotel has entries in all 3 tiers for each destination
- [ ] Every route has transport options in all 3 tiers
- [ ] Prices are in INR (₹) and realistic for Indian travel
- [ ] Drive times are realistic (check Google Maps)
- [ ] Available slots for activities make sense (rafting not at midnight)
- [ ] Highway restaurants have `km_from_origin` values that match the route
- [ ] Waypoint `order` values are sequential per route
- [ ] Tags are consistent (use lowercase, underscore-separated: `river_view`, not `River View`)
- [ ] The seed script runs without errors against a fresh Neo4j instance

---

## Coordination with Other Tasks

| You need from | What |
|--------------|------|
| Task 5 (Mainframe) | Neo4j schema definition (node labels, relationship types, property names) |
| Task 5 (Mainframe) | Neo4j connection details (`connection.py` import) |

| Others need from you | What |
|---------------------|------|
| Task 2 (Agents) | Sample tool function return values (so they can build mock data) |
| Task 5 (Mainframe) | The actual data content to populate the knowledge graph |

---

## Git Workflow

```bash
git checkout -b bucket-1/seed-cities-routes
# Create seed_cities.json and seed_routes.json
git add backend/data/seed_cities.json backend/data/seed_routes.json
git commit -m "Task 1: Add city and route seed data"
git push origin bucket-1/seed-cities-routes
# Open PR on GitHub

git checkout main && git pull
git checkout -b bucket-1/seed-hotels-activities
# Create more data files...
```
