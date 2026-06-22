"""LangGraph node 4b: fetch transport candidates for all routes."""
from backend.agents.nodes.data_retriever import retrieve_transport
from backend.agents.state import TripState


def transport_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    constraints = state.get("extracted_constraints") or {}
    transport: list[dict] = []
    for route in routes:
        rid = route.get("route_id", "")
        transport.extend(retrieve_transport(rid, constraints))
    return {"transport_candidates": transport}
