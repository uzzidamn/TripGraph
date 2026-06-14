"""
Tool: get_activities — returns activities matching destination and optional tags.
"""
from backend.knowledge_graph.connection import execute_query
from backend.knowledge_graph.queries import TravelQueries


def get_activities(destination: str, tags: list[str] | None = None) -> list[dict]:
    """
    Returns activities at a destination, optionally filtered by preference tags.
    """
    cypher, params = TravelQueries.find_activities(destination, tags)
    results = execute_query(cypher, params)
    return [r["activity"] for r in results]
