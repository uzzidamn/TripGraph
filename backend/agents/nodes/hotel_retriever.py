"""LangGraph node 4a: fetch hotel candidates for all route destinations."""
from backend.agents.nodes.data_retriever import retrieve_hotels
from backend.agents.state import TripState


def hotel_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    constraints = state.get("extracted_constraints") or {}
    hotels: list[dict] = []
    for route in routes:
        dest = str(route.get("destination", "")).strip().title()
        hotels.extend(retrieve_hotels(dest, constraints))
    return {"hotel_candidates": hotels}
