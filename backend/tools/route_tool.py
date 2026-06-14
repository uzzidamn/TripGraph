"""
Tool: get_routes — returns matching routes from the knowledge graph.
"""
from backend.knowledge_graph.connection import execute_query
from backend.knowledge_graph.queries import TravelQueries


def get_routes(origin: str, destination_type: str | None = None) -> list[dict]:
    """
    Returns route options matching origin and optional destination type.
    Called by: Data Retriever Agent (Task 2)
    """
    cypher, params = TravelQueries.find_routes(origin, destination_type)
    results = execute_query(cypher, params)
    return [r["route"] for r in results]
