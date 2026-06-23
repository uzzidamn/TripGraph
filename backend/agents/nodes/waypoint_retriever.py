"""Agent 4e — Waypoint Retriever (parallel domain sub-node)."""
from backend.agents.state import TripState
from backend.agents.nodes.data_retriever import _fetch_domain_waypoints


def waypoint_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    try:
        waypoints = _fetch_domain_waypoints(routes)
    except Exception as e:
        print(f"  ⚠️  Waypoint retriever failed: {e}")
        waypoints = []
    print(f"  ✅ Waypoint retriever: {len(waypoints)} candidates")
    return {"waypoint_candidates": waypoints}
