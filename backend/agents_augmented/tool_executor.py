"""
Tool executor: dispatches LLM tool calls to real implementations,
falls back to mock_tools if the real tool raises an exception.
"""
from backend.agents_augmented import mock_tools as _mocks

# Real tool imports
from backend.tools.route_tool import get_routes as _real_get_routes
from backend.tools.hotel_tool import get_hotels as _real_get_hotels
from backend.tools.activity_tool import get_activities as _real_get_activities
from backend.tools.transport_tool import get_transport_options as _real_get_transport_options
from backend.tools.restaurant_tool import get_restaurants as _real_get_restaurants
from backend.tools.waypoint_tool import get_waypoints as _real_get_waypoints
from backend.planner.candidate_generator import generate_candidates as _real_generate_candidates
from backend.planner.scorer import score_itinerary as _real_score_itinerary
from backend.planner.validator import validate_itinerary as _real_validate_itinerary
from backend.planner.timeline_generator import generate_timeline as _real_generate_timeline
from backend.planner.replanner import replan_itinerary as _real_replan_itinerary

_REAL: dict[str, callable] = {
    "get_routes": _real_get_routes,
    "get_hotels": _real_get_hotels,
    "get_activities": _real_get_activities,
    "get_transport_options": _real_get_transport_options,
    "get_restaurants": _real_get_restaurants,
    "get_waypoints": _real_get_waypoints,
    "generate_candidates": _real_generate_candidates,
    "score_itinerary": _real_score_itinerary,
    "validate_itinerary": _real_validate_itinerary,
    "generate_timeline": _real_generate_timeline,
    "replan_itinerary": _real_replan_itinerary,
}

_MOCK: dict[str, callable] = {
    "get_routes": _mocks.get_routes,
    "get_hotels": _mocks.get_hotels,
    "get_activities": _mocks.get_activities,
    "get_transport_options": _mocks.get_transport_options,
    "get_restaurants": _mocks.get_restaurants,
    "get_waypoints": _mocks.get_waypoints,
    "generate_candidates": _mocks.generate_candidates,
    "score_itinerary": _mocks.score_itinerary,
    "validate_itinerary": _mocks.validate_itinerary,
    "generate_timeline": _mocks.generate_timeline,
    "replan_itinerary": _mocks.replan_itinerary,
}


_LOCATION_TOOLS = {
    "get_routes", "get_hotels", "get_activities", "get_restaurants", "get_waypoints"
}


def _normalize_location(value) -> str:
    """Normalize city/location strings to title case before tool dispatch."""
    if isinstance(value, str):
        return value.strip().title()
    return value


def _normalize_arguments(tool_name: str, arguments: dict) -> dict:
    """Apply location normalization to origin/destination args for retrieval tools."""
    if tool_name not in _LOCATION_TOOLS:
        return arguments
    normalized = dict(arguments)
    for key in ("origin", "destination"):
        if key in normalized:
            normalized[key] = _normalize_location(normalized[key])
    return normalized


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """
    Try the real tool first. If it raises (e.g. Neo4j unavailable),
    fall back to the mock. Returns {"result": ...} or {"error": ...}.
    """
    if tool_name not in _REAL:
        return {"error": f"Unknown tool: {tool_name}"}

    arguments = _normalize_arguments(tool_name, arguments)

    try:
        result = _REAL[tool_name](**arguments)
        return {"result": result}
    except Exception as real_err:
        try:
            result = _MOCK[tool_name](**arguments)
            return {"result": result}
        except Exception as mock_err:
            return {"error": f"real: {real_err}; mock: {mock_err}"}
