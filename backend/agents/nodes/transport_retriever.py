"""Agent 4b — Transport Retriever (parallel domain sub-node)."""
from backend.agents.state import TripState
from backend.agents.nodes.data_retriever import _fetch_domain_transport


def transport_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    try:
        transport = _fetch_domain_transport(routes)
    except Exception as e:
        print(f"  ⚠️  Transport retriever failed: {e}")
        transport = []
    print(f"  ✅ Transport retriever: {len(transport)} candidates")
    return {"transport_candidates": transport}
