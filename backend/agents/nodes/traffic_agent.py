"""Traffic agent — annotates the timeline's driving legs with current or
historically-typical congestion intelligence.

Silent until a traffic provider key is configured
(see backend/api_clients/traffic_client.py).
"""
from backend.api_clients.traffic_client import TrafficClient
from backend.agents.state import TripState


def traffic_agent_node(state: TripState) -> dict:
    """Annotate each driving leg in the timeline with traffic data when available.

    Returns {'traffic': {<route_id_or_leg_index>: APIResult, ...}}.
    Silent stub returns one unavailable entry so the UI can show a "—" placeholder.
    """
    routes = state.get("route_candidates") or []
    if not routes:
        return {"traffic": {"_default": {"available": False, "reason": "NO_ROUTES", "provider": "none", "data": None}}}

    out: dict = {}
    for r in routes:
        rid = r.get("route_id") or "unknown"
        orig_lat = r.get("origin_lat") or 28.4595   # Gurugram default
        orig_lng = r.get("origin_lng") or 77.0266
        dest_lat = r.get("dest_lat")
        dest_lng = r.get("dest_lng")
        if dest_lat is None or dest_lng is None:
            continue
        out[rid] = TrafficClient.conditions(
            origin_lat=orig_lat, origin_lng=orig_lng,
            dest_lat=dest_lat, dest_lng=dest_lng,
        )
    return {"traffic": out}
