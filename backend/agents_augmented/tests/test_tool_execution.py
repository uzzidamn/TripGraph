"""
Tests for execute_tool().
No external dependencies — if real tools fail (Neo4j down),
the mock fallback ensures results are always valid.
"""
import pytest
from backend.agents_augmented.tool_executor import execute_tool

# Minimal valid itinerary for planner tool tests
_ITINERARY = {
    "route": {
        "route_id": "route-gurgaon-rishikesh",
        "origin": "Gurugram",
        "destination": "Rishikesh",
        "risk_level": "medium",
        "scenic_score": 8,
    },
    "transport": {
        "route_id": "route-gurgaon-rishikesh",
        "mode": "cab",
        "comfort_score": 7,
        "cost_total": 8000,
        "fatigue_score": 5,
        "night_driving_allowed": False,
    },
    "hotel": {
        "destination": "Rishikesh",
        "tier": "comfort",
        "price_per_night": 4000,
        "comfort_score": 8,
    },
    "activities": [
        {
            "name": "White Water Rafting",
            "destination": "Rishikesh",
            "cost_per_person": 1200,
            "duration_hours": 3,
            "tags": ["adventure", "rafting"],
        }
    ],
    "restaurants": [{"name": "Little Buddha", "avg_cost_per_person": 400}],
    "waypoints": [{"route_id": "route-gurgaon-rishikesh", "name": "Murthal"}],
    "destination": "Rishikesh",
    "total_cost_per_person": 4500,
    "cost_breakdown": {"transport": 2000, "hotel": 1000, "activities": 1200, "food": 400, "miscellaneous": 500, "total": 4500},
}

_CONSTRAINTS = {
    "origin": "Gurugram",
    "destination": "Rishikesh",
    "budget_per_person": 6000,
    "group_size": 4,
    "hotel_tier": "comfort",
    "must_include": ["rafting"],
    "trip_duration": "2D1N",
}

_DATA = {
    "routes": [_ITINERARY["route"]],
    "hotels": [_ITINERARY["hotel"]],
    "transport": [_ITINERARY["transport"]],
    "activities": _ITINERARY["activities"],
    "food": _ITINERARY["restaurants"],
    "waypoints": _ITINERARY["waypoints"],
}


# ---------------------------------------------------------------------------
# Retrieval tools
# ---------------------------------------------------------------------------

def test_get_routes_returns_list():
    r = execute_tool("get_routes", {"origin": "Gurugram"})
    assert "result" in r, r
    assert isinstance(r["result"], list)
    assert len(r["result"]) > 0


def test_get_hotels_returns_list():
    r = execute_tool("get_hotels", {"destination": "Rishikesh"})
    assert "result" in r
    assert isinstance(r["result"], list)
    assert len(r["result"]) > 0


def test_get_activities_returns_list():
    r = execute_tool("get_activities", {"destination": "Rishikesh"})
    assert "result" in r
    assert isinstance(r["result"], list)
    assert len(r["result"]) > 0


def test_get_transport_options_returns_list():
    r = execute_tool("get_transport_options", {"route_id": "route-gurgaon-rishikesh"})
    assert "result" in r
    assert isinstance(r["result"], list)
    assert len(r["result"]) > 0


def test_get_restaurants_returns_list():
    r = execute_tool("get_restaurants", {"destination": "Rishikesh"})
    assert "result" in r
    assert isinstance(r["result"], list)
    assert len(r["result"]) > 0


def test_get_waypoints_returns_list():
    r = execute_tool("get_waypoints", {"route_id": "route-gurgaon-rishikesh"})
    assert "result" in r
    assert isinstance(r["result"], list)
    assert len(r["result"]) > 0


# ---------------------------------------------------------------------------
# Planner tools
# ---------------------------------------------------------------------------

def test_generate_candidates_returns_list():
    r = execute_tool("generate_candidates", {"constraints": _CONSTRAINTS, "data": _DATA})
    assert "result" in r, r
    assert isinstance(r["result"], list)
    assert len(r["result"]) > 0


def test_score_itinerary_has_final_score():
    r = execute_tool("score_itinerary", {"itinerary": _ITINERARY, "constraints": _CONSTRAINTS})
    assert "result" in r, r
    assert "final_score" in r["result"]


def test_validate_itinerary_has_is_valid():
    r = execute_tool("validate_itinerary", {"itinerary": _ITINERARY, "constraints": _CONSTRAINTS})
    assert "result" in r, r
    assert "is_valid" in r["result"]


def test_generate_timeline_returns_list():
    r = execute_tool("generate_timeline", {"itinerary": _ITINERARY})
    assert "result" in r, r
    assert isinstance(r["result"], list)
    assert len(r["result"]) > 0


def test_replan_itinerary_returns_updated():
    delay = {"delay_type": "departure_delay", "delay_minutes": 60}
    r = execute_tool("replan_itinerary", {
        "itinerary": _ITINERARY,
        "delay_event": delay,
        "constraints": _CONSTRAINTS,
    })
    assert "result" in r, r
    assert "updated_itinerary" in r["result"]
    assert "changes" in r["result"]


# ---------------------------------------------------------------------------
# Unknown tool
# ---------------------------------------------------------------------------

def test_unknown_tool_returns_error():
    r = execute_tool("nonexistent_tool", {})
    assert "error" in r
    assert "Unknown tool" in r["error"]
