"""Photo Enricher — for each timeline event with lat/lng but no Google
photo, query Google Places to fetch a photo_name + editorial_summary.

The new KG seed data (566 activities) doesn't carry Google's photo_name
(that's an API-only field). This pass fills it in so the popover can
actually render photos.

Runs AFTER architect, BEFORE review. Caches aggressively in a JSON file
so the same place isn't re-queried across trips.
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from backend.agents.state import TripState
from backend.api_clients.google_places_client import GooglePlacesClient, GOOGLE_MAPS_API_KEY

_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "places_photo_cache.json"

# Cap fresh Google lookups per plan and run them concurrently. Previously these
# ran one-by-one (25+ sequential network round-trips → 25-40s). Cache hits are
# still applied for every event; only NEW lookups are capped.
_MAX_LIVE_LOOKUPS = int(os.getenv("PHOTO_MAX_LOOKUPS", "12"))
_MAX_WORKERS = int(os.getenv("PHOTO_MAX_WORKERS", "8"))


def _lookup_place(name: str, destination: str, lat: float, lng: float):
    """Single Google Places text search — runs in a worker thread (network I/O)."""
    try:
        results = GooglePlacesClient._search(
            f"{name} {destination}".strip(), lat=lat, lng=lng, radius_m=3000, limit=1,
        )
        return results[0] if results else None
    except Exception as e:
        print(f"  ⚠️  Photo lookup failed for {name}: {e}")
        return "__error__"


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
        _CACHE_PATH.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        print(f"  ⚠️  Failed to write photo cache: {e}")


def _cache_key(name: str, lat: float, lng: float) -> str:
    """Stable key — name + 3-decimal lat/lng so same-named places at same spot match."""
    return f"{(name or '').lower().strip()}@{round(lat, 3)},{round(lng, 3)}"


def photo_enricher_node(state: TripState) -> dict:
    if not GOOGLE_MAPS_API_KEY:
        return {}

    timeline = state.get("timeline") or []
    selected = state.get("selected_itinerary") or {}
    destination = (selected.get("route") or {}).get("destination") or ""

    if not timeline:
        return {}

    cache = _load_cache()
    enriched_count = 0

    def _apply(ev: dict, data: dict) -> None:
        """Copy photo/editorial/rating from a cache or lookup result onto an event."""
        if data.get("photo_name"):
            ev["photo_name"] = data["photo_name"]
        if data.get("editorial_summary") and not ev.get("editorial_summary"):
            ev["editorial_summary"] = data["editorial_summary"]
        if data.get("rating") and not ev.get("rating"):
            ev["rating"] = data["rating"]

    # Pass 1 (free): apply cache hits inline, collect cache-miss events to look up.
    pending = []  # list of (ev, key, name, lat, lng)
    for ev in timeline:
        if ev.get("photo_name"):
            continue
        lat, lng, name = ev.get("lat"), ev.get("lng"), ev.get("title") or ""
        if not (lat and lng and name):
            continue
        # Skip generic meal/rest events that won't yield useful photos
        etype = (ev.get("type") or "").lower()
        if etype in ("rest", "meal") and not any(k in name.lower() for k in ("restaurant", "cafe", "dhaba", "kitchen")):
            continue

        key = _cache_key(name, lat, lng)
        if key in cache:
            _apply(ev, cache[key])
            if cache[key].get("photo_name"):
                enriched_count += 1
            continue
        pending.append((ev, key, name, lat, lng))

    # Pass 2 (parallel + capped): only the first N cache misses, fired concurrently.
    pending = pending[:_MAX_LIVE_LOOKUPS]
    new_lookups = 0
    if pending:
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
            futures = {
                pool.submit(_lookup_place, name, destination, lat, lng): (ev, key)
                for (ev, key, name, lat, lng) in pending
            }
            for fut in as_completed(futures):
                ev, key = futures[fut]
                best = fut.result()
                if best == "__error__":
                    continue
                new_lookups += 1
                if not best:
                    cache[key] = {"photo_name": None}  # negative cache
                    continue
                data = {
                    "photo_name": best.get("photo_name"),
                    "editorial_summary": best.get("editorial_summary"),
                    "rating": best.get("rating"),
                }
                cache[key] = data
                _apply(ev, data)
                if data["photo_name"]:
                    enriched_count += 1

    if new_lookups:
        _save_cache(cache)

    print(f"  📸 Photo enricher: {enriched_count}/{len(timeline)} events have photos "
          f"({new_lookups} live Google Places lookups, rest cached)")

    return {"timeline": timeline}
