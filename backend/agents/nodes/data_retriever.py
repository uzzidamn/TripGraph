"""
Agent 3: fetch travel data via tool functions (real or mock).
"""
import os

from backend.agents.state import TripState

_NEO4J = os.getenv("NEO4J_ENABLED", "false").lower() == "true"

if _NEO4J:
    from backend.tools.route_tool import get_routes as _real_get_routes
    from backend.tools.hotel_tool import get_hotels as _real_get_hotels
    from backend.tools.activity_tool import get_activities as _real_get_activities
    from backend.tools.transport_tool import get_transport_options as _real_get_transport_options
    from backend.tools.restaurant_tool import get_restaurants as _real_get_restaurants
    from backend.tools.waypoint_tool import get_waypoints as _real_get_waypoints

from backend.agents.nodes.mock_tools import (
    get_routes as _mock_get_routes,
    get_hotels as _mock_get_hotels,
    get_activities as _mock_get_activities,
    get_transport_options as _mock_get_transport_options,
    get_restaurants as _mock_get_restaurants,
    get_waypoints as _mock_get_waypoints,
)


def _call(real_fn, mock_fn, *args, **kwargs):
    """Call real tool; fall back to mock on any exception."""
    if not _NEO4J:
        return mock_fn(*args, **kwargs)
    try:
        return real_fn(*args, **kwargs)
    except Exception as e:
        print(f"[DATA] Tool failed, using mock: {e}")
        return mock_fn(*args, **kwargs)


def data_retriever_node(state: TripState) -> dict:
    constraints = state.get("extracted_constraints") or {}

    # Normalize locations (Decision 21) defensively
    origin = str(constraints.get("origin") or "Gurugram").strip().title()
    destination_type = constraints.get("destination_type")
    if destination_type:
        destination_type = str(destination_type).strip().lower()

    # Fetch routes
    routes = _call(_real_get_routes if _NEO4J else _mock_get_routes,
                   _mock_get_routes, origin, destination_type)

    hotels: list[dict] = []
    activities: list[dict] = []
    transport: list[dict] = []
    food: list[dict] = []
    waypoints: list[dict] = []

    for route in routes:
        destination = str(route.get("destination", "")).strip().title()
        route_id = route.get("route_id", "")

        hotels.extend(_call(
            _real_get_hotels if _NEO4J else _mock_get_hotels,
            _mock_get_hotels, destination,
        ))
        activities.extend(_call(
            _real_get_activities if _NEO4J else _mock_get_activities,
            _mock_get_activities, destination,
        ))
        transport.extend(_call(
            _real_get_transport_options if _NEO4J else _mock_get_transport_options,
            _mock_get_transport_options, route_id,
        ))
        food.extend(_call(
            _real_get_restaurants if _NEO4J else _mock_get_restaurants,
            _mock_get_restaurants, destination,
        ))
        waypoints.extend(_call(
            _real_get_waypoints if _NEO4J else _mock_get_waypoints,
            _mock_get_waypoints, route_id,
        ))

    return {
        "route_candidates": routes,
        "hotel_candidates": hotels,
        "activity_candidates": activities,
        "transport_candidates": transport,
        "food_candidates": food,
        "waypoint_candidates": waypoints,
    }
