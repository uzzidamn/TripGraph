"""
Tool: get_transport_options — returns transport options for a route.
"""
from backend.knowledge_graph.connection import execute_query
from backend.knowledge_graph.queries import TravelQueries


def get_transport_options(route_id: str, modes: list[str] | None = None) -> list[dict]:
    """
    Returns transport options for a route, optionally filtered by mode.
    """
    cypher, params = TravelQueries.find_transport(route_id, modes)
    results = execute_query(cypher, params)
    return [r["transport"] for r in results]
