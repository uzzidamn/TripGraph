# Task 5: Neo4j Knowledge Graph + Graph Planning Engine — Mini Spec

> **Owner**: You (Mainframe)
> **Priority**: P0 — Start Day 1, this is the intellectual core of the project
> **Estimated effort**: 15-20 days
> **Reference**: Read `MASTER_SPEC.md` (same folder) for full project context

---

## Overview

You own the **entire data infrastructure and planning intelligence** of TripGraph AI. This includes:

1. **Neo4j Knowledge Graph** — Schema design, connection manager, Cypher query library, tool function implementations
2. **Graph Planning Engine** — Trip graph construction, candidate generation, scoring, constraint validation, timeline generation, delay-aware replanning

You define the interfaces that Task 1 (data), Task 2 (agents), and Task 3 (API) integrate against.

---

## What You Deliver

### Knowledge Graph Layer

| # | Deliverable | File |
|---|------------|------|
| 1 | Neo4j connection manager | `backend/knowledge_graph/connection.py` |
| 2 | Schema creation script | `backend/knowledge_graph/schema.py` |
| 3 | Cypher query library | `backend/knowledge_graph/queries.py` |
| 4 | Route tool | `backend/tools/route_tool.py` |
| 5 | Hotel tool | `backend/tools/hotel_tool.py` |
| 6 | Activity tool | `backend/tools/activity_tool.py` |
| 7 | Transport tool | `backend/tools/transport_tool.py` |
| 8 | Restaurant tool | `backend/tools/restaurant_tool.py` |
| 9 | Waypoint tool | `backend/tools/waypoint_tool.py` |

### Planning Engine

| # | Deliverable | File |
|---|------------|------|
| 10 | Trip graph builder | `backend/planner/trip_graph_builder.py` |
| 11 | Candidate generator | `backend/planner/candidate_generator.py` |
| 12 | Multi-objective scorer | `backend/planner/scorer.py` |
| 13 | Constraint validator | `backend/planner/validator.py` |
| 14 | Timeline generator | `backend/planner/timeline_generator.py` |
| 15 | Replanning engine | `backend/planner/replanner.py` |

---

## Part A: Neo4j Knowledge Graph

### Step 1: Install Docker and Start Neo4j

```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop/
# Then run Neo4j:
docker run -d \
  --name tripgraph-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/tripgraph123 \
  neo4j:5-community

# Access Neo4j Browser at http://localhost:7474
# Login: neo4j / tripgraph123
```

### Step 2: Create `connection.py` — Neo4j Driver

```python
"""
Neo4j connection manager. Singleton driver for the application.
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "tripgraph123")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver

def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None

def execute_query(cypher: str, parameters: dict = None) -> list[dict]:
    """Execute a Cypher query and return results as list of dicts."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, parameters or {})
        return [record.data() for record in result]

def execute_write(cypher: str, parameters: dict = None):
    """Execute a write Cypher query."""
    driver = get_driver()
    with driver.session() as session:
        session.run(cypher, parameters or {})
```

### Step 3: Create `schema.py` — Graph Schema

```python
"""
Create Neo4j constraints and indexes for the knowledge graph.
Run once to initialize the database schema.
"""
from backend.knowledge_graph.connection import execute_write

SCHEMA_QUERIES = [
    # Uniqueness constraints
    "CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:Route) REQUIRE r.route_id IS UNIQUE",
    "CREATE CONSTRAINT hotel_id IF NOT EXISTS FOR (h:Hotel) REQUIRE h.hotel_id IS UNIQUE",
    "CREATE CONSTRAINT activity_id IF NOT EXISTS FOR (a:Activity) REQUIRE a.activity_id IS UNIQUE",
    "CREATE CONSTRAINT restaurant_id IF NOT EXISTS FOR (r:Restaurant) REQUIRE r.restaurant_id IS UNIQUE",
    "CREATE CONSTRAINT transport_id IF NOT EXISTS FOR (t:TransportOption) REQUIRE t.transport_id IS UNIQUE",
    "CREATE CONSTRAINT waypoint_id IF NOT EXISTS FOR (w:Waypoint) REQUIRE w.waypoint_id IS UNIQUE",
    "CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",

    # Performance indexes
    "CREATE INDEX city_type IF NOT EXISTS FOR (c:City) ON (c.type)",
    "CREATE INDEX hotel_tier IF NOT EXISTS FOR (h:Hotel) ON (h.tier)",
    "CREATE INDEX hotel_dest IF NOT EXISTS FOR (h:Hotel) ON (h.destination)",
    "CREATE INDEX activity_cat IF NOT EXISTS FOR (a:Activity) ON (a.category)",
    "CREATE INDEX transport_tier IF NOT EXISTS FOR (t:TransportOption) ON (t.tier)",
]

def create_schema():
    for query in SCHEMA_QUERIES:
        try:
            execute_write(query)
        except Exception as e:
            print(f"Schema query warning: {e}")
    print("✅ Neo4j schema created/verified")

if __name__ == "__main__":
    create_schema()
```

### Step 4: Create `queries.py` — Cypher Query Library

```python
"""
Reusable Cypher queries for the knowledge graph.
Each function returns a Cypher string and parameters dict.
"""

class TravelQueries:
    """Cypher queries organized by entity type."""

    @staticmethod
    def find_routes(origin: str, destination_type: str | None = None) -> tuple[str, dict]:
        if destination_type:
            return (
                """
                MATCH (origin:City {name: $origin})-[:ORIGIN_OF]->(r:Route)-[:ARRIVES_AT]->(dest:City)
                WHERE dest.type = $dest_type
                RETURN r {.*, destination: dest.name, destination_type: dest.type,
                          dest_lat: dest.lat, dest_lng: dest.lng} AS route
                """,
                {"origin": origin, "dest_type": destination_type},
            )
        return (
            """
            MATCH (origin:City {name: $origin})-[:ORIGIN_OF]->(r:Route)-[:ARRIVES_AT]->(dest:City)
            RETURN r {.*, destination: dest.name, destination_type: dest.type,
                      dest_lat: dest.lat, dest_lng: dest.lng} AS route
            """,
            {"origin": origin},
        )

    @staticmethod
    def find_hotels(destination: str, tier: str | None = None) -> tuple[str, dict]:
        if tier:
            return (
                """
                MATCH (c:City {name: $destination})-[:HAS_HOTEL]->(h:Hotel {tier: $tier})
                RETURN h {.*} AS hotel
                ORDER BY h.price_per_night ASC
                """,
                {"destination": destination, "tier": tier},
            )
        return (
            """
            MATCH (c:City {name: $destination})-[:HAS_HOTEL]->(h:Hotel)
            RETURN h {.*} AS hotel
            ORDER BY h.tier, h.price_per_night ASC
            """,
            {"destination": destination},
        )

    @staticmethod
    def find_activities(destination: str, tags: list[str] | None = None) -> tuple[str, dict]:
        if tags:
            return (
                """
                MATCH (c:City {name: $destination})-[:HAS_ACTIVITY]->(a:Activity)
                WHERE any(tag IN $tags WHERE tag IN a.tags)
                RETURN a {.*} AS activity
                """,
                {"destination": destination, "tags": tags},
            )
        return (
            """
            MATCH (c:City {name: $destination})-[:HAS_ACTIVITY]->(a:Activity)
            RETURN a {.*} AS activity
            """,
            {"destination": destination},
        )

    @staticmethod
    def find_transport(route_id: str, modes: list[str] | None = None) -> tuple[str, dict]:
        if modes:
            return (
                """
                MATCH (r:Route {route_id: $route_id})-[:HAS_TRANSPORT]->(t:TransportOption)
                WHERE t.mode IN $modes
                RETURN t {.*} AS transport
                ORDER BY t.cost_total ASC
                """,
                {"route_id": route_id, "modes": modes},
            )
        return (
            """
            MATCH (r:Route {route_id: $route_id})-[:HAS_TRANSPORT]->(t:TransportOption)
            RETURN t {.*} AS transport
            ORDER BY t.cost_total ASC
            """,
            {"route_id": route_id},
        )

    @staticmethod
    def find_restaurants(destination: str, route_id: str | None = None) -> tuple[str, dict]:
        if route_id:
            # Get both destination restaurants and highway stops
            return (
                """
                MATCH (c:City {name: $destination})-[:HAS_RESTAURANT]->(r:Restaurant)
                RETURN r {.*, location_type: 'destination'} AS restaurant
                UNION
                MATCH (route:Route {route_id: $route_id})<-[:ON_ROUTE]-(r:Restaurant)
                RETURN r {.*, location_type: 'highway'} AS restaurant
                """,
                {"destination": destination, "route_id": route_id},
            )
        return (
            """
            MATCH (c:City {name: $destination})-[:HAS_RESTAURANT]->(r:Restaurant)
            RETURN r {.*} AS restaurant
            """,
            {"destination": destination},
        )

    @staticmethod
    def find_waypoints(route_id: str) -> tuple[str, dict]:
        return (
            """
            MATCH (r:Route {route_id: $route_id})-[:PASSES_THROUGH]->(w:Waypoint)
            RETURN w {.*} AS waypoint
            ORDER BY w.order ASC
            """,
            {"route_id": route_id},
        )

    @staticmethod
    def full_route_data(origin: str, destination_type: str | None = None) -> tuple[str, dict]:
        """Get complete route data with all connected entities."""
        params = {"origin": origin}
        where_clause = ""
        if destination_type:
            where_clause = "WHERE dest.type = $dest_type"
            params["dest_type"] = destination_type

        return (
            f"""
            MATCH (origin:City {{name: $origin}})-[:ORIGIN_OF]->(r:Route)-[:ARRIVES_AT]->(dest:City)
            {where_clause}
            OPTIONAL MATCH (dest)-[:HAS_HOTEL]->(h:Hotel)
            OPTIONAL MATCH (dest)-[:HAS_ACTIVITY]->(a:Activity)
            OPTIONAL MATCH (r)-[:HAS_TRANSPORT]->(t:TransportOption)
            OPTIONAL MATCH (dest)-[:HAS_RESTAURANT]->(rest:Restaurant)
            OPTIONAL MATCH (r)-[:PASSES_THROUGH]->(w:Waypoint)
            RETURN r {{.*}} AS route,
                   dest {{.*}} AS destination,
                   collect(DISTINCT h {{.*}}) AS hotels,
                   collect(DISTINCT a {{.*}}) AS activities,
                   collect(DISTINCT t {{.*}}) AS transport,
                   collect(DISTINCT rest {{.*}}) AS restaurants,
                   collect(DISTINCT w {{.*}}) AS waypoints
            """,
            params,
        )
```

### Step 5: Create Tool Functions

Each tool function wraps a Cypher query and returns data as a list of dicts. These are the interfaces that Task 2 (agents) call.

```python
# backend/tools/route_tool.py
"""Tool: get_routes — returns matching routes from the knowledge graph."""
from backend.knowledge_graph.connection import execute_query
from backend.knowledge_graph.queries import TravelQueries


def get_routes(origin: str, destination_type: str | None = None) -> list[dict]:
    """
    Returns route options matching origin and optional destination type.
    Called by: Data Retriever Agent (Task 2)
    """
    cypher, params = TravelQueries.find_routes(origin, destination_type)
    results = execute_query(cypher, params)
    return [r["route"] for r in results]
```

```python
# backend/tools/hotel_tool.py
from backend.knowledge_graph.connection import execute_query
from backend.knowledge_graph.queries import TravelQueries

def get_hotels(destination: str, tier: str | None = None) -> list[dict]:
    """Returns hotels at a destination, optionally filtered by tier."""
    cypher, params = TravelQueries.find_hotels(destination, tier)
    results = execute_query(cypher, params)
    return [r["hotel"] for r in results]
```

Follow the same pattern for `activity_tool.py`, `transport_tool.py`, `restaurant_tool.py`, `waypoint_tool.py`.

---

## Part B: Graph Planning Engine

### Step 6: `trip_graph_builder.py` — Build Trip DAG

```python
"""
Builds a trip graph (DAG) from the retrieved travel data.
Each node is a trip event (departure, stop, hotel, activity, return).
Each edge carries cost, duration, and constraints.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TripNode:
    node_id: str
    node_type: str  # origin, waypoint, hotel, activity, restaurant, return
    name: str
    day: int
    time_window: tuple[str, str] | None = None  # (earliest_start, latest_start)
    duration_minutes: int = 0
    cost_per_person: float = 0
    lat: float = 0.0
    lng: float = 0.0
    is_mandatory: bool = True
    is_flexible: bool = True
    data: dict = field(default_factory=dict)  # raw entity data


@dataclass
class TripEdge:
    from_node: str
    to_node: str
    mode: str  # drive, walk, wait
    duration_minutes: int = 0
    cost: float = 0
    distance_km: float = 0


@dataclass
class TripGraph:
    nodes: dict[str, TripNode] = field(default_factory=dict)
    edges: list[TripEdge] = field(default_factory=list)
    adjacency: dict[str, list[str]] = field(default_factory=dict)

    def add_node(self, node: TripNode):
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []

    def add_edge(self, edge: TripEdge):
        self.edges.append(edge)
        if edge.from_node not in self.adjacency:
            self.adjacency[edge.from_node] = []
        self.adjacency[edge.from_node].append(edge.to_node)

    def get_ordered_nodes(self) -> list[TripNode]:
        """Topological sort of the DAG."""
        # Simple: return nodes sorted by day and time
        return sorted(self.nodes.values(), key=lambda n: (n.day, n.time_window[0] if n.time_window else "00:00"))


def build_trip_graph(route: dict, transport: dict, hotel: dict,
                     activities: list[dict], restaurants: list[dict],
                     waypoints: list[dict], constraints: dict) -> TripGraph:
    """
    Construct a trip DAG from selected entities.
    This is the core graph construction logic.
    """
    graph = TripGraph()
    group_size = constraints.get("group_size", 4)

    # Day 1: Origin → Waypoints → Destination → Hotel → Activities → Dinner
    graph.add_node(TripNode(
        node_id="origin",
        node_type="origin",
        name=route.get("origin", "Gurugram"),
        day=1,
        time_window=("05:00", "07:00"),
        lat=constraints.get("origin_lat", 28.4595),
        lng=constraints.get("origin_lng", 77.0266),
    ))

    # Add waypoints (highway stops)
    for i, wp in enumerate(waypoints):
        graph.add_node(TripNode(
            node_id=f"waypoint_{i}",
            node_type="waypoint",
            name=wp.get("name", f"Stop {i+1}"),
            day=1,
            duration_minutes=wp.get("typical_stop_minutes", 30),
            cost_per_person=0,
            lat=wp.get("lat", 0),
            lng=wp.get("lng", 0),
            is_mandatory=False,
            data=wp,
        ))

    # Hotel check-in
    graph.add_node(TripNode(
        node_id="hotel_checkin",
        node_type="hotel",
        name=hotel.get("name", "Hotel"),
        day=1,
        time_window=(hotel.get("checkin_time", "14:00"), "16:00"),
        duration_minutes=90,  # rest time
        cost_per_person=hotel.get("price_per_night", 0) / group_size,
        lat=hotel.get("lat", 0),
        lng=hotel.get("lng", 0),
        data=hotel,
    ))

    # Activities
    for i, act in enumerate(activities):
        graph.add_node(TripNode(
            node_id=f"activity_{i}",
            node_type="activity",
            name=act.get("name", f"Activity {i+1}"),
            day=1 if i == 0 else 2,  # Spread across days
            duration_minutes=act.get("duration_minutes", 120),
            cost_per_person=act.get("cost_per_person", 0),
            lat=act.get("lat", 0),
            lng=act.get("lng", 0),
            is_mandatory="must_include" in str(constraints.get("must_include", [])),
            data=act,
        ))

    # Meals
    for i, rest in enumerate(restaurants):
        meal_type = rest.get("meal_types", ["lunch"])[0] if rest.get("meal_types") else "meal"
        graph.add_node(TripNode(
            node_id=f"meal_{i}",
            node_type="restaurant",
            name=rest.get("name", f"Meal {i+1}"),
            day=1 if i < 2 else 2,
            duration_minutes=rest.get("avg_duration_minutes", 60),
            cost_per_person=rest.get("avg_cost_per_person", 0),
            lat=rest.get("lat", 0),
            lng=rest.get("lng", 0),
            is_mandatory=False,
            is_flexible=True,
            data=rest,
        ))

    # Return
    graph.add_node(TripNode(
        node_id="return",
        node_type="return",
        name=f"Return to {route.get('origin', 'Gurugram')}",
        day=2,
        duration_minutes=route.get("base_drive_minutes", 300),
        lat=constraints.get("origin_lat", 28.4595),
        lng=constraints.get("origin_lng", 77.0266),
    ))

    # Build edges (sequential for now — you can add more complex routing later)
    ordered = graph.get_ordered_nodes()
    for i in range(len(ordered) - 1):
        graph.add_edge(TripEdge(
            from_node=ordered[i].node_id,
            to_node=ordered[i+1].node_id,
            mode=transport.get("mode", "cab"),
            duration_minutes=30,  # estimated transition time
        ))

    return graph
```

### Step 7: `candidate_generator.py`

```python
"""
Generate candidate itineraries by combining routes × transport × hotels × activities.
"""
from itertools import product
from backend.planner.trip_graph_builder import build_trip_graph


def generate_candidates(constraints: dict, data: dict) -> list[dict]:
    """
    Generate candidate itinerary combinations.
    Each candidate = route + transport + hotel + activity set + restaurant set.
    """
    candidates = []
    routes = data.get("routes", [])
    all_hotels = data.get("hotels", [])
    all_transport = data.get("transport", [])
    all_activities = data.get("activities", [])
    all_restaurants = data.get("food", [])
    all_waypoints = data.get("waypoints", [])

    for route in routes:
        route_id = route.get("route_id")
        destination = route.get("destination")

        # Filter entities for this route/destination
        hotels = [h for h in all_hotels if h.get("destination") == destination]
        transport_opts = [t for t in all_transport if t.get("route_id") == route_id]
        activities = [a for a in all_activities if a.get("destination") == destination]
        restaurants = [r for r in all_restaurants if r.get("destination") == destination or r.get("route_id") == route_id]
        waypoints = [w for w in all_waypoints if w.get("route_id") == route_id]

        # Generate combinations: each hotel × each transport
        # (activities and restaurants are included as sets)
        for hotel in (hotels or [{}]):
            for transport in (transport_opts or [{}]):
                candidate = {
                    "route": route,
                    "transport": transport,
                    "hotel": hotel,
                    "activities": activities,
                    "restaurants": restaurants,
                    "waypoints": waypoints,
                    "destination": destination,
                    # Build the trip graph for this candidate
                    "trip_graph": None,  # populated below
                }

                # Build trip graph
                trip_graph = build_trip_graph(
                    route=route, transport=transport, hotel=hotel,
                    activities=activities, restaurants=restaurants,
                    waypoints=waypoints, constraints=constraints,
                )
                candidate["trip_graph"] = trip_graph

                # Calculate totals
                group_size = constraints.get("group_size", 4)
                transport_cost_pp = transport.get("cost_total", 0) / group_size
                hotel_cost_pp = hotel.get("price_per_night", 0) / group_size
                activity_cost = sum(a.get("cost_per_person", 0) for a in activities)
                food_cost = sum(r.get("avg_cost_per_person", 0) for r in restaurants)
                misc = 2000  # buffer

                candidate["cost_breakdown"] = {
                    "transport": round(transport_cost_pp),
                    "hotel": round(hotel_cost_pp),
                    "activities": round(activity_cost),
                    "food": round(food_cost),
                    "miscellaneous": misc,
                    "total": round(transport_cost_pp + hotel_cost_pp + activity_cost + food_cost + misc),
                    "budget_limit": constraints.get("budget_per_person", 0),
                }

                candidate["total_cost_per_person"] = candidate["cost_breakdown"]["total"]
                candidates.append(candidate)

    return candidates
```

### Step 8: `scorer.py` — Multi-Objective Scoring

```python
"""
Score itinerary candidates using a multi-objective function.
Higher score = better itinerary.
"""

def score_itinerary(itinerary: dict, constraints: dict) -> dict:
    """
    Score an itinerary candidate.
    Returns a dict with individual scores and final_score.
    """
    scores = {}

    # 1. Preference match (0-25 points)
    must_include = set(constraints.get("must_include", []))
    activity_tags = set()
    for act in itinerary.get("activities", []):
        activity_tags.update(act.get("tags", []))
        activity_tags.add(act.get("name", "").lower())
    matched = must_include & activity_tags
    scores["preference_match"] = (len(matched) / max(len(must_include), 1)) * 25

    # 2. Budget efficiency (0-20 points)
    budget = constraints.get("budget_per_person", 15000)
    cost = itinerary.get("total_cost_per_person", 0)
    if budget > 0 and cost <= budget:
        scores["budget_efficiency"] = ((budget - cost) / budget) * 20
    else:
        scores["budget_efficiency"] = 0

    # 3. Comfort score (0-15 points)
    hotel_comfort = itinerary.get("hotel", {}).get("comfort_score", 5)
    transport_comfort = itinerary.get("transport", {}).get("comfort_score", 5)
    scores["comfort"] = ((hotel_comfort + transport_comfort) / 2) * 1.5

    # 4. Scenic score (0-10 points)
    scores["scenic"] = itinerary.get("route", {}).get("scenic_score", 5)

    # 5. Fatigue penalty (0-15 points, lower fatigue = higher score)
    fatigue = itinerary.get("transport", {}).get("fatigue_score", 5)
    scores["fatigue"] = max(0, (10 - fatigue)) * 1.5

    # 6. Risk penalty (0-10 points, lower risk = higher score)
    risk_map = {"low": 10, "medium": 6, "high": 3}
    scores["risk"] = risk_map.get(itinerary.get("route", {}).get("risk_level", "medium"), 5)

    # 7. Night driving penalty
    if constraints.get("avoid_night_driving") and itinerary.get("transport", {}).get("night_driving_allowed"):
        scores["night_driving_penalty"] = -20
    else:
        scores["night_driving_penalty"] = 0

    scores["final_score"] = sum(scores.values())
    return scores
```

### Step 9: `validator.py` — Constraint Validation

```python
"""
Validate itinerary against hard and soft constraints.
"""

def validate_itinerary(itinerary: dict, constraints: dict) -> dict:
    """
    Check hard and soft constraints. Returns validation report.
    """
    hard_violations = []
    soft_warnings = []

    cost = itinerary.get("total_cost_per_person", 0)
    budget = constraints.get("budget_per_person", float("inf"))

    # Hard: Budget
    if cost > budget:
        hard_violations.append(f"Cost ₹{cost:,.0f} exceeds budget ₹{budget:,.0f}")

    # Hard: Night driving
    if constraints.get("avoid_night_driving"):
        transport = itinerary.get("transport", {})
        if transport.get("night_driving_allowed") and transport.get("mode") == "self_drive":
            hard_violations.append("Self-drive with night driving conflicts with 'no night driving' constraint")

    # Hard: Must-include activities
    must_include = set(constraints.get("must_include", []))
    available_tags = set()
    for act in itinerary.get("activities", []):
        available_tags.update(act.get("tags", []))
        available_tags.add(act.get("name", "").lower())
    missing = must_include - available_tags
    if missing:
        hard_violations.append(f"Missing required activities: {', '.join(missing)}")

    # Hard: Destination type mismatch
    dest_type = constraints.get("destination_type")
    route_dest_type = itinerary.get("route", {}).get("destination_type")
    if dest_type and route_dest_type and dest_type != route_dest_type:
        hard_violations.append(f"Destination type '{route_dest_type}' does not match preference '{dest_type}'")

    # Soft: Rest time
    # Soft: Comfort level
    if itinerary.get("hotel", {}).get("comfort_score", 10) < 5:
        soft_warnings.append("Hotel comfort is below average")

    return {
        "is_valid": len(hard_violations) == 0,
        "hard_constraint_violations": hard_violations,
        "soft_constraint_warnings": soft_warnings,
        "budget_used": cost,
        "budget_limit": budget,
        "must_include_satisfied": list(must_include - missing) if must_include else [],
    }
```

### Step 10: `timeline_generator.py`

```python
"""
Generate a sequential timeline of events from a trip graph.
Places events in chronological order with calculated start/end times.
"""
from datetime import datetime, timedelta


def generate_timeline(itinerary: dict) -> list[dict]:
    """
    Create a chronological list of timeline events from the itinerary.
    Each event has: day, start_time, end_time, title, type, cost (optional).
    """
    events = []
    route = itinerary.get("route", {})
    transport = itinerary.get("transport", {})
    hotel = itinerary.get("hotel", {})
    activities = itinerary.get("activities", [])
    restaurants = itinerary.get("restaurants", [])
    waypoints = itinerary.get("waypoints", [])

    drive_minutes = transport.get("base_duration_minutes", route.get("base_drive_minutes", 300))
    group_size = 4

    # Day 1
    current = datetime(2026, 1, 1, 6, 0)  # 06:00 departure

    # Departure
    depart_end = current + timedelta(minutes=drive_minutes // 2)
    events.append(_event(1, current, depart_end, f"Drive from {route.get('origin', 'Origin')}", "travel"))

    # Breakfast waypoint
    current = depart_end
    breakfast_end = current + timedelta(minutes=45)
    if waypoints:
        wp = waypoints[0]
        events.append(_event(1, current, breakfast_end, f"Breakfast at {wp.get('name', 'Highway Stop')}", "meal"))
    current = breakfast_end

    # Continue drive
    arrive_time = current + timedelta(minutes=drive_minutes // 2)
    events.append(_event(1, current, arrive_time, f"Continue drive to {route.get('destination', 'Destination')}", "travel"))
    current = arrive_time

    # Lunch
    if restaurants:
        dest_restaurants = [r for r in restaurants if r.get("destination") == route.get("destination")]
        if dest_restaurants:
            lunch_dur = dest_restaurants[0].get("avg_duration_minutes", 60)
            lunch_end = current + timedelta(minutes=lunch_dur)
            events.append(_event(1, current, lunch_end, f"Lunch at {dest_restaurants[0].get('name', 'Restaurant')}", "meal",
                                 cost=dest_restaurants[0].get("avg_cost_per_person", 0)))
            current = lunch_end

    # Hotel check-in
    checkin = current + timedelta(minutes=30)
    rest_end = checkin + timedelta(minutes=90)
    events.append(_event(1, checkin, rest_end, f"Check-in at {hotel.get('name', 'Hotel')}", "hotel",
                         cost=hotel.get("price_per_night", 0) // group_size))
    current = rest_end

    # Evening activities (Day 1)
    evening_acts = [a for a in activities if "evening" in a.get("tags", []) or "cultural" == a.get("category")]
    for act in evening_acts[:1]:
        act_end = current + timedelta(minutes=act.get("duration_minutes", 90))
        events.append(_event(1, current, act_end, act.get("name", "Activity"), "activity",
                             cost=act.get("cost_per_person", 0)))
        current = act_end

    # Dinner
    events.append(_event(1, current, current + timedelta(minutes=60), "Dinner", "meal"))

    # Day 2
    current = datetime(2026, 1, 2, 7, 30)
    events.append(_event(2, current, current + timedelta(minutes=45), "Breakfast", "meal"))
    current += timedelta(minutes=45)

    # Morning activities (Day 2)
    morning_acts = [a for a in activities if a not in evening_acts]
    for act in morning_acts[:1]:
        act_end = current + timedelta(minutes=act.get("duration_minutes", 180))
        events.append(_event(2, current, act_end, act.get("name", "Activity"), "activity",
                             cost=act.get("cost_per_person", 0)))
        current = act_end

    # Rest + lunch
    events.append(_event(2, current, current + timedelta(minutes=60), "Freshen up", "rest"))
    current += timedelta(minutes=60)
    events.append(_event(2, current, current + timedelta(minutes=60), "Lunch", "meal"))
    current += timedelta(minutes=60)

    # Return journey
    return_end = current + timedelta(minutes=drive_minutes)
    events.append(_event(2, current, return_end, f"Return to {route.get('origin', 'Origin')}", "travel"))

    return events


def _event(day: int, start: datetime, end: datetime, title: str, event_type: str, cost: int = 0) -> dict:
    return {
        "day": day,
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "title": title,
        "type": event_type,
        **({"cost": cost} if cost else {}),
    }
```

### Step 11: `replanner.py` — Delay-Aware Replanning

```python
"""
Delay-aware replanning engine.
Takes an existing itinerary + delay event → produces adjusted itinerary.
"""
from datetime import datetime, timedelta


def replan_itinerary(itinerary: dict, delay_event: dict, constraints: dict) -> dict:
    """
    Adjust itinerary after a delay event.
    Returns updated itinerary and list of changes made.
    """
    from backend.planner.timeline_generator import generate_timeline

    delay_minutes = delay_event.get("delay_minutes", 0)
    delay_type = delay_event.get("delay_type", "departure_delay")
    changes = []

    # Re-generate timeline with shifted departure
    timeline = generate_timeline(itinerary)

    # Shift all events by delay amount
    shifted_timeline = []
    total_slack_recovered = 0

    for event in timeline:
        start = datetime.strptime(event["start_time"], "%H:%M")
        end = datetime.strptime(event["end_time"], "%H:%M")
        duration = (end - start).total_seconds() / 60

        if event["type"] in ["rest", "meal"] and event.get("title") not in ["Breakfast"]:
            # Flexible: compress by up to 50%
            compress = min(delay_minutes - total_slack_recovered, duration * 0.5)
            if compress > 0:
                duration -= compress
                total_slack_recovered += compress
                changes.append(f"{event['title']} shortened by {int(compress)} minutes")

        # Apply remaining delay as shift
        remaining_delay = max(0, delay_minutes - total_slack_recovered)
        new_start = start + timedelta(minutes=remaining_delay)
        new_end = new_start + timedelta(minutes=duration)

        shifted_timeline.append({
            **event,
            "start_time": new_start.strftime("%H:%M"),
            "end_time": new_end.strftime("%H:%M"),
        })

    # Check if optional events need to be dropped
    if total_slack_recovered < delay_minutes:
        # Drop optional events
        final_timeline = []
        for event in shifted_timeline:
            # Keep mandatory, drop optional if still over time
            if event["type"] in ["activity"] and "optional" in event.get("title", "").lower():
                changes.append(f"{event['title']} removed due to time constraints")
                continue
            final_timeline.append(event)
        shifted_timeline = final_timeline

    if not changes:
        changes.append(f"All events shifted by {delay_minutes} minutes")

    return {
        "updated_itinerary": {
            **itinerary,
            "timeline": shifted_timeline,
        },
        "changes": changes,
        "delay_absorbed": total_slack_recovered,
        "delay_remaining": max(0, delay_minutes - total_slack_recovered),
    }
```

---

## Testing Checklist

- [ ] Neo4j Docker starts and is accessible at `http://localhost:7474`
- [ ] Schema creation runs without errors
- [ ] After seeding (Task 1), queries return expected data
- [ ] All 6 tool functions return correct results
- [ ] `generate_candidates()` produces ≥1 candidate per route
- [ ] `score_itinerary()` returns scores for all dimensions
- [ ] `validate_itinerary()` catches budget violations and missing activities
- [ ] `generate_timeline()` produces chronologically valid events
- [ ] `replan_itinerary()` handles 90-min departure delay correctly
- [ ] Jaipur route is rejected when destination_type = "mountains"

---

## Git Workflow

```bash
git checkout -b bucket-5/neo4j-setup
# connection.py, schema.py
git commit -m "Task 5: Neo4j connection and schema"

git checkout -b bucket-5/queries-tools
# queries.py + all tool files
git commit -m "Task 5: Cypher queries and tool functions"

git checkout -b bucket-5/planner-core
# trip_graph_builder.py, candidate_generator.py, scorer.py, validator.py
git commit -m "Task 5: Core planning engine"

git checkout -b bucket-5/timeline-replanner
# timeline_generator.py, replanner.py
git commit -m "Task 5: Timeline generation and delay replanning"
```
