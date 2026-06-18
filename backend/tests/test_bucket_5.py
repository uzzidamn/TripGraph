"""
Bucket 5 Validation Script.
Tests the Neo4j knowledge graph layer and graph planning engine.

Run: PYTHONPATH=. python backend/tests/test_bucket_5.py

Does NOT require Neo4j to be running — all planning tests use in-memory mock data.
Neo4j tool-import tests only check that modules load (no connection made).
"""
import sys
from pathlib import Path

PASS = 0
FAIL = 0


def check(condition: bool, msg: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {msg}")
    else:
        FAIL += 1
        print(f"  ❌ {msg}")


# ---------------------------------------------------------------------------
# Shared mock data (mirrors seed data IDs from Bucket 1 exactly)
# ---------------------------------------------------------------------------

_ROUTE = {
    "route_id": "gurugram_rishikesh_2d1n",
    "origin": "Gurugram",
    "destination": "Rishikesh",
    "destination_type": "mountains",
    "distance_km": 260,
    "base_drive_minutes": 390,
    "risk_level": "medium",
    "scenic_score": 7,
    "dest_lat": 30.0869,
    "dest_lng": 78.2676,
}

_TRANSPORT = {
    "transport_id": "cab_rishikesh_comfort",
    "route_id": "gurugram_rishikesh_2d1n",
    "mode": "cab_with_driver",
    "tier": "comfort",
    "cost_total": 9500,
    "capacity": 4,
    "base_duration_minutes": 390,
    "night_driving_allowed": False,
    "comfort_score": 8,
    "fatigue_score": 3,
    "tags": ["ac", "sedan"],
}

_HOTEL = {
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
    "amenities": ["wifi", "parking", "restaurant"],
    "tags": ["riverside"],
}

_ACTIVITIES = [
    {
        "activity_id": "rafting_rishikesh_01",
        "destination": "Rishikesh",
        "name": "White Water Rafting (16 km)",
        "category": "adventure",
        "duration_minutes": 180,
        "cost_per_person": 1800,
        "available_slots": ["09:00", "12:00"],
        "risk_level": "medium",
        "tags": ["adventure", "rafting", "water", "outdoor"],
        "lat": 30.1159,
        "lng": 78.3127,
    },
    {
        "activity_id": "ganga_aarti_rishikesh_01",
        "destination": "Rishikesh",
        "name": "Parmarth Niketan Ganga Aarti",
        "category": "spiritual",
        "duration_minutes": 60,
        "cost_per_person": 0,
        "available_slots": ["18:30"],
        "risk_level": "low",
        "tags": ["spiritual", "aarti", "ganga", "evening", "culture"],
        "lat": 30.1354,
        "lng": 78.3207,
    },
    {
        "activity_id": "cafe_hopping_rishikesh_01",
        "destination": "Rishikesh",
        "name": "Lakshman Jhula Cafe Hopping",
        "category": "food",
        "duration_minutes": 90,
        "cost_per_person": 500,
        "available_slots": ["10:00", "15:00", "16:00"],
        "risk_level": "low",
        "tags": ["cafes", "food", "river_view", "relaxed"],
        "lat": 30.1256,
        "lng": 78.3152,
    },
]

_RESTAURANTS = [
    {
        "restaurant_id": "little_buddha_rishikesh_01",
        "destination": "Rishikesh",
        "route_id": None,
        "name": "Little Buddha Cafe",
        "meal_types": ["lunch", "dinner"],
        "avg_cost_per_person": 600,
        "avg_duration_minutes": 75,
        "tags": ["cafe", "river_view"],
        "lat": 30.1256,
        "lng": 78.3152,
        "location_type": "destination",
    },
    {
        "restaurant_id": "highway_amrik_sukhdev_01",
        "destination": None,
        "route_id": "gurugram_rishikesh_2d1n",
        "name": "Amrik Sukhdev Dhaba",
        "meal_types": ["breakfast", "lunch"],
        "avg_cost_per_person": 250,
        "avg_duration_minutes": 45,
        "km_from_origin": 35,
        "tags": ["dhaba", "highway"],
        "lat": 29.0281,
        "lng": 77.0474,
        "location_type": "highway",
    },
]

_WAYPOINTS = [
    {
        "waypoint_id": "murthal_stop",
        "route_id": "gurugram_rishikesh_2d1n",
        "name": "Murthal Dhaba Belt",
        "type": "breakfast_stop",
        "km_from_origin": 35,
        "order": 1,
        "lat": 29.0281,
        "lng": 77.0474,
        "typical_stop_minutes": 30,
    },
]

_CONSTRAINTS = {
    "origin": "Gurugram",
    "destination_type": "mountains",
    "budget_per_person": 15000,
    "group_size": 4,
    "hotel_tier": "comfort",
    "avoid_night_driving": True,
    "must_include": ["rafting", "cafes"],
    "return_deadline": "Monday morning",
    "risk_tolerance": "medium",
}

_CANDIDATE = {
    "route": _ROUTE,
    "transport": _TRANSPORT,
    "hotel": _HOTEL,
    "activities": _ACTIVITIES,
    "restaurants": _RESTAURANTS,
    "waypoints": _WAYPOINTS,
    "destination": "Rishikesh",
    "total_cost_per_person": 9450,  # 2375+1050+(1800+0+500)+1725+2000 = 9450
    "cost_breakdown": {
        "transport": 2375,
        "hotel": 1050,
        "activities": 2300,  # 1800 + 0 + 500
        "food": 1725,
        "miscellaneous": 2000,
        "total": 9450,
        "budget_limit": 15000,
    },
}


# ---------------------------------------------------------------------------
# Section 1: Knowledge Graph module imports
# ---------------------------------------------------------------------------

def test_kg_imports():
    print("\n=== Section 1: Knowledge Graph module imports ===")
    try:
        import neo4j  # noqa: F401
        neo4j_available = True
    except ImportError:
        neo4j_available = False
        print("  ⚠️  neo4j package not installed — skipping connection/schema imports (needs backend venv)")

    if neo4j_available:
        try:
            from backend.knowledge_graph import connection
            check(hasattr(connection, "get_driver"), "connection.get_driver exists")
            check(hasattr(connection, "execute_query"), "connection.execute_query exists")
            check(hasattr(connection, "execute_write"), "connection.execute_write exists")
            check(hasattr(connection, "close_driver"), "connection.close_driver exists")
        except Exception as e:
            check(False, f"connection import failed: {e}")
            return

        try:
            from backend.knowledge_graph import schema
            check(hasattr(schema, "create_schema"), "schema.create_schema exists")
            check(isinstance(schema.SCHEMA_QUERIES, list), "schema.SCHEMA_QUERIES is a list")
            check(len(schema.SCHEMA_QUERIES) >= 8, f"at least 8 schema queries ({len(schema.SCHEMA_QUERIES)} found)")
        except Exception as e:
            check(False, f"schema import failed: {e}")
    else:
        # Verify files exist and have correct content without importing
        kg_dir = Path(__file__).parent.parent / "knowledge_graph"
        check((kg_dir / "connection.py").exists(), "connection.py exists")
        check((kg_dir / "schema.py").exists(), "schema.py exists")
        check((kg_dir / "queries.py").exists(), "queries.py exists")
        check((kg_dir / "seed.py").exists(), "seed.py exists")

        content = (kg_dir / "connection.py").read_text()
        check("def get_driver" in content, "connection.py defines get_driver")
        check("def execute_query" in content, "connection.py defines execute_query")
        check("def execute_write" in content, "connection.py defines execute_write")

        schema_content = (kg_dir / "schema.py").read_text()
        check("SCHEMA_QUERIES" in schema_content, "schema.py defines SCHEMA_QUERIES")
        check("create_schema" in schema_content, "schema.py defines create_schema")

    try:
        from backend.knowledge_graph.queries import TravelQueries
        check(callable(TravelQueries.find_routes), "TravelQueries.find_routes callable")
        check(callable(TravelQueries.find_hotels), "TravelQueries.find_hotels callable")
        check(callable(TravelQueries.find_activities), "TravelQueries.find_activities callable")
        check(callable(TravelQueries.find_transport), "TravelQueries.find_transport callable")
        check(callable(TravelQueries.find_restaurants), "TravelQueries.find_restaurants callable")
        check(callable(TravelQueries.find_waypoints), "TravelQueries.find_waypoints callable")
        check(callable(TravelQueries.full_route_data), "TravelQueries.full_route_data callable")
    except Exception as e:
        check(False, f"TravelQueries import failed: {e}")


# ---------------------------------------------------------------------------
# Section 2: Cypher query outputs (no DB — just shape/type checks)
# ---------------------------------------------------------------------------

def test_query_outputs():
    print("\n=== Section 2: Query method return types ===")
    from backend.knowledge_graph.queries import TravelQueries

    result = TravelQueries.find_routes("Gurugram")
    check(isinstance(result, tuple) and len(result) == 2, "find_routes returns (cypher, params) tuple")
    check(isinstance(result[0], str) and "MATCH" in result[0], "find_routes cypher is a MATCH string")
    check(isinstance(result[1], dict), "find_routes params is a dict")
    check("origin" in result[1], "find_routes params contains 'origin'")
    check("origin.name" in result[0], "find_routes includes origin.name in projection")

    result = TravelQueries.find_routes("Gurugram", "mountains")
    check("dest_type" in result[1], "find_routes with dest_type has dest_type param")

    result = TravelQueries.find_hotels("Rishikesh", "comfort")
    check("destination" in result[1] and "tier" in result[1], "find_hotels(dest, tier) params correct")

    result = TravelQueries.find_activities("Rishikesh", ["rafting", "adventure"])
    check("tags" in result[1], "find_activities with tags includes tags param")

    result = TravelQueries.find_transport("gurugram_rishikesh_2d1n", ["cab_with_driver"])
    check("modes" in result[1], "find_transport with modes includes modes param")

    result = TravelQueries.find_restaurants("Rishikesh", "gurugram_rishikesh_2d1n")
    check("UNION" in result[0], "find_restaurants(dest, route_id) uses UNION for highway + destination")

    result = TravelQueries.find_waypoints("gurugram_rishikesh_2d1n")
    check("ORDER BY" in result[0], "find_waypoints returns ordered results")


# ---------------------------------------------------------------------------
# Section 3: Tool function imports (no DB connection at import time)
# ---------------------------------------------------------------------------

def test_tool_imports():
    print("\n=== Section 3: Tool function imports ===")
    try:
        import neo4j  # noqa: F401
        neo4j_available = True
    except ImportError:
        neo4j_available = False
        print("  ⚠️  neo4j package not installed — verifying tool files via source inspection")

    tools_dir = Path(__file__).parent.parent / "tools"
    tool_files = [
        ("route_tool.py",     "get_routes"),
        ("hotel_tool.py",     "get_hotels"),
        ("activity_tool.py",  "get_activities"),
        ("transport_tool.py", "get_transport_options"),
        ("restaurant_tool.py","get_restaurants"),
        ("waypoint_tool.py",  "get_waypoints"),
    ]

    if neo4j_available:
        import importlib
        for filename, fn_name in tool_files:
            module_path = f"backend.tools.{filename[:-3]}"
            try:
                module = importlib.import_module(module_path)
                check(callable(getattr(module, fn_name, None)), f"{module_path}.{fn_name} is callable")
            except Exception as e:
                check(False, f"{module_path} import failed: {e}")
    else:
        for filename, fn_name in tool_files:
            path = tools_dir / filename
            check(path.exists(), f"tools/{filename} exists")
            content = path.read_text()
            check(f"def {fn_name}" in content, f"tools/{filename} defines {fn_name}")
            check("from backend.knowledge_graph.connection import execute_query" in content,
                  f"tools/{filename} imports execute_query")


# ---------------------------------------------------------------------------
# Section 4: TripGraph builder
# ---------------------------------------------------------------------------

def test_trip_graph_builder():
    print("\n=== Section 4: Trip graph builder ===")
    from backend.planner.trip_graph_builder import (
        TripNode, TripEdge, TripGraph, build_trip_graph,
    )

    # Dataclass construction
    node = TripNode(node_id="test", node_type="origin", name="Gurugram", day=1)
    check(node.node_id == "test", "TripNode construction works")
    check(node.is_mandatory is True, "TripNode.is_mandatory defaults to True")
    check(node.cost_per_person == 0, "TripNode.cost_per_person defaults to 0")

    edge = TripEdge(from_node="origin", to_node="waypoint_0", mode="drive")
    check(edge.mode == "drive", "TripEdge construction works")

    graph = TripGraph()
    graph.add_node(node)
    check("test" in graph.nodes, "TripGraph.add_node stores node")
    check("test" in graph.adjacency, "TripGraph.add_node initialises adjacency list")

    graph.add_edge(edge)
    check(len(graph.edges) == 1, "TripGraph.add_edge stores edge")

    # Full graph build
    g = build_trip_graph(
        route=_ROUTE, transport=_TRANSPORT, hotel=_HOTEL,
        activities=_ACTIVITIES, restaurants=_RESTAURANTS,
        waypoints=_WAYPOINTS, constraints=_CONSTRAINTS,
    )
    check(isinstance(g, TripGraph), "build_trip_graph returns TripGraph")
    check("origin" in g.nodes, "trip graph has 'origin' node")
    check("hotel_checkin" in g.nodes, "trip graph has 'hotel_checkin' node")
    check("return" in g.nodes, "trip graph has 'return' node")
    check(len(g.nodes) >= 4, f"trip graph has at least 4 nodes ({len(g.nodes)} found)")
    check(len(g.edges) >= 3, f"trip graph has at least 3 edges ({len(g.edges)} found)")

    ordered = g.get_ordered_nodes()
    check(len(ordered) == len(g.nodes), "get_ordered_nodes returns all nodes")
    check(ordered[0].day <= ordered[-1].day, "nodes are sorted by day")

    hotel_node = g.nodes["hotel_checkin"]
    check(hotel_node.cost_per_person == 4200 / 4, "hotel cost is price_per_night / group_size")


# ---------------------------------------------------------------------------
# Section 5: Candidate generator
# ---------------------------------------------------------------------------

def test_candidate_generator():
    print("\n=== Section 5: Candidate generator ===")
    from backend.planner.candidate_generator import generate_candidates

    data = {
        "routes": [_ROUTE],
        "hotels": [_HOTEL],
        "transport": [_TRANSPORT],
        "activities": _ACTIVITIES,
        "food": _RESTAURANTS,
        "waypoints": _WAYPOINTS,
    }
    candidates = generate_candidates(_CONSTRAINTS, data)
    check(len(candidates) >= 1, f"generates at least 1 candidate ({len(candidates)} found)")

    c = candidates[0]
    check("route" in c, "candidate has 'route'")
    check("hotel" in c, "candidate has 'hotel'")
    check("transport" in c, "candidate has 'transport'")
    check("activities" in c, "candidate has 'activities'")
    check("cost_breakdown" in c, "candidate has 'cost_breakdown'")
    check("total_cost_per_person" in c, "candidate has 'total_cost_per_person'")
    check("trip_graph" in c, "candidate has 'trip_graph' (TripGraph object)")
    check(c["cost_breakdown"]["transport"] == 9500 // 4, "transport cost_per_person = cost_total / group_size")
    check(c["cost_breakdown"]["miscellaneous"] == 2000, "miscellaneous is fixed ₹2000")

    # Multiple routes
    route_jaipur = {**_ROUTE, "route_id": "gurugram_jaipur_2d1n", "destination": "Jaipur", "destination_type": "heritage"}
    hotel_jaipur = {**_HOTEL, "hotel_id": "jaipur_comfort_01", "destination": "Jaipur"}
    transport_jaipur = {**_TRANSPORT, "transport_id": "cab_jaipur_comfort", "route_id": "gurugram_jaipur_2d1n"}
    data2 = {
        "routes": [_ROUTE, route_jaipur],
        "hotels": [_HOTEL, hotel_jaipur],
        "transport": [_TRANSPORT, transport_jaipur],
        "activities": _ACTIVITIES + [{**_ACTIVITIES[0], "destination": "Jaipur", "activity_id": "jaipur_act_01"}],
        "food": _RESTAURANTS,
        "waypoints": _WAYPOINTS,
    }
    candidates2 = generate_candidates(_CONSTRAINTS, data2)
    check(len(candidates2) >= 2, f"generates candidates for multiple routes ({len(candidates2)} found)")


# ---------------------------------------------------------------------------
# Section 6: Scorer
# ---------------------------------------------------------------------------

def test_scorer():
    print("\n=== Section 6: Multi-objective scorer ===")
    from backend.planner.scorer import score_itinerary

    scores = score_itinerary(_CANDIDATE, _CONSTRAINTS)
    check("final_score" in scores, "score_itinerary returns final_score")
    check("preference_match" in scores, "score has preference_match")
    check("budget_efficiency" in scores, "score has budget_efficiency")
    check("comfort" in scores, "score has comfort")
    check("scenic" in scores, "score has scenic")
    check("fatigue" in scores, "score has fatigue")
    check("risk" in scores, "score has risk")
    check("night_driving_penalty" in scores, "score has night_driving_penalty")
    check(scores["final_score"] > 0, f"final_score is positive ({scores['final_score']:.1f})")
    check(scores["night_driving_penalty"] == 0, "no penalty when cab_with_driver night_driving_allowed=False")

    # Night driving penalty
    self_drive = {**_TRANSPORT, "mode": "self_drive", "night_driving_allowed": True}
    penalised = score_itinerary({**_CANDIDATE, "transport": self_drive}, _CONSTRAINTS)
    check(penalised["night_driving_penalty"] == -20, "self_drive + avoid_night_driving = -20 penalty")
    check(penalised["final_score"] < scores["final_score"], "night driving penalty reduces total score")

    # Budget exceeded → budget_efficiency = 0
    over_budget = score_itinerary({**_CANDIDATE, "total_cost_per_person": 20000}, _CONSTRAINTS)
    check(over_budget["budget_efficiency"] == 0, "cost > budget gives budget_efficiency = 0")

    # Must-include fully matched
    check(scores["preference_match"] > 0, "preference_match > 0 when activities match must_include")


# ---------------------------------------------------------------------------
# Section 7: Validator
# ---------------------------------------------------------------------------

def test_validator():
    print("\n=== Section 7: Constraint validator ===")
    from backend.planner.validator import validate_itinerary

    # Valid candidate
    report = validate_itinerary(_CANDIDATE, _CONSTRAINTS)
    check(report["is_valid"] is True, "valid candidate passes validation")
    check(report["hard_constraint_violations"] == [], "no hard violations for valid candidate")

    # Budget violation
    over = {**_CANDIDATE, "total_cost_per_person": 20000}
    r = validate_itinerary(over, _CONSTRAINTS)
    check(r["is_valid"] is False, "budget violation → is_valid=False")
    check(any("budget" in v.lower() or "₹" in v for v in r["hard_constraint_violations"]),
          "budget violation message in hard_violations")

    # Destination type mismatch — jaipur heritage against mountains constraint
    jaipur_route = {**_ROUTE, "destination_type": "heritage"}
    jaipur_itinerary = {**_CANDIDATE, "route": jaipur_route}
    r2 = validate_itinerary(jaipur_itinerary, _CONSTRAINTS)
    check(r2["is_valid"] is False, "destination_type mismatch → is_valid=False")
    check(any("type" in v.lower() for v in r2["hard_constraint_violations"]),
          "destination type violation message present")

    # Night driving with self_drive
    self_drive = {**_TRANSPORT, "mode": "self_drive", "night_driving_allowed": True}
    nd_itinerary = {**_CANDIDATE, "transport": self_drive}
    r3 = validate_itinerary(nd_itinerary, _CONSTRAINTS)
    check(r3["is_valid"] is False, "self_drive + night_driving_allowed + avoid_night_driving → violation")

    # Missing must-include
    no_rafting = {**_CANDIDATE, "activities": [_ACTIVITIES[1]]}  # only aarti, no rafting
    r4 = validate_itinerary(no_rafting, _CONSTRAINTS)
    check(r4["is_valid"] is False, "missing must_include activity → is_valid=False")
    check(any("missing" in v.lower() for v in r4["hard_constraint_violations"]),
          "missing activity message in hard_violations")

    # Soft warning — low comfort hotel
    low_comfort_hotel = {**_HOTEL, "comfort_score": 3}
    low_c = {**_CANDIDATE, "hotel": low_comfort_hotel}
    r5 = validate_itinerary(low_c, _CONSTRAINTS)
    check(len(r5["soft_constraint_warnings"]) > 0, "comfort_score < 5 generates soft warning")


# ---------------------------------------------------------------------------
# Section 8: Timeline generator
# ---------------------------------------------------------------------------

def test_timeline_generator():
    print("\n=== Section 8: Timeline generator ===")
    from backend.planner.timeline_generator import generate_timeline

    timeline = generate_timeline(_CANDIDATE)
    check(len(timeline) >= 6, f"generates at least 6 events ({len(timeline)} found)")

    event_types = {e["type"] for e in timeline}
    check("travel" in event_types, "timeline includes travel events")
    check("meal" in event_types, "timeline includes meal events")
    check("hotel" in event_types, "timeline includes hotel event")

    # Chronological check within each day
    for day in [1, 2]:
        day_events = [e for e in timeline if e["day"] == day]
        for i in range(len(day_events) - 1):
            a, b = day_events[i], day_events[i + 1]
            check(
                a["start_time"] <= b["start_time"],
                f"day {day}: '{a['title']}' ({a['start_time']}) before '{b['title']}' ({b['start_time']})",
            )

    # Required fields on every event
    for ev in timeline:
        check("day" in ev and "start_time" in ev and "end_time" in ev and "title" in ev and "type" in ev,
              f"event '{ev.get('title', '?')}' has all required fields")

    # First event is always travel (departure)
    check(timeline[0]["type"] == "travel", "first event is travel (departure)")
    check(timeline[0]["day"] == 1, "first event is on day 1")

    # Last event is always travel (return)
    check(timeline[-1]["type"] == "travel", "last event is travel (return)")
    check(timeline[-1]["day"] == 2, "last event is on day 2")

    # Route names in events
    any_origin = any("Gurugram" in e["title"] for e in timeline)
    check(any_origin, "timeline uses route origin name 'Gurugram'")
    any_dest = any("Rishikesh" in e["title"] or "Little Buddha" in e["title"] for e in timeline)
    check(any_dest, "timeline uses destination name or restaurant name")


# ---------------------------------------------------------------------------
# Section 9: Replanner
# ---------------------------------------------------------------------------

def test_replanner():
    print("\n=== Section 9: Delay replanner ===")
    from backend.planner.replanner import replan_itinerary

    # Moderate delay (90 min) — should be absorbed by compression
    result = replan_itinerary(_CANDIDATE, {"delay_type": "departure_delay", "delay_minutes": 90}, _CONSTRAINTS)
    check("updated_itinerary" in result, "replan returns updated_itinerary")
    check("changes" in result, "replan returns changes list")
    check("delay_absorbed" in result, "replan returns delay_absorbed")
    check("delay_remaining" in result, "replan returns delay_remaining")
    check(len(result["changes"]) >= 1, f"90-min delay generates at least 1 change ({len(result['changes'])} found)")

    # Timeline in result should still be chronological (day 1)
    tl = result["updated_itinerary"].get("timeline", [])
    check(len(tl) >= 6, f"replanned timeline has at least 6 events ({len(tl)} found)")
    day1 = [e for e in tl if e.get("day") == 1]
    for i in range(len(day1) - 1):
        a, b = day1[i], day1[i + 1]
        check(
            a["start_time"] <= b["start_time"],
            f"replanned day 1: '{a['title']}' ({a['start_time']}) ≤ '{b['title']}' ({b['start_time']})",
        )

    # Zero delay — should still return a valid result
    result0 = replan_itinerary(_CANDIDATE, {"delay_type": "departure_delay", "delay_minutes": 0}, _CONSTRAINTS)
    check("updated_itinerary" in result0, "zero-delay replan returns updated_itinerary")

    # Large delay (240 min) — should generate multiple changes
    result_large = replan_itinerary(_CANDIDATE, {"delay_type": "departure_delay", "delay_minutes": 240}, _CONSTRAINTS)
    check(len(result_large["changes"]) >= 1, "large delay also generates changes")

    # Delay absorbed ≤ delay total
    check(result["delay_absorbed"] + result["delay_remaining"] == 90,
          "delay_absorbed + delay_remaining = delay_minutes (90)")


# ---------------------------------------------------------------------------
# Section 10: Full integration — pipeline from data to selection
# ---------------------------------------------------------------------------

def test_integration():
    print("\n=== Section 10: Full pipeline integration ===")
    from backend.planner.candidate_generator import generate_candidates
    from backend.planner.scorer import score_itinerary
    from backend.planner.validator import validate_itinerary
    from backend.planner.timeline_generator import generate_timeline

    # Jaipur route added to verify destination_type filtering
    route_jaipur = {**_ROUTE, "route_id": "gurugram_jaipur_2d1n", "destination": "Jaipur", "destination_type": "heritage"}
    hotel_jaipur = {**_HOTEL, "hotel_id": "jaipur_comfort_01", "destination": "Jaipur", "name": "Heritage Haveli"}
    transport_jaipur = {**_TRANSPORT, "transport_id": "cab_jaipur_comfort", "route_id": "gurugram_jaipur_2d1n"}
    activity_jaipur = {**_ACTIVITIES[0], "activity_id": "amber_fort_01", "destination": "Jaipur",
                       "name": "Amber Fort", "tags": ["heritage", "fort"]}

    data = {
        "routes": [_ROUTE, route_jaipur],
        "hotels": [_HOTEL, hotel_jaipur],
        "transport": [_TRANSPORT, transport_jaipur],
        "activities": _ACTIVITIES + [activity_jaipur],
        "food": _RESTAURANTS,
        "waypoints": _WAYPOINTS,
    }
    candidates = generate_candidates(_CONSTRAINTS, data)
    check(len(candidates) >= 2, f"pipeline generates ≥2 candidates ({len(candidates)} found)")

    scored = []
    for c in candidates:
        s = score_itinerary(c, _CONSTRAINTS)
        v = validate_itinerary(c, _CONSTRAINTS)
        scored.append((c, s, v))

    valid = [(c, s, v) for c, s, v in scored if v["is_valid"]]
    check(len(valid) >= 1, f"at least 1 candidate passes validation ({len(valid)} valid)")

    # Best candidate should be Rishikesh (mountains match, not Jaipur heritage)
    if valid:
        valid_sorted = sorted(valid, key=lambda x: x[1]["final_score"], reverse=True)
        best, best_scores, best_val = valid_sorted[0]
        check(best["destination"] == "Rishikesh", f"best valid candidate is Rishikesh (got {best['destination']})")

        timeline = generate_timeline(best)
        check(len(timeline) >= 6, f"full pipeline timeline has ≥6 events ({len(timeline)} found)")
        check(timeline[0]["day"] == 1, "timeline starts on day 1")
        check(timeline[-1]["day"] == 2, "timeline ends on day 2")
        check(all("start_time" in e for e in timeline), "all timeline events have start_time")

    # Jaipur must fail validation (destination_type mismatch against 'mountains' constraint)
    jaipur_scored = [(c, s, v) for c, s, v in scored if c["destination"] == "Jaipur"]
    if jaipur_scored:
        _, _, jaipur_val = jaipur_scored[0]
        check(jaipur_val["is_valid"] is False, "Jaipur route rejected (destination_type heritage ≠ mountains)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_kg_imports()
    test_query_outputs()
    test_tool_imports()
    test_trip_graph_builder()
    test_candidate_generator()
    test_scorer()
    test_validator()
    test_timeline_generator()
    test_replanner()
    test_integration()

    print(f"\n{'='*50}")
    print(f"Bucket 5 results: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        print("❌ Some checks failed — review output above")
        sys.exit(1)
    else:
        print("✅ All checks passed")
