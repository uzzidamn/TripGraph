"""
Tool: get_restaurants — returns restaurants matching destination and optional route.
"""
from backend.knowledge_graph.connection import execute_query
from backend.knowledge_graph.queries import TravelQueries


def get_restaurants(destination: str, route_id: str | None = None) -> list[dict]:
    """
    Returns restaurant options. If route_id is provided, includes transit eating stops.
    """
    cypher, params = TravelQueries.find_restaurants(destination, route_id)
    results = execute_query(cypher, params)
    return [r["restaurant"] for r in results]
