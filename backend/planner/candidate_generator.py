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
