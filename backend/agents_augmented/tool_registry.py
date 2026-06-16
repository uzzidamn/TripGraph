"""
Tool registry: neutral TOOLS list + provider-specific schema converters.
"""

TOOLS: list[dict] = [
    # -----------------------------------------------------------------------
    # Travel retrieval tools
    # -----------------------------------------------------------------------
    {
        "name": "get_routes",
        "description": (
            "Fetch available routes from an origin city. "
            "Returns a list of route objects with fields: "
            "route_id, origin, destination, destination_type, distance_km, "
            "drive_time_hours, risk_level, scenic_score."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "Departure city name (e.g. 'Gurugram')",
                },
                "destination_type": {
                    "type": "string",
                    "description": "Optional filter: adventure | heritage | nature",
                },
            },
            "required": ["origin"],
        },
    },
    {
        "name": "get_hotels",
        "description": (
            "Fetch hotels at a destination. "
            "Returns a list of hotel objects with fields: "
            "hotel_id, name, destination, tier, price_per_night, comfort_score, rating."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Destination city name",
                },
                "tier": {
                    "type": "string",
                    "description": "Optional filter: budget | comfort | expedition",
                },
            },
            "required": ["destination"],
        },
    },
    {
        "name": "get_activities",
        "description": (
            "Fetch activities at a destination. "
            "Returns a list with fields: activity_id, name, destination, "
            "cost_per_person, duration_hours, tags."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Destination city name",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tag filters (e.g. ['adventure', 'rafting'])",
                },
            },
            "required": ["destination"],
        },
    },
    {
        "name": "get_transport_options",
        "description": (
            "Fetch transport options for a route. "
            "Returns a list with fields: transport_id, route_id, mode, "
            "comfort_score, cost_total, fatigue_score, night_driving_allowed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "route_id": {
                    "type": "string",
                    "description": "Route ID from get_routes result",
                },
                "modes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional mode filters: cab | bus | self_drive | train",
                },
            },
            "required": ["route_id"],
        },
    },
    {
        "name": "get_restaurants",
        "description": (
            "Fetch restaurants at a destination. "
            "Returns a list with fields: restaurant_id, name, destination, "
            "route_id, avg_cost_per_person, cuisine, rating."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Destination city name",
                },
                "route_id": {
                    "type": "string",
                    "description": "Optional route ID to filter by",
                },
            },
            "required": ["destination"],
        },
    },
    {
        "name": "get_waypoints",
        "description": (
            "Fetch waypoints along a route (fuel stops, food stops, scenic points). "
            "Returns a list with fields: waypoint_id, route_id, name, type, "
            "distance_from_origin_km, lat, lng."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "route_id": {
                    "type": "string",
                    "description": "Route ID from get_routes result",
                },
            },
            "required": ["route_id"],
        },
    },
    # -----------------------------------------------------------------------
    # Planning tools
    # -----------------------------------------------------------------------
    {
        "name": "generate_candidates",
        "description": (
            "Generate itinerary candidates by combining collected travel data. "
            "IMPORTANT: the 'data' dict must use these exact keys: "
            "routes (from get_routes), hotels (from get_hotels), "
            "transport (from get_transport_options), activities (from get_activities), "
            "food (from get_restaurants), waypoints (from get_waypoints). "
            "Returns a list of candidate itinerary dicts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "constraints": {
                    "type": "object",
                    "description": (
                        "Extracted travel constraints: origin, destination, budget_per_person, "
                        "group_size, hotel_tier, must_include, trip_duration, etc."
                    ),
                },
                "data": {
                    "type": "object",
                    "description": (
                        "Collected travel data with keys: "
                        "routes (list), hotels (list), transport (list), "
                        "activities (list), food (list), waypoints (list)."
                    ),
                },
            },
            "required": ["constraints", "data"],
        },
    },
    {
        "name": "score_itinerary",
        "description": (
            "Score an itinerary candidate using a multi-objective function. "
            "Returns a dict with scores: preference_match, budget_efficiency, "
            "comfort, scenic, fatigue, risk, night_driving_penalty, final_score."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "itinerary": {
                    "type": "object",
                    "description": "A candidate itinerary dict from generate_candidates",
                },
                "constraints": {
                    "type": "object",
                    "description": "Travel constraints dict",
                },
            },
            "required": ["itinerary", "constraints"],
        },
    },
    {
        "name": "validate_itinerary",
        "description": (
            "Validate an itinerary against hard and soft constraints. "
            "Returns: is_valid, hard_constraint_violations, soft_constraint_warnings, "
            "budget_used, budget_limit. MUST be called before finalizing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "itinerary": {
                    "type": "object",
                    "description": "A candidate itinerary dict from generate_candidates",
                },
                "constraints": {
                    "type": "object",
                    "description": "Travel constraints dict",
                },
            },
            "required": ["itinerary", "constraints"],
        },
    },
    {
        "name": "generate_timeline",
        "description": (
            "Generate a sequential day-by-day timeline of events from an itinerary. "
            "Returns a list of event dicts with: day, start_time, end_time, title, type, cost. "
            "MUST be called before finalizing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "itinerary": {
                    "type": "object",
                    "description": "The selected itinerary dict",
                },
            },
            "required": ["itinerary"],
        },
    },
    # -----------------------------------------------------------------------
    # Replanning tools
    # -----------------------------------------------------------------------
    {
        "name": "replan_itinerary",
        "description": (
            "Adjust an itinerary after a delay event. "
            "Shifts/compresses/removes events to absorb the delay. "
            "Returns: updated_itinerary, changes (list of strings), "
            "delay_absorbed (minutes), delay_remaining (minutes)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "itinerary": {
                    "type": "object",
                    "description": "The currently selected itinerary dict",
                },
                "delay_event": {
                    "type": "object",
                    "description": "Delay event: {delay_type: str, delay_minutes: int}",
                },
                "constraints": {
                    "type": "object",
                    "description": "Original travel constraints dict",
                },
            },
            "required": ["itinerary", "delay_event", "constraints"],
        },
    },
]

TOOL_NAMES: set[str] = {t["name"] for t in TOOLS}


# ---------------------------------------------------------------------------
# Provider schema converters
# ---------------------------------------------------------------------------

def _build_gemini_schema(prop: dict):
    """Recursively convert a neutral param dict to a types.Schema object."""
    from google.genai import types  # lazy — only needed when Gemini is active
    t = prop.get("type", "string").upper()
    kwargs: dict = {"type": t, "description": prop.get("description", "")}
    if t == "ARRAY" and "items" in prop:
        kwargs["items"] = _build_gemini_schema(prop["items"])
    if t == "OBJECT":
        kwargs["properties"] = {
            k: _build_gemini_schema(v)
            for k, v in prop.get("properties", {}).items()
        }
    return types.Schema(**kwargs)


def get_gemini_tool_schemas():
    """Return TOOLS as a list of types.Tool objects for the google-genai SDK."""
    from google.genai import types  # lazy — only needed when Gemini is active
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            k: _build_gemini_schema(v)
                            for k, v in t["parameters"].get("properties", {}).items()
                        },
                        required=t["parameters"].get("required", []),
                    ),
                )
                for t in TOOLS
            ]
        )
    ]


def get_claude_tool_schemas() -> list[dict]:
    """Return TOOLS in Anthropic tool format (parameters → input_schema)."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["parameters"],
        }
        for t in TOOLS
    ]
