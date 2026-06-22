"""Photo Enricher — for each timeline event with lat/lng but no Google
photo, query Google Places to fetch a photo_name + editorial_summary.

The new KG seed data (566 activities) doesn't carry Google's photo_name
(that's an API-only field). This pass fills it in so the popover can
actually render photos.

Runs AFTER architect, BEFORE review. Caches aggressively in a JSON file
so the same place isn't re-queried across trips.
"""
import json
from pathlib import Path

from backend.agents.state import TripState
from backend.api_clients.google_places_client import GooglePlacesClient, GOOGLE_MAPS_API_KEY

_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "places_photo_cache.json"


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
    new_lookups = 0

    for ev in timeline:
        if ev.get("photo_name"):
            continue
        lat = ev.get("lat")
        lng = ev.get("lng")
        name = ev.get("title") or ""
        if not (lat and lng and name):
            continue
        # Skip generic meal/rest events that won't yield useful photos
        etype = (ev.get("type") or "").lower()
        if etype in ("rest", "meal") and not any(k in name.lower() for k in ("restaurant", "cafe", "dhaba", "kitchen")):
            continue

        key = _cache_key(name, lat, lng)
        if key in cache:
            cached = cache[key]
            if cached.get("photo_name"):
                ev["photo_name"] = cached["photo_name"]
            if cached.get("editorial_summary") and not ev.get("editorial_summary"):
                ev["editorial_summary"] = cached["editorial_summary"]
            if cached.get("rating") and not ev.get("rating"):
                ev["rating"] = cached["rating"]
            enriched_count += 1
            continue

        # Live lookup via Google Places Text Search biased to the event's coords
        try:
            results = GooglePlacesClient._search(
                f"{name} {destination}".strip(),
                lat=lat, lng=lng,
                radius_m=3000, limit=1,
            )
        except Exception as e:
            print(f"  ⚠️  Photo lookup failed for {name}: {e}")
            continue

        new_lookups += 1
        if not results:
            cache[key] = {"photo_name": None}  # negative cache
            continue

        best = results[0]
        photo_name = best.get("photo_name")
        editorial = best.get("editorial_summary")
        rating = best.get("rating")
        cache[key] = {
            "photo_name": photo_name,
            "editorial_summary": editorial,
            "rating": rating,
        }
        if photo_name:
            ev["photo_name"] = photo_name
            enriched_count += 1
        if editorial and not ev.get("editorial_summary"):
            ev["editorial_summary"] = editorial
        if rating and not ev.get("rating"):
            ev["rating"] = rating

    if new_lookups:
        _save_cache(cache)

    print(f"  📸 Photo enricher: {enriched_count}/{len(timeline)} events have photos "
          f"({new_lookups} live Google Places lookups, rest cached)")

    return {"timeline": timeline}
