"""Agent 4d — Food Retriever (parallel domain sub-node)."""
from backend.agents.state import TripState
from backend.agents.nodes.data_retriever import _fetch_domain_restaurants


def food_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    try:
        food = _fetch_domain_restaurants(routes)
    except Exception as e:
        print(f"  ⚠️  Food retriever failed: {e}")
        food = []
    print(f"  ✅ Food retriever: {len(food)} candidates")
    return {"food_candidates": food}
