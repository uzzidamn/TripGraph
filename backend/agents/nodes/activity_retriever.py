"""LangGraph node 4c: fetch activity candidates for all route destinations."""
from backend.agents.nodes.data_retriever import retrieve_activities
from backend.agents.state import TripState


def activity_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    constraints = state.get("extracted_constraints") or {}
    activities: list[dict] = []
    for route in routes:
        dest = str(route.get("destination", "")).strip().title()
        activities.extend(retrieve_activities(dest, constraints))
    return {"activity_candidates": activities}
