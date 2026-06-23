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


# ─── Domain helper functions used by parallel sub-nodes ──────────────────────

def _fetch_domain_hotels(routes: list, hotel_tier: str | None) -> list:
    from backend.tools.hotel_tool import get_hotels
    hotels = []
    for route in routes:
        dest = route.get("destination", "")
        try:
            hotels.extend(get_hotels(dest, hotel_tier, kg_only=True) or [])
        except Exception:
            sd = _seed_for_route(route.get("route_id", ""), dest)
            hotels.extend(sd["hotels"])
    return hotels


def _fetch_domain_transport(routes: list) -> list:
    from backend.tools.transport_tool import get_transport_options
    transport = []
    for route in routes:
        rid = route.get("route_id", "")
        try:
            transport.extend(get_transport_options(rid) or [])
        except Exception:
            sd = _seed_for_route(rid, route.get("destination", ""))
            transport.extend(sd["transport"])
    return transport


def _fetch_domain_activities(routes: list, must_include: list) -> list:
    from backend.tools.activity_tool import get_activities
    activities = []
    for route in routes:
        dest = route.get("destination", "")
        try:
            activities.extend(get_activities(dest, must_include or None, kg_only=True) or [])
        except Exception:
            sd = _seed_for_route(route.get("route_id", ""), dest)
            activities.extend(sd["activities"])
    return activities


def _fetch_domain_restaurants(routes: list) -> list:
    from backend.tools.restaurant_tool import get_restaurants
    restaurants = []
    for route in routes:
        dest = route.get("destination", "")
        rid = route.get("route_id", "")
        try:
            restaurants.extend(get_restaurants(dest, rid) or [])
        except Exception:
            sd = _seed_for_route(rid, dest)
            restaurants.extend(sd["restaurants"])
    return restaurants


def _fetch_domain_waypoints(routes: list) -> list:
    from backend.tools.waypoint_tool import get_waypoints
    waypoints = []
    for route in routes:
        rid = route.get("route_id", "")
        try:
            waypoints.extend(get_waypoints(rid) or [])
        except Exception:
            sd = _seed_for_route(rid, route.get("destination", ""))
            waypoints.extend(sd["waypoints"])
    return waypoints


@lru_cache(maxsize=1)
def _get_seed_catalog() -> dict:
    """Return seed catalog: {origin: set(destinations)} — ground truth for what's supported."""
    seed = _load_seed_data()["routes"]
    catalog: dict[str, set] = {}
    for r in seed:
        o = (r.get("origin") or "").strip().lower()
        d = (r.get("destination") or "").strip().lower()
        if o:
            catalog.setdefault(o, set()).add(d)
    return catalog


def _get_all_catalog_routes() -> list:
    """Return every route in the catalog (for unsupported-route suggestions)."""
    try:
        from backend.tools.route_tool import get_routes
        return get_routes(None, None, None, kg_only=True) or []
    except Exception:
        return _load_seed_data()["routes"]


def _is_supported_route(origin: str, destination: str | None) -> bool:
    """Check origin (and optionally destination) against the seed catalog only.

    This uses the seed files as the authoritative list of supported routes,
    so dynamically-created routes in local_kg_store.json or Neo4j do NOT
    widen the support boundary.
    """
    catalog = _get_seed_catalog()
    o_key = (origin or "").strip().lower()
    if o_key not in catalog:
        return False
    if destination:
        d_key = destination.strip().lower()
        return d_key in catalog[o_key]
    return True  # origin is supported, any destination is fine


def _closest_alternatives(origin: str, destination: str | None, seed_routes: list) -> list:
    """Return up to 4 closest alternative routes.

    Priority:
    1. If origin is invalid → find routes from supported origins to the requested
       destination (or any destination if destination is also invalid).
    2. If origin is valid but destination is invalid → find other destinations from
       that origin.
    3. Sort suggestions so that routes whose destination / origin share the most
       characters with the requested city come first (simple prefix/substring match).
    """
    def _similarity(a: str, b: str) -> int:
        a, b = a.lower(), b.lower()
        score = 0
        if a == b:
            return 100
        if a in b or b in a:
            score += 60
        # common prefix length
        for i, (ca, cb) in enumerate(zip(a, b)):
            if ca == cb:
                score += 1
            else:
                break
        return score

    catalog = _get_seed_catalog()
    valid_origins = set(catalog.keys())
    o_key = (origin or "").strip().lower()
    d_key = (destination or "").strip().lower()
    origin_valid = o_key in valid_origins

    if origin_valid:
        # Origin exists but destination doesn't — suggest other destinations from same origin
        candidates = [r for r in seed_routes if r.get("origin", "").lower() == o_key]
        candidates.sort(key=lambda r: -_similarity(r.get("destination", ""), destination or ""))
    else:
        # Origin doesn't exist — suggest routes to the requested destination from any origin
        if d_key:
            candidates = [r for r in seed_routes if r.get("destination", "").lower() == d_key]
        else:
            candidates = seed_routes[:]
        # Also suggest routes from the most "similar" valid origin
        if not candidates:
            closest_origin = max(valid_origins, key=lambda o: _similarity(o, origin), default=None)
            if closest_origin:
                candidates = [r for r in seed_routes if r.get("origin", "").lower() == closest_origin]

    # Deduplicate by (origin, destination) and cap at 4
    seen, result = set(), []
    for r in candidates:
        key = (r.get("origin", ""), r.get("destination", ""))
        if key not in seen:
            seen.add(key)
            result.append(r)
        if len(result) >= 4:
            break
    return result


def _unsupported_route_response(origin: str, destination: str | None, all_catalog: list) -> dict:
    reason = (
        f"No routes from '{origin}' to '{destination}'" if destination
        else f"No routes from '{origin}' in our catalog"
    )
    seed_routes = _load_seed_data()["routes"]
    suggestions = _closest_alternatives(origin, destination, seed_routes)
    return {
        "route_candidates": [],
        "all_route_candidates": [],
        "unsupported_route": {
            "origin": origin,
            "destination": destination,
            "reason": reason,
        },
        "suggested_routes": suggestions,
    }


def route_retriever_node(state: TripState) -> dict:
    """Agent 4.0 — Route Retriever with dedup filter and unsupported-route detection."""
    constraints = state.get("extracted_constraints") or {}
    origin = constraints.get("origin") or "Gurugram"
    destination = constraints.get("destination")
    destination_type = constraints.get("destination_type")
    visited = state.get("visited_destinations") or []
    memory_context = dict(state.get("memory_context") or {})
    dedup_override = memory_context.get("dedup_override", False)

    from backend.tools.route_tool import get_routes
    all_catalog = _get_all_catalog_routes()

    # Seed-catalog gate: authoritative check before any KG or local-store query.
    # This prevents dynamically-created routes (from ORS backfill) from widening
    # the supported-route boundary beyond what's in seed_routes.json.
    if not _is_supported_route(origin, destination):
        reason = (
            f"No routes from '{origin}' to '{destination}'" if destination
            else f"No routes from '{origin}' in our catalog"
        )
        print(f"  ⛔ Route retriever: {reason} (seed-catalog check)")
        return _unsupported_route_response(origin, destination, all_catalog)

    try:
        all_routes = get_routes(origin, destination_type, destination, kg_only=True) or []
    except Exception:
        all_routes = _load_seed_data()["routes"]

    if not all_routes:
        print(f"  ⛔ Route retriever: no routes from '{origin}'")
        return _unsupported_route_response(origin, destination, all_catalog)

    if destination:
        dest_routes = [r for r in all_routes if r.get("destination", "").lower() == destination.lower()]
        if not dest_routes:
            print(f"  ⛔ Route retriever: '{destination}' not reachable from '{origin}'")
            return _unsupported_route_response(origin, destination, all_catalog)
        all_routes = dest_routes
    elif destination_type:
        filt = [r for r in all_routes if r.get("destination_type") == destination_type]
        if filt:
            all_routes = filt

    # Dedup filter
    if not dedup_override and visited:
        filtered = [r for r in all_routes if r.get("destination") not in visited]
    else:
        filtered = list(all_routes)

    print(f"  ✅ Route retriever: {len(filtered)} filtered routes, {len(all_routes)} total")
    return {
        "route_candidates": filtered,
        "all_route_candidates": all_routes,
        "unsupported_route": None,
        "suggested_routes": [],
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
