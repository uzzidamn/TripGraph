"""Agent 4c — Activity Retriever (parallel domain sub-node)."""
from backend.agents.state import TripState
from backend.agents.nodes.data_retriever import _fetch_domain_activities


def activity_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    constraints = state.get("extracted_constraints") or {}
    must_include = constraints.get("must_include") or []
    try:
        activities = _fetch_domain_activities(routes, must_include)
    except Exception as e:
        print(f"  ⚠️  Activity retriever failed: {e}")
        activities = []
    print(f"  ✅ Activity retriever: {len(activities)} candidates")
    return {"activity_candidates": activities}
