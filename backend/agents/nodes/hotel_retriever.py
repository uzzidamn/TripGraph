"""Agent 4a — Hotel Retriever (parallel domain sub-node)."""
from backend.agents.state import TripState
from backend.agents.nodes.data_retriever import _fetch_domain_hotels


def hotel_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    constraints = state.get("extracted_constraints") or {}
    hotel_tier = constraints.get("hotel_tier")
    try:
        hotels = _fetch_domain_hotels(routes, hotel_tier)
    except Exception as e:
        print(f"  ⚠️  Hotel retriever failed: {e}")
        hotels = []
    print(f"  ✅ Hotel retriever: {len(hotels)} candidates")
    return {"hotel_candidates": hotels}
