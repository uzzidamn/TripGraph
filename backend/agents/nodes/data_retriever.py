"""
Agent 3: Data Retriever
Fetches travel domain data from Neo4j via tool functions.

No LLM call. Falls back to seed JSON files (backend/data/seed_*.json) if Neo4j
is unreachable. This gives the full 18 hotels × 12 transport options × 15 activities
instead of the old sparse hardcoded arrays, so the planner generates diverse candidates.
"""
import json
from functools import lru_cache
from pathlib import Path

from backend.agents.state import TripState

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


@lru_cache(maxsize=1)
def _load_seed_data() -> dict:
    """Load and enrich all seed JSON files once at import.

    Routes are enriched with destination_type / dest_lat / dest_lng from the
    cities file (matching what the Neo4j queries.py projection returns).
    Restaurants that are highway stops keep their route_id; destination
    restaurants keep their destination field.
    """
    def _read(filename):
        path = _DATA_DIR / filename
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    cities_list = _read("seed_cities.json")
    city_by_name = {c["name"]: c for c in cities_list}

    # Enrich routes: add origin (already present) + destination_type + dest_lat/lng
    raw_routes = _read("seed_routes.json")
    routes = []
    for r in raw_routes:
        dest_city = city_by_name.get(r["destination"], {})
        routes.append({
            **r,
            "destination_type": dest_city.get("type", ""),
            "dest_lat": dest_city.get("lat", 0.0),
            "dest_lng": dest_city.get("lng", 0.0),
        })

    return {
        "routes": routes,
        "hotels": _read("seed_hotels.json"),
        "activities": _read("seed_activities.json"),
        "transport": _read("seed_transport.json"),
        "restaurants": _read("seed_restaurants.json"),
        "waypoints": _read("seed_waypoints.json"),
    }


def _seed_mock_for_route(route_id: str, destination: str) -> dict:
    """Return seed data filtered for a specific route/destination."""
    sd = _load_seed_data()
    return {
        "hotels": [h for h in sd["hotels"] if h.get("destination") == destination],
        "activities": [a for a in sd["activities"] if a.get("destination") == destination],
        "transport": [t for t in sd["transport"] if t.get("route_id") == route_id],
        "restaurants": [
            r for r in sd["restaurants"]
            if r.get("destination") == destination or r.get("route_id") == route_id
        ],
        "waypoints": [w for w in sd["waypoints"] if w.get("route_id") == route_id],
    }


def data_retriever_node(state: TripState) -> dict:
    """Fetch travel data from Neo4j via tool functions.

    Calls tools sequentially: routes first, then per-route data.
    Falls back to seed JSON data if any tool call raises (Neo4j offline/not installed).
    All results are aggregated into flat candidate lists.
    """
    constraints = state["extracted_constraints"]
    origin = constraints.get("origin", "Gurugram")
    destination_type = constraints.get("destination_type")
    destination = constraints.get("destination")
    hotel_tier = constraints.get("hotel_tier")
    must_include = constraints.get("must_include") or []

    seed = _load_seed_data()

    # --- Fetch routes ---
    routes: list[dict] = []
    try:
        from backend.tools.route_tool import get_routes
        routes = get_routes(origin, destination_type, destination)
        if not routes:
            routes = seed["routes"]
    except Exception as e:
        print(f"  ⚠️  route_tool failed ({e}), using seed routes")
        routes = seed["routes"]

    # Filter to specific destination if extracted
    if destination:
        filtered = [r for r in routes if r.get("destination") == destination]
        if filtered:
            routes = filtered

    # Filter by destination_type if specified
    if destination_type:
        filtered = [r for r in routes if r.get("destination_type") == destination_type]
        if filtered:
            routes = filtered

    # --- Fetch per-route data ---
    all_hotels: list[dict] = []
    all_activities: list[dict] = []
    all_transport: list[dict] = []
    all_restaurants: list[dict] = []
    all_waypoints: list[dict] = []

    for route in routes:
        route_id = route.get("route_id", "")
        dest = route.get("destination", "")

        # Hotels
        try:
            from backend.tools.hotel_tool import get_hotels
            hotels = get_hotels(dest, hotel_tier)
            if not hotels:
                hotels = _seed_mock_for_route(route_id, dest)["hotels"]
        except Exception as e:
            print(f"  ⚠️  hotel_tool failed for {dest} ({e}), using seed")
            hotels = _seed_mock_for_route(route_id, dest)["hotels"]
        for h in hotels:
            h.setdefault("destination", dest)
        all_hotels.extend(hotels)

        # Activities
        try:
            from backend.tools.activity_tool import get_activities
            activities = get_activities(dest, must_include if must_include else None)
            if not activities:
                activities = _seed_mock_for_route(route_id, dest)["activities"]
        except Exception as e:
            print(f"  ⚠️  activity_tool failed for {dest} ({e}), using seed")
            activities = _seed_mock_for_route(route_id, dest)["activities"]
        for a in activities:
            a.setdefault("destination", dest)
        all_activities.extend(activities)

        # Transport
        try:
            from backend.tools.transport_tool import get_transport_options
            transport = get_transport_options(route_id)
            if not transport:
                transport = _seed_mock_for_route(route_id, dest)["transport"]
        except Exception as e:
            print(f"  ⚠️  transport_tool failed for {route_id} ({e}), using seed")
            transport = _seed_mock_for_route(route_id, dest)["transport"]
        for t in transport:
            t.setdefault("route_id", route_id)
        all_transport.extend(transport)

        # Restaurants
        try:
            from backend.tools.restaurant_tool import get_restaurants
            restaurants = get_restaurants(dest, route_id)
            if not restaurants:
                restaurants = _seed_mock_for_route(route_id, dest)["restaurants"]
        except Exception as e:
            print(f"  ⚠️  restaurant_tool failed for {dest} ({e}), using seed")
            restaurants = _seed_mock_for_route(route_id, dest)["restaurants"]
        all_restaurants.extend(restaurants)

        # Waypoints
        try:
            from backend.tools.waypoint_tool import get_waypoints
            waypoints = get_waypoints(route_id)
            if not waypoints:
                waypoints = _seed_mock_for_route(route_id, dest)["waypoints"]
        except Exception as e:
            print(f"  ⚠️  waypoint_tool failed for {route_id} ({e}), using seed")
            waypoints = _seed_mock_for_route(route_id, dest)["waypoints"]
        for w in waypoints:
            w.setdefault("route_id", route_id)
        all_waypoints.extend(waypoints)

    print(f"  ✅ Data retriever: {len(routes)} routes, {len(all_hotels)} hotels, "
          f"{len(all_activities)} activities, {len(all_transport)} transport, "
          f"{len(all_restaurants)} restaurants, {len(all_waypoints)} waypoints")

    return {
        "route_candidates": routes,
        "hotel_candidates": all_hotels,
        "transport_candidates": all_transport,
        "activity_candidates": all_activities,
        "food_candidates": all_restaurants,
        "waypoint_candidates": all_waypoints,
    }
