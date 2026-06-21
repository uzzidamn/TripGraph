"""
Agent 3: Data Retriever — 2-pass KG ↔ API ↔ cache orchestrator.

Goal: cleanly separate "what's already in the KG" from "what we just enriched
from external APIs" so the planner can trace data provenance and the UI can
badge KG-vs-fresh.

Loop:
    Pass N (max 2):
      1. Read all candidate buckets from KG only (no API calls).
      2. Assess coverage (routes >= 1, hotels >= MIN_HOTELS, activities >= MIN_ACTIVITIES).
      3. If coverage is OK → return.
      4. Else, call the tools in their full mode (kg_only=False) for the
         deficient buckets. Those tools hit the external APIs (ORS / Geoapify),
         LLM-shaped data is merged back into the KG via IngestionQueries.
      5. Loop — pass 2 re-reads the now-enriched KG.

If still partial after 2 passes, fall back to seed_*.json so the planner
never gets an empty bucket.

Outputs onto state:
    route_candidates / hotel_candidates / activity_candidates / transport_candidates
    food_candidates / waypoint_candidates
    retrieval_passes       — how many full passes ran (0 if KG was complete on first try)
    retrieval_source       — { bucket: 'kg' | 'api+kg' | 'empty' }
"""
import json
from functools import lru_cache
from pathlib import Path

from backend.agents.state import TripState

_DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Coverage thresholds — below these the planner produces poor candidates.
MIN_HOTELS = 2
MIN_ACTIVITIES = 2
MAX_PASSES = 2


# ─── Seed loader (final fallback when even APIs fail) ────────────────────────
@lru_cache(maxsize=1)
def _load_seed_data() -> dict:
    def _read(filename):
        path = _DATA_DIR / filename
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    cities_list = _read("seed_cities.json")
    city_by_name = {c["name"]: c for c in cities_list}

    raw_routes = _read("seed_routes.json")
    routes = []
    for r in raw_routes:
        dest_city = city_by_name.get(r["destination"], {})
        routes.append({
            **r,
            "destination_type": dest_city.get("type", ""),
            "dest_lat": dest_city.get("lat", 0.0),
            "dest_lng": dest_city.get("lng", 0.0),
        })

    return {
        "routes": routes,
        "hotels": _read("seed_hotels.json"),
        "activities": _read("seed_activities.json"),
        "transport": _read("seed_transport.json"),
        "restaurants": _read("seed_restaurants.json"),
        "waypoints": _read("seed_waypoints.json"),
    }


def _seed_for_route(route_id: str, destination: str) -> dict:
    sd = _load_seed_data()
    return {
        "hotels": [h for h in sd["hotels"] if h.get("destination") == destination],
        "activities": [a for a in sd["activities"] if a.get("destination") == destination],
        "transport": [t for t in sd["transport"] if t.get("route_id") == route_id],
        "restaurants": [
            r for r in sd["restaurants"]
            if r.get("destination") == destination or r.get("route_id") == route_id
        ],
        "waypoints": [w for w in sd["waypoints"] if w.get("route_id") == route_id],
    }


# ─── Single KG snapshot (no API calls) ────────────────────────────────────────
def _fetch_from_kg(origin: str, destination: str | None, destination_type: str | None,
                   hotel_tier: str | None, must_include: list[str] | None) -> dict:
    """One pass of pure-KG reads across every bucket."""
    from backend.tools.route_tool import get_routes
    from backend.tools.hotel_tool import get_hotels
    from backend.tools.activity_tool import get_activities
    from backend.tools.transport_tool import get_transport_options
    from backend.tools.restaurant_tool import get_restaurants
    from backend.tools.waypoint_tool import get_waypoints

    routes = []
    try:
        routes = get_routes(origin, destination_type, destination, kg_only=True) or []
    except Exception as e:
        print(f"  ⚠️  KG route fetch failed: {e}")

    if destination:
        filt = [r for r in routes if r.get("destination") == destination]
        if filt:
            routes = filt
    if destination_type:
        filt = [r for r in routes if r.get("destination_type") == destination_type]
        if filt:
            routes = filt

    hotels, activities, transport, restaurants, waypoints = [], [], [], [], []

    for route in routes:
        rid = route.get("route_id", "")
        dest = route.get("destination", "")
        try:
            hotels.extend(get_hotels(dest, hotel_tier, kg_only=True) or [])
        except Exception as e:
            print(f"  ⚠️  KG hotel fetch failed for {dest}: {e}")
        try:
            activities.extend(get_activities(dest, must_include if must_include else None, kg_only=True) or [])
        except Exception as e:
            print(f"  ⚠️  KG activity fetch failed for {dest}: {e}")
        try:
            transport.extend(get_transport_options(rid) or [])
        except Exception as e:
            print(f"  ⚠️  KG transport fetch failed for {rid}: {e}")
        try:
            restaurants.extend(get_restaurants(dest, rid) or [])
        except Exception as e:
            print(f"  ⚠️  KG restaurant fetch failed for {dest}: {e}")
        try:
            waypoints.extend(get_waypoints(rid) or [])
        except Exception as e:
            print(f"  ⚠️  KG waypoint fetch failed for {rid}: {e}")

    # Stamp destination/route_id on rows that were missing it
    for h in hotels:
        h.setdefault("destination", h.get("destination"))
    for a in activities:
        a.setdefault("destination", a.get("destination"))

    return {
        "routes": routes,
        "hotels": hotels,
        "activities": activities,
        "transport": transport,
        "restaurants": restaurants,
        "waypoints": waypoints,
    }


# ─── Backfill from external APIs (writes through KG) ─────────────────────────
def _backfill_from_apis(origin: str, destination: str | None, destination_type: str | None,
                        hotel_tier: str | None, must_include: list[str] | None,
                        deficits: dict, snapshot: dict) -> None:
    """For each deficient bucket, call the corresponding tool in full mode
    (kg_only=False) so it hits the API and writes back to the KG.

    We DON'T use the returned values here — the next KG pass will read the
    cached rows, keeping the data provenance clean.
    """
    from backend.tools.route_tool import get_routes
    from backend.tools.hotel_tool import get_hotels
    from backend.tools.activity_tool import get_activities

    if deficits.get("routes"):
        try:
            print("  [Backfill] Routes deficient — triggering ORS enrichment")
            get_routes(origin, destination_type, destination, kg_only=False)
        except Exception as e:
            print(f"  ⚠️  Route backfill failed: {e}")

    # For hotels/activities we need to know which destinations are short.
    # Use the route candidates we have (or, if none, the explicit destination).
    targets = list({(r.get("destination") or "") for r in snapshot.get("routes", []) if r.get("destination")})
    if not targets and destination:
        targets = [destination]

    if deficits.get("hotels"):
        for dest in targets:
            try:
                print(f"  [Backfill] Hotels deficient at {dest} — triggering Geoapify enrichment")
                get_hotels(dest, hotel_tier, kg_only=False)
            except Exception as e:
                print(f"  ⚠️  Hotel backfill failed for {dest}: {e}")

    if deficits.get("activities"):
        for dest in targets:
            try:
                print(f"  [Backfill] Activities deficient at {dest} — triggering Geoapify enrichment")
                get_activities(dest, must_include if must_include else None, kg_only=False)
            except Exception as e:
                print(f"  ⚠️  Activity backfill failed for {dest}: {e}")


def _assess_coverage(snapshot: dict) -> dict:
    """Return a deficits dict marking which buckets need API backfill."""
    return {
        "routes":     len(snapshot["routes"]) == 0,
        "hotels":     len(snapshot["hotels"]) < MIN_HOTELS,
        "activities": len(snapshot["activities"]) < MIN_ACTIVITIES,
    }


def data_retriever_node(state: TripState) -> dict:
    """Drive the 2-pass loop and emit candidate lists + provenance telemetry."""
    constraints = state["extracted_constraints"]
    origin = constraints.get("origin") or "Gurugram"  # last-resort fallback only
    destination = constraints.get("destination")
    destination_type = constraints.get("destination_type")
    hotel_tier = constraints.get("hotel_tier")
    must_include = constraints.get("must_include") or []

    source_map: dict[str, str] = {}
    snapshot: dict = {"routes": [], "hotels": [], "activities": [], "transport": [], "restaurants": [], "waypoints": []}
    passes_run = 0

    for pass_num in range(1, MAX_PASSES + 1):
        passes_run = pass_num
        snapshot = _fetch_from_kg(origin, destination, destination_type, hotel_tier, must_include)
        deficits = _assess_coverage(snapshot)

        if not any(deficits.values()):
            print(f"  ✅ Pass {pass_num}: KG coverage sufficient")
            break

        if pass_num >= MAX_PASSES:
            print(f"  ⚠️  Pass {pass_num}: still deficient after backfill — using what we have + seed fallback")
            break

        print(f"  ⏳ Pass {pass_num}: deficits = {[k for k,v in deficits.items() if v]} — backfilling from APIs")
        _backfill_from_apis(origin, destination, destination_type, hotel_tier, must_include, deficits, snapshot)

    # Seed-file final fallback: never let a bucket be entirely empty
    seed = _load_seed_data()
    if not snapshot["routes"]:
        snapshot["routes"] = seed["routes"]
        source_map["routes"] = "seed"
    else:
        source_map["routes"] = "kg" if passes_run == 1 else "api+kg"

    for route in snapshot["routes"]:
        rid = route.get("route_id", "")
        dest = route.get("destination", "")
        sb = _seed_for_route(rid, dest)
        # Stamp ids where they came from KG
        for h in snapshot["hotels"]:
            h.setdefault("destination", dest if h.get("destination") in (None, "") else h.get("destination"))
        # if we still have nothing for a route's destination, fall back to that route's seed slice
        if not any(h.get("destination") == dest for h in snapshot["hotels"]):
            snapshot["hotels"].extend(sb["hotels"])
        if not any(a.get("destination") == dest for a in snapshot["activities"]):
            snapshot["activities"].extend(sb["activities"])
        if not any(t.get("route_id") == rid for t in snapshot["transport"]):
            snapshot["transport"].extend(sb["transport"])
        if not any(r.get("destination") == dest or r.get("route_id") == rid for r in snapshot["restaurants"]):
            snapshot["restaurants"].extend(sb["restaurants"])
        if not any(w.get("route_id") == rid for w in snapshot["waypoints"]):
            snapshot["waypoints"].extend(sb["waypoints"])

    for bucket, items in (
        ("hotels", snapshot["hotels"]),
        ("activities", snapshot["activities"]),
        ("transport", snapshot["transport"]),
        ("restaurants", snapshot["restaurants"]),
        ("waypoints", snapshot["waypoints"]),
    ):
        if bucket not in source_map:
            source_map[bucket] = "kg" if passes_run == 1 else "api+kg" if items else "empty"

    print(f"  ✅ Data retriever: passes={passes_run}, "
          f"routes={len(snapshot['routes'])}, hotels={len(snapshot['hotels'])}, "
          f"activities={len(snapshot['activities'])}, transport={len(snapshot['transport'])}, "
          f"restaurants={len(snapshot['restaurants'])}, waypoints={len(snapshot['waypoints'])}, "
          f"source={source_map}")

    return {
        "route_candidates": snapshot["routes"],
        "hotel_candidates": snapshot["hotels"],
        "activity_candidates": snapshot["activities"],
        "transport_candidates": snapshot["transport"],
        "food_candidates": snapshot["restaurants"],
        "waypoint_candidates": snapshot["waypoints"],
        "retrieval_passes": passes_run,
        "retrieval_source": source_map,
    }
