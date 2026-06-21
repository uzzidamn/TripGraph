"""
Generate candidate itineraries by combining routes × transport × hotels × activities.
"""
import re

from backend.planner.trip_graph_builder import build_trip_graph


def _parse_nights(trip_duration) -> int:
    """Return number of hotel nights from trip_duration string."""
    if not trip_duration:
        return 1
    s = str(trip_duration).lower().strip()
    m = re.search(r"(\d+)\s*n", s)          # "XDYn" → Y nights
    if m:
        return max(1, int(m.group(1)))
    m = re.match(r"(\d+)\s*d", s)           # "XD" only → X-1 nights
    if m:
        return max(1, int(m.group(1)) - 1)
    m = re.match(r"(\d+)\s*week", s)
    if m:
        return int(m.group(1)) * 7 - 1
    m = re.match(r"(\d+)\s*day", s)
    if m:
        return max(1, int(m.group(1)) - 1)
    if "weekend" in s:
        return 1
    return 1


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

        # Honour transport_preference constraint if specified
        preferred_modes = constraints.get("transport_preference") or []
        if preferred_modes and transport_opts:
            filtered = [t for t in transport_opts if t.get("mode") in preferred_modes]
            if filtered:
                transport_opts = filtered
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
                group_size = constraints.get("group_size") or 4
                n_nights = _parse_nights(constraints.get("trip_duration"))

                # Transport: web-enriched data uses cost_per_person (per traveller);
                # seed data uses cost_total (vehicle hire total) ÷ group_size.
                if "cost_per_person" in transport:
                    transport_cost_pp = transport["cost_per_person"]
                else:
                    transport_cost_pp = transport.get("cost_total", 0) / max(group_size, 1)

                # Hotel: price_per_night × rooms_required × nights ÷ group_size
                rooms = hotel.get("rooms_required", 1) or 1
                hotel_cost_pp = hotel.get("price_per_night", 0) * rooms * n_nights / max(group_size, 1)

                activity_cost = sum(a.get("cost_per_person", 0) for a in activities)
                food_cost = sum(r.get("avg_cost_per_person", 0) for r in restaurants)
                misc = 500 * n_nights  # per-night buffer

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
