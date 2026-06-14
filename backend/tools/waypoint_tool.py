"""
Tool: get_waypoints — returns checkpoints/stops for a route in order.
"""
from backend.knowledge_graph.connection import execute_query
from backend.knowledge_graph.queries import TravelQueries


def get_waypoints(route_id: str) -> list[dict]:
    """
    Returns waypoints along a route, ordered by sequencing fields.
    """
    cypher, params = TravelQueries.find_waypoints(route_id)
    results = execute_query(cypher, params)
    return [r["waypoint"] for r in results]
