"""
Tool: get_hotels — returns hotels matching destination and optional tier.
"""
from backend.knowledge_graph.connection import execute_query
from backend.knowledge_graph.queries import TravelQueries


def get_hotels(destination: str, tier: str | None = None) -> list[dict]:
    """
    Returns hotels at a destination, optionally filtered by comfort tier.
    """
    cypher, params = TravelQueries.find_hotels(destination, tier)
    results = execute_query(cypher, params)
    return [r["hotel"] for r in results]
