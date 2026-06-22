"""
Data retrieval helpers shared by the 5 domain sub-nodes (hotel, transport, activity,
food, waypoint). Also provides route_retriever_node — the graph node that fetches routes
and applies dedup, producing both route_candidates (filtered) and all_route_candidates.
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
    get_all_routes as _mock_get_all_routes,
    get_hotels as _mock_get_hotels,
    get_activities as _mock_get_activities,
    get_transport_options as _mock_get_transport_options,
    get_restaurants as _mock_get_restaurants,
    get_waypoints as _mock_get_waypoints,
)


def _call(real_fn, mock_fn, *args, **kwargs):
    if not _NEO4J:
        return mock_fn(*args, **kwargs)
    try:
        return real_fn(*args, **kwargs)
    except Exception as e:
        print(f"[DATA] Tool failed, using mock: {e}")
        return mock_fn(*args, **kwargs)


def retrieve_hotels(destination: str, constraints: dict) -> list[dict]:
    try:
        tier = constraints.get("hotel_tier")
        return _call(
            _real_get_hotels if _NEO4J else _mock_get_hotels,
            _mock_get_hotels, destination, tier,
        )
    except Exception as e:
        print(f"[DATA] hotel retriever failed for {destination}: {e}")
        return []


def retrieve_transport(route_id: str, constraints: dict) -> list[dict]:
    try:
        modes = constraints.get("transport_preference") or None
        return _call(
            _real_get_transport_options if _NEO4J else _mock_get_transport_options,
            _mock_get_transport_options, route_id, modes,
        )
    except Exception as e:
        print(f"[DATA] transport retriever failed for {route_id}: {e}")
        return []


def retrieve_activities(destination: str, constraints: dict) -> list[dict]:
    try:
        tags = constraints.get("must_include") or None
        return _call(
            _real_get_activities if _NEO4J else _mock_get_activities,
            _mock_get_activities, destination, tags,
        )
    except Exception as e:
        print(f"[DATA] activity retriever failed for {destination}: {e}")
        return []


def retrieve_food(destination: str, constraints: dict) -> list[dict]:
    try:
        return _call(
            _real_get_restaurants if _NEO4J else _mock_get_restaurants,
            _mock_get_restaurants, destination,
        )
    except Exception as e:
        print(f"[DATA] food retriever failed for {destination}: {e}")
        return []


def retrieve_waypoints(route_id: str, constraints: dict) -> list[dict]:
    try:
        return _call(
            _real_get_waypoints if _NEO4J else _mock_get_waypoints,
            _mock_get_waypoints, route_id,
        )
    except Exception as e:
        print(f"[DATA] waypoint retriever failed for {route_id}: {e}")
        return []


def route_retriever_node(state: TripState) -> dict:
    """LangGraph node: fetch all matching routes, apply dedup filter.

    Writes:
    - route_candidates      — dedup-filtered; sub-nodes use this for the primary plan
    - all_route_candidates  — unfiltered; planner falls back here if all visited
    """
    constraints = state.get("extracted_constraints") or {}
    visited = state.get("visited_destinations") or []
    dedup_override = (state.get("memory_context") or {}).get("dedup_override", False)

    origin = str(constraints.get("origin") or "Gurugram").strip().title()
    destination_type = constraints.get("destination_type")
    if destination_type:
        destination_type = str(destination_type).strip().lower()

    all_routes = _call(
        _real_get_routes if _NEO4J else _mock_get_routes,
        _mock_get_routes, origin, destination_type,
    )

    destination = str(constraints.get("destination") or "").strip().title() or None
    all_catalog_routes = _mock_get_all_routes()

    # Check 1: origin has no routes at all in the catalog
    if not all_routes:
        reason_parts = [f"origin '{origin}'"]
        if destination:
            reason_parts.insert(0, f"destination '{destination}'")
        if destination_type:
            reason_parts.append(f"type '{destination_type}'")
        return {
            "route_candidates": [],
            "all_route_candidates": [],
            "unsupported_route": {
                "origin": origin,
                "destination": destination,
                "destination_type": destination_type,
                "reason": " / ".join(reason_parts),
            },
            "suggested_routes": all_catalog_routes,
        }

    # Check 2: specific destination requested but no route goes there
    if destination:
        dest_routes = [r for r in all_routes if r.get("destination", "").lower() == destination.lower()]
        if not dest_routes:
            return {
                "route_candidates": [],
                "all_route_candidates": [],
                "unsupported_route": {
                    "origin": origin,
                    "destination": destination,
                    "destination_type": destination_type,
                    "reason": f"destination '{destination}' / origin '{origin}'",
                },
                "suggested_routes": all_catalog_routes,
            }
        # Narrow all_routes to only the matching destination
        all_routes = dest_routes

    if not dedup_override and visited:
        filtered_routes = [r for r in all_routes if r.get("destination") not in visited]
    else:
        filtered_routes = all_routes

    return {
        "route_candidates": filtered_routes,
        "all_route_candidates": all_routes,
        "unsupported_route": None,
        "suggested_routes": [],
    }
