"""Segment Router — for each consecutive pair of stops in a day, compute
the real road-following polyline via ORS so the map can draw actual
directions instead of straight lines.

Only road segments (cab / drive / car / bus) get polylines. Flight and
train segments stay as straight dashed lines on the map.

Output → state['segment_polylines']:
[
  {"day": 1, "from_seq": 1, "to_seq": 2, "mode": "cab",
   "polyline": [[lat,lng], ...], "distance_km": 12.3, "duration_min": 25}
]
"""
import json
from pathlib import Path

from backend.agents.state import TripState
from backend.api_clients.ors_client import ORSClient, ORS_API_KEY

_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "segment_polyline_cache.json"
_MAX_ROAD_KM = 250  # don't try to road-route segments longer than this — likely a flight


def _load_cache() -> dict:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(json.dumps(cache))
    except Exception:
        pass


def _key(lat1, lng1, lat2, lng2):
    return f"{round(lat1,4)},{round(lng1,4)}-{round(lat2,4)},{round(lng2,4)}"


def _haversine_km(lat1, lng1, lat2, lng2):
    import math
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def segment_router_node(state: TripState) -> dict:
    if not ORS_API_KEY:
        return {}

    map_points = state.get("map_points") or []
    if not map_points:
        return {}

    # Group event points (those with day + seq) by day
    by_day = {}
    for p in map_points:
        if p.get("seq") is None or p.get("day") is None:
            continue
        if not (p.get("lat") and p.get("lng")):
            continue
        by_day.setdefault(p["day"], []).append(p)

    cache = _load_cache()
    new_fetches = 0
    MAX_FRESH_ORS_CALLS = 4  # cap per-request to avoid blocking the response
    segments = []

    for day, pts in by_day.items():
        pts = sorted(pts, key=lambda x: x.get("seq", 0))
        for i in range(len(pts) - 1):
            p1, p2 = pts[i], pts[i + 1]
            mode = (p2.get("mode") or "").lower()
            if mode in ("flight", "air", "train", "rail"):
                continue  # straight line for these

            dist = _haversine_km(p1["lat"], p1["lng"], p2["lat"], p2["lng"])
            if dist < 0.3 or dist > _MAX_ROAD_KM:
                continue

            ck = _key(p1["lat"], p1["lng"], p2["lat"], p2["lng"])
            if ck in cache:
                cached = cache[ck]
                if cached.get("polyline"):
                    segments.append({
                        "day": day,
                        "from_seq": p1.get("seq"),
                        "to_seq": p2.get("seq"),
                        "mode": mode or "cab",
                        "polyline": cached["polyline"],
                        "distance_km": cached.get("distance_km"),
                        "duration_min": cached.get("duration_min"),
                    })
                continue

            if new_fetches >= MAX_FRESH_ORS_CALLS:
                continue  # defer remaining segments to next request (will be cached then)

            try:
                route = ORSClient.get_route(p1["lng"], p1["lat"], p2["lng"], p2["lat"])
            except Exception:
                route = None

            new_fetches += 1
            if not route or not route.get("polyline"):
                cache[ck] = {"polyline": None}
                continue

            duration_min = int(round(route.get("duration_hours", 0) * 60))
            cache[ck] = {
                "polyline": route["polyline"],
                "distance_km": route.get("distance_km"),
                "duration_min": duration_min,
            }
            segments.append({
                "day": day,
                "from_seq": p1.get("seq"),
                "to_seq": p2.get("seq"),
                "mode": mode or "cab",
                "polyline": route["polyline"],
                "distance_km": route.get("distance_km"),
                "duration_min": duration_min,
            })

    if new_fetches:
        _save_cache(cache)

    print(f"  🛣️  Segment router: {len(segments)} road polylines drawn "
          f"({new_fetches} fresh ORS calls)")

    return {"segment_polylines": segments}
