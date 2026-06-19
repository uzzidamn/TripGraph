"""
Mock tool implementations — same signatures as real backend.tools.* functions.
Used when NEO4J_ENABLED=false or as fallback on real tool errors.
"""

MOCK_ROUTES = [
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
]

MOCK_HOTELS = [
    {
        "hotel_id": "rishikesh_comfort_01",
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
        "destination": "Rishikesh",
    },
    {
        "hotel_id": "jaipur_comfort_01",
        "name": "Pink City Heritage Inn",
        "tier": "comfort",
        "price_per_night": 3800,
        "rooms_required": 1,
        "checkin_time": "13:00",
        "checkout_time": "11:00",
        "comfort_score": 7,
        "lat": 26.9124,
        "lng": 75.7873,
        "amenities": ["wifi", "parking", "pool"],
        "tags": ["heritage", "central"],
        "destination": "Jaipur",
    },
]

MOCK_ACTIVITIES = [
    {
        "activity_id": "rafting_rishikesh_01",
        "name": "White Water Rafting (16 km)",
        "category": "adventure",
        "duration_minutes": 180,
        "cost_per_person": 1800,
        "available_slots": ["09:00", "12:00"],
        "risk_level": "medium",
        "tags": ["adventure", "rafting", "water", "outdoor"],
        "lat": 30.1159,
        "lng": 78.3127,
        "destination": "Rishikesh",
    },
    {
        "activity_id": "aarti_rishikesh_01",
        "name": "Ganga Aarti at Triveni Ghat",
        "category": "spiritual",
        "duration_minutes": 60,
        "cost_per_person": 0,
        "available_slots": ["18:30"],
        "risk_level": "low",
        "tags": ["spiritual", "cultural", "evening", "free"],
        "lat": 30.1050,
        "lng": 78.2950,
        "destination": "Rishikesh",
    },
    {
        "activity_id": "amber_fort_jaipur_01",
        "name": "Amber Fort Tour",
        "category": "cultural",
        "duration_minutes": 150,
        "cost_per_person": 500,
        "available_slots": ["09:00", "11:00", "14:00"],
        "risk_level": "low",
        "tags": ["heritage", "fort", "history", "cultural"],
        "lat": 26.9855,
        "lng": 75.8513,
        "destination": "Jaipur",
    },
]

MOCK_TRANSPORT = [
    {
        "transport_id": "cab_rishikesh_comfort",
        "mode": "cab_with_driver",
        "tier": "comfort",
        "cost_total": 9500,
        "capacity": 4,
        "base_duration_minutes": 390,
        "night_driving_allowed": False,
        "comfort_score": 8,
        "fatigue_score": 3,
        "tags": ["ac", "sedan", "professional_driver"],
        "route_id": "gurugram_rishikesh_2d1n",
    },
    {
        "transport_id": "cab_jaipur_comfort",
        "mode": "cab_with_driver",
        "tier": "comfort",
        "cost_total": 7500,
        "capacity": 4,
        "base_duration_minutes": 300,
        "night_driving_allowed": True,
        "comfort_score": 7,
        "fatigue_score": 2,
        "tags": ["ac", "sedan"],
        "route_id": "gurugram_jaipur_2d1n",
    },
]

MOCK_RESTAURANTS = [
    {
        "restaurant_id": "rishikesh_cafe_01",
        "name": "Little Buddha Cafe",
        "meal_types": ["lunch", "dinner"],
        "avg_cost_per_person": 600,
        "avg_duration_minutes": 75,
        "tags": ["cafe", "river_view"],
        "lat": 30.1256,
        "lng": 78.3152,
        "destination": "Rishikesh",
    },
    {
        "restaurant_id": "jaipur_thali_01",
        "name": "Chokhi Dhani",
        "meal_types": ["dinner"],
        "avg_cost_per_person": 900,
        "avg_duration_minutes": 90,
        "tags": ["rajasthani", "cultural", "thali"],
        "lat": 26.8468,
        "lng": 75.8118,
        "destination": "Jaipur",
    },
]

MOCK_WAYPOINTS = [
    {
        "waypoint_id": "murthal_stop",
        "name": "Murthal Dhaba Belt",
        "type": "breakfast_stop",
        "km_from_origin": 35,
        "order": 1,
        "lat": 29.0281,
        "lng": 77.0474,
        "typical_stop_minutes": 30,
        "route_id": "gurugram_rishikesh_2d1n",
    },
    {
        "waypoint_id": "neemrana_stop",
        "name": "Neemrana Fort View",
        "type": "viewpoint",
        "km_from_origin": 120,
        "order": 1,
        "lat": 27.9897,
        "lng": 76.3886,
        "typical_stop_minutes": 20,
        "route_id": "gurugram_jaipur_2d1n",
    },
]


def get_routes(origin: str, destination_type: str | None = None) -> list[dict]:
    results = [r for r in MOCK_ROUTES if r["origin"].lower() == origin.strip().lower()]
    if destination_type:
        results = [r for r in results if r["destination_type"] == destination_type.strip().lower()]
    return results


def get_hotels(destination: str, tier: str | None = None) -> list[dict]:
    results = [h for h in MOCK_HOTELS if h.get("destination", "").lower() == destination.strip().lower()]
    if tier:
        results = [h for h in results if h["tier"] == tier.strip().lower()]
    return results


def get_activities(destination: str, tags: list[str] | None = None) -> list[dict]:
    results = [a for a in MOCK_ACTIVITIES if a.get("destination", "").lower() == destination.strip().lower()]
    if tags:
        tags_lower = [t.lower() for t in tags]
        results = [
            a for a in results
            if any(t in [x.lower() for x in a.get("tags", [])] for t in tags_lower)
        ]
    return results


def get_transport_options(route_id: str, modes: list[str] | None = None) -> list[dict]:
    results = [t for t in MOCK_TRANSPORT if t.get("route_id") == route_id]
    if modes:
        modes_lower = [m.lower() for m in modes]
        results = [t for t in results if t["mode"].lower() in modes_lower]
    return results


def get_restaurants(destination: str, route_id: str | None = None) -> list[dict]:
    results = [r for r in MOCK_RESTAURANTS if r.get("destination", "").lower() == destination.strip().lower()]
    if route_id:
        results = [r for r in results if r.get("route_id") == route_id or r.get("destination", "").lower() == destination.strip().lower()]
    return results


def get_waypoints(route_id: str) -> list[dict]:
    return [w for w in MOCK_WAYPOINTS if w.get("route_id") == route_id]
