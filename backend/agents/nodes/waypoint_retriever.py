"""LangGraph node 4e: fetch waypoint candidates for all routes."""
from backend.agents.nodes.data_retriever import retrieve_waypoints
from backend.agents.state import TripState


def waypoint_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    constraints = state.get("extracted_constraints") or {}
    waypoints: list[dict] = []
    for route in routes:
        rid = route.get("route_id", "")
        waypoints.extend(retrieve_waypoints(rid, constraints))
    return {"waypoint_candidates": waypoints}
