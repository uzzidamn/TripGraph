"""
Mock implementations of all 11 tools.
Runtime fallback when Neo4j is unavailable (retrieval tools)
or when planner functions fail for any reason.
Field names match real tool output exactly.
"""

# ---------------------------------------------------------------------------
# Mock data — Gurugram → Rishikesh baseline
# ---------------------------------------------------------------------------

_ROUTES = [
    {
        "route_id": "route-gurgaon-rishikesh",
        "origin": "Gurugram",
        "destination": "Rishikesh",
        "destination_type": "adventure",
        "distance_km": 280,
        "drive_time_hours": 6,
        "base_drive_minutes": 360,
        "risk_level": "medium",
        "scenic_score": 8,
        "description": "Scenic NH58 drive through Haridwar to Rishikesh",
    }
]

_HOTELS = {
    "Rishikesh": [
        {
            "hotel_id": "hotel-rishikesh-ganga-comfort",
            "name": "Ganga View Retreat",
            "destination": "Rishikesh",
            "tier": "comfort",
            "price_per_night": 4000,
            "comfort_score": 8,
            "rating": 4.2,
            "amenities": ["wifi", "restaurant", "yoga_hall"],
        }
    ]
}

_ACTIVITIES = {
    "Rishikesh": [
        {
            "activity_id": "act-rafting-rishikesh",
            "name": "White Water Rafting",
            "destination": "Rishikesh",
            "cost_per_person": 1200,
            "duration_hours": 3,
            "tags": ["adventure", "rafting", "water_sport"],
        },
        {
            "activity_id": "act-ganga-aarti",
            "name": "Ganga Aarti",
            "destination": "Rishikesh",
            "cost_per_person": 0,
            "duration_hours": 1,
            "tags": ["cultural", "spiritual", "evening"],
        },
    ]
}

_TRANSPORT = {
    "route-gurgaon-rishikesh": [
        {
            "transport_id": "transport-cab-comfort",
            "route_id": "route-gurgaon-rishikesh",
            "mode": "cab",
            "comfort_score": 7,
            "cost_total": 8000,
            "fatigue_score": 5,
            "night_driving_allowed": False,
            "base_duration_minutes": 360,
        }
    ]
}

_RESTAURANTS = {
    "Rishikesh": [
        {
            "restaurant_id": "rest-little-buddha",
            "name": "Little Buddha Cafe",
            "destination": "Rishikesh",
            "route_id": "route-gurgaon-rishikesh",
            "avg_cost_per_person": 400,
            "cuisine": ["continental", "cafe"],
            "rating": 4.5,
        }
    ]
}

_WAYPOINTS = {
    "route-gurgaon-rishikesh": [
        {
            "waypoint_id": "wp-murthal",
            "route_id": "route-gurgaon-rishikesh",
            "name": "Murthal",
            "type": "food_stop",
            "distance_from_origin_km": 50,
            "lat": 29.089,
            "lng": 76.877,
        }
    ]
}


# ---------------------------------------------------------------------------
# Travel retrieval mocks — match backend/tools/ signatures exactly
# ---------------------------------------------------------------------------

def get_routes(origin: str, destination_type: str | None = None) -> list[dict]:
    results = [r for r in _ROUTES if r["origin"].lower() == origin.lower()]
    if destination_type:
        results = [r for r in results if r.get("destination_type") == destination_type]
    return results or list(_ROUTES)


def get_hotels(destination: str, tier: str | None = None) -> list[dict]:
    hotels = list(_HOTELS.get(destination, _HOTELS.get("Rishikesh", [])))
    if tier:
        hotels = [h for h in hotels if h.get("tier") == tier]
    return hotels or list(_HOTELS["Rishikesh"])


def get_activities(destination: str, tags: list[str] | None = None) -> list[dict]:
    activities = list(_ACTIVITIES.get(destination, _ACTIVITIES.get("Rishikesh", [])))
    if tags:
        tag_set = {t.lower() for t in tags}
        filtered = [a for a in activities if tag_set & {t.lower() for t in a.get("tags", [])}]
        activities = filtered or activities
    return activities


def get_transport_options(route_id: str, modes: list[str] | None = None) -> list[dict]:
    options = list(_TRANSPORT.get(route_id, _TRANSPORT.get("route-gurgaon-rishikesh", [])))
    if modes:
        options = [t for t in options if t.get("mode") in modes]
    return options or list(_TRANSPORT["route-gurgaon-rishikesh"])


def get_restaurants(destination: str, route_id: str | None = None) -> list[dict]:
    return list(_RESTAURANTS.get(destination, _RESTAURANTS.get("Rishikesh", [])))


def get_waypoints(route_id: str) -> list[dict]:
    return list(_WAYPOINTS.get(route_id, _WAYPOINTS.get("route-gurgaon-rishikesh", [])))


# ---------------------------------------------------------------------------
# Planner mocks — match backend/planner/ signatures exactly
# ---------------------------------------------------------------------------

def generate_candidates(constraints: dict, data: dict) -> list[dict]:
    routes = data.get("routes") or _ROUTES
    hotels = data.get("hotels") or list(_HOTELS["Rishikesh"])
    transport_list = data.get("transport") or list(_TRANSPORT["route-gurgaon-rishikesh"])
    activities = data.get("activities") or list(_ACTIVITIES["Rishikesh"])
    food = data.get("food") or list(_RESTAURANTS["Rishikesh"])
    waypoints = data.get("waypoints") or list(_WAYPOINTS["route-gurgaon-rishikesh"])

    group_size = constraints.get("group_size") or 4
    budget = constraints.get("budget_per_person") or 0
    candidates = []

    for route in routes:
        dest = route.get("destination", "Rishikesh")
        route_hotels = [h for h in hotels if h.get("destination") == dest] or hotels
        route_transport = [t for t in transport_list if t.get("route_id") == route.get("route_id")] or transport_list

        for hotel in route_hotels or [{}]:
            for transport in route_transport or [{}]:
                transport_pp = transport.get("cost_total", 0) / max(group_size, 1)
                hotel_pp = hotel.get("price_per_night", 0) / max(group_size, 1)
                activity_cost = sum(a.get("cost_per_person", 0) for a in activities)
                food_cost = sum(r.get("avg_cost_per_person", 0) for r in food)
                misc = 500
                total = round(transport_pp + hotel_pp + activity_cost + food_cost + misc)

                candidates.append({
                    "route": route,
                    "transport": transport,
                    "hotel": hotel,
                    "activities": activities,
                    "restaurants": food,
                    "waypoints": waypoints,
                    "destination": dest,
                    "total_cost_per_person": total,
                    "cost_breakdown": {
                        "transport": round(transport_pp),
                        "hotel": round(hotel_pp),
                        "activities": round(activity_cost),
                        "food": round(food_cost),
                        "miscellaneous": misc,
                        "total": total,
                        "budget_limit": budget,
                    },
                })

    return candidates or [_default_candidate(constraints)]


def score_itinerary(itinerary: dict, constraints: dict) -> dict:
    budget = constraints.get("budget_per_person") or 10000
    cost = itinerary.get("total_cost_per_person", 0)
    budget_score = 20 if cost <= budget else 0

    must_include = {str(x).lower() for x in (constraints.get("must_include") or [])}
    activity_tags: set[str] = set()
    for a in itinerary.get("activities", []):
        activity_tags.update(str(t).lower() for t in a.get("tags", []))
        if a.get("name"):
            activity_tags.add(a["name"].lower())
    pref_score = (len(must_include & activity_tags) / max(len(must_include), 1)) * 25 if must_include else 20

    comfort = itinerary.get("hotel", {}).get("comfort_score", 7)
    scenic = itinerary.get("route", {}).get("scenic_score", 8)
    fatigue = itinerary.get("transport", {}).get("fatigue_score", 5)

    return {
        "preference_match": pref_score,
        "budget_efficiency": budget_score,
        "comfort": comfort,
        "scenic": scenic,
        "fatigue": max(0, (10 - fatigue) * 1.5),
        "risk": 6,
        "night_driving_penalty": 0,
        "final_score": pref_score + budget_score + comfort + scenic,
    }


def validate_itinerary(itinerary: dict, constraints: dict) -> dict:
    hard_violations = []
    budget = constraints.get("budget_per_person")
    cost = itinerary.get("total_cost_per_person", 0)
    if budget and cost > budget:
        hard_violations.append(f"Cost ₹{cost} exceeds budget ₹{budget}")
    return {
        "is_valid": len(hard_violations) == 0,
        "hard_constraint_violations": hard_violations,
        "soft_constraint_warnings": [],
        "budget_used": cost,
        "budget_limit": budget,
        "must_include_satisfied": [],
    }


def generate_timeline(itinerary: dict) -> list[dict]:
    route = itinerary.get("route", {})
    waypoints = itinerary.get("waypoints", [])
    activities = itinerary.get("activities", [])
    restaurants = itinerary.get("restaurants", [])

    timeline = [
        {
            "day": 1,
            "start_time": "06:00",
            "end_time": "09:00",
            "title": f"Drive from {route.get('origin', 'Origin')} towards {route.get('destination', 'Destination')}",
            "type": "travel",
            "cost": 0,
        }
    ]

    if waypoints:
        timeline.append({
            "day": 1, "start_time": "09:00", "end_time": "09:45",
            "title": f"Breakfast stop at {waypoints[0].get('name', 'Highway Stop')}",
            "type": "meal", "cost": 200,
        })

    timeline.append({
        "day": 1, "start_time": "09:45", "end_time": "13:00",
        "title": f"Continue drive to {route.get('destination', 'Destination')}",
        "type": "travel", "cost": 0,
    })

    if restaurants:
        timeline.append({
            "day": 1, "start_time": "13:00", "end_time": "14:00",
            "title": f"Lunch at {restaurants[0].get('name', 'Local Restaurant')}",
            "type": "meal", "cost": restaurants[0].get("avg_cost_per_person", 300),
        })

    current_hour = 14
    for act in activities:
        duration = int(act.get("duration_hours", 2))
        end_hour = current_hour + duration
        timeline.append({
            "day": 1,
            "start_time": f"{current_hour:02d}:00",
            "end_time": f"{end_hour:02d}:00",
            "title": act.get("name", "Activity"),
            "type": "activity",
            "cost": act.get("cost_per_person", 0),
        })
        current_hour = end_hour

    timeline.append({
        "day": 2, "start_time": "08:00", "end_time": "14:00",
        "title": f"Return drive to {route.get('origin', 'Origin')}",
        "type": "travel", "cost": 0,
    })

    return timeline


def replan_itinerary(itinerary: dict, delay_event: dict, constraints: dict) -> dict:
    delay_minutes = delay_event.get("delay_minutes", 60)
    return {
        "updated_itinerary": {**itinerary, "replanned": True},
        "changes": [f"All events shifted by {delay_minutes} minutes due to {delay_event.get('delay_type', 'delay')}"],
        "delay_absorbed": 0,
        "delay_remaining": delay_minutes,
    }


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _default_candidate(constraints: dict) -> dict:
    group_size = constraints.get("group_size") or 4
    route = _ROUTES[0]
    hotel = _HOTELS["Rishikesh"][0]
    transport = _TRANSPORT["route-gurgaon-rishikesh"][0]
    activities = _ACTIVITIES["Rishikesh"]
    food = _RESTAURANTS["Rishikesh"]
    waypoints = _WAYPOINTS["route-gurgaon-rishikesh"]

    transport_pp = transport["cost_total"] / group_size
    hotel_pp = hotel["price_per_night"] / group_size
    activity_cost = sum(a["cost_per_person"] for a in activities)
    food_cost = sum(r["avg_cost_per_person"] for r in food)
    misc = 500
    total = round(transport_pp + hotel_pp + activity_cost + food_cost + misc)

    return {
        "route": route,
        "transport": transport,
        "hotel": hotel,
        "activities": activities,
        "restaurants": food,
        "waypoints": waypoints,
        "destination": route["destination"],
        "total_cost_per_person": total,
        "cost_breakdown": {
            "transport": round(transport_pp),
            "hotel": round(hotel_pp),
            "activities": round(activity_cost),
            "food": round(food_cost),
            "miscellaneous": misc,
            "total": total,
            "budget_limit": constraints.get("budget_per_person") or 0,
        },
    }
