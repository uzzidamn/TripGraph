"""
Agent 3: Data Retriever
Fetches travel domain data from Neo4j via tool functions.

No LLM call. Falls back to mock data if Neo4j is unreachable at call time.
Mock IDs match Bucket 1 seed data exactly for seamless transition.
"""
from backend.agents.state import TripState

# ---------------------------------------------------------------------------
# Mock fallback data (IDs match backend/data/seed_*.json from Bucket 1)
# ---------------------------------------------------------------------------

_MOCK_ROUTES = [
    {
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
    },
    {
        "route_id": "gurugram_jaipur_2d1n",
        "origin": "Gurugram",
        "destination": "Jaipur",
        "destination_type": "heritage",
        "distance_km": 240,
        "base_drive_minutes": 300,
        "risk_level": "low",
        "scenic_score": 5,
        "dest_lat": 26.9124,
        "dest_lng": 75.7873,
    },
    {
        "route_id": "gurugram_tirthan_3d2n",
        "origin": "Gurugram",
        "destination": "Tirthan Valley",
        "destination_type": "mountains",
        "distance_km": 510,
        "base_drive_minutes": 720,
        "risk_level": "high",
        "scenic_score": 9,
        "dest_lat": 31.6381,
        "dest_lng": 77.4511,
    },
]

_MOCK_HOTELS = [
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
        "tags": ["riverside", "central"],
    },
    {
        "hotel_id": "jaipur_comfort_01",
        "destination": "Jaipur",
        "name": "Heritage Haveli Resort",
        "tier": "comfort",
        "price_per_night": 4500,
        "rooms_required": 1,
        "checkin_time": "14:00",
        "checkout_time": "11:00",
        "comfort_score": 8,
        "lat": 26.9124,
        "lng": 75.7873,
        "amenities": ["wifi", "parking", "restaurant", "pool", "heritage_architecture"],
        "tags": ["heritage", "haveli", "central"],
    },
]

_MOCK_ACTIVITIES = [
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

_MOCK_TRANSPORT = [
    {
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
        "tags": ["ac", "sedan", "professional_driver"],
    },
    {
        "transport_id": "cab_jaipur_comfort",
        "route_id": "gurugram_jaipur_2d1n",
        "mode": "cab_with_driver",
        "tier": "comfort",
        "cost_total": 8500,
        "capacity": 4,
        "base_duration_minutes": 300,
        "night_driving_allowed": False,
        "comfort_score": 8,
        "fatigue_score": 3,
        "tags": ["ac", "sedan", "professional_driver"],
    },
]

_MOCK_RESTAURANTS = [
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

_MOCK_WAYPOINTS = [
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


def _get_mock_for_route(route_id: str, destination: str) -> dict:
    """Return mock data filtered for a specific route/destination."""
    return {
        "hotels": [h for h in _MOCK_HOTELS if h.get("destination") == destination],
        "activities": [a for a in _MOCK_ACTIVITIES if a.get("destination") == destination],
        "transport": [t for t in _MOCK_TRANSPORT if t.get("route_id") == route_id],
        "restaurants": [r for r in _MOCK_RESTAURANTS
                        if r.get("destination") == destination or r.get("route_id") == route_id],
        "waypoints": [w for w in _MOCK_WAYPOINTS if w.get("route_id") == route_id],
    }


def data_retriever_node(state: TripState) -> dict:
    """Fetch travel data from Neo4j via tool functions.

    Calls tools sequentially: routes first, then per-route data.
    Falls back to mock data if any tool call raises (Neo4j offline).
    All results are aggregated into flat candidate lists.
    """
    constraints = state["extracted_constraints"]
    origin = constraints.get("origin", "Gurugram")
    destination_type = constraints.get("destination_type")
    destination = constraints.get("destination")
    hotel_tier = constraints.get("hotel_tier")
    must_include = constraints.get("must_include") or []

    # --- Fetch routes ---
    routes: list[dict] = []
    try:
        from backend.tools.route_tool import get_routes
        routes = get_routes(origin, destination_type)
        if not routes:
            routes = _MOCK_ROUTES
    except Exception as e:
        print(f"  ⚠️  route_tool failed ({e}), using mock routes")
        routes = _MOCK_ROUTES

    # Filter to specific destination if extracted
    if destination:
        routes = [r for r in routes if r.get("destination") == destination] or routes

    # Filter by destination_type if specified
    if destination_type:
        filtered = [r for r in routes if r.get("destination_type") == destination_type]
        routes = filtered if filtered else routes

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
                hotels = _get_mock_for_route(route_id, dest)["hotels"]
        except Exception as e:
            print(f"  ⚠️  hotel_tool failed for {dest} ({e}), using mock")
            hotels = _get_mock_for_route(route_id, dest)["hotels"]
        # Attach destination field for candidate_generator filtering
        for h in hotels:
            h.setdefault("destination", dest)
        all_hotels.extend(hotels)

        # Activities
        try:
            from backend.tools.activity_tool import get_activities
            activities = get_activities(dest, must_include if must_include else None)
            if not activities:
                activities = _get_mock_for_route(route_id, dest)["activities"]
        except Exception as e:
            print(f"  ⚠️  activity_tool failed for {dest} ({e}), using mock")
            activities = _get_mock_for_route(route_id, dest)["activities"]
        for a in activities:
            a.setdefault("destination", dest)
        all_activities.extend(activities)

        # Transport
        try:
            from backend.tools.transport_tool import get_transport_options
            transport = get_transport_options(route_id)
            if not transport:
                transport = _get_mock_for_route(route_id, dest)["transport"]
        except Exception as e:
            print(f"  ⚠️  transport_tool failed for {route_id} ({e}), using mock")
            transport = _get_mock_for_route(route_id, dest)["transport"]
        for t in transport:
            t.setdefault("route_id", route_id)
        all_transport.extend(transport)

        # Restaurants (destination + highway)
        try:
            from backend.tools.restaurant_tool import get_restaurants
            restaurants = get_restaurants(dest, route_id)
            if not restaurants:
                restaurants = _get_mock_for_route(route_id, dest)["restaurants"]
        except Exception as e:
            print(f"  ⚠️  restaurant_tool failed for {dest} ({e}), using mock")
            restaurants = _get_mock_for_route(route_id, dest)["restaurants"]
        all_restaurants.extend(restaurants)

        # Waypoints
        try:
            from backend.tools.waypoint_tool import get_waypoints
            waypoints = get_waypoints(route_id)
            if not waypoints:
                waypoints = _get_mock_for_route(route_id, dest)["waypoints"]
        except Exception as e:
            print(f"  ⚠️  waypoint_tool failed for {route_id} ({e}), using mock")
            waypoints = _get_mock_for_route(route_id, dest)["waypoints"]
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
