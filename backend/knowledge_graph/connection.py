"""
Neo4j connection manager. Singleton driver for the application.

Automatic fallback to a local JSON knowledge graph store (backend/data/local_kg_store.json)
when Neo4j is offline. The fallback is *not permanent*: after `NEO4J_RETRY_COOLDOWN_S`
seconds, the next call retries Neo4j. The moment Neo4j comes back online (e.g. user
starts the Docker container mid-session), it is picked up transparently.

The local store is also *additive over seeds*: seed_*.json entries that don't yet
exist in the local store are merged in on every load. So adding a new row to a seed
file propagates without needing to delete the local store.
"""
import os
import json
import time
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

_driver = None

# Fallback state — when Neo4j fails, we set this to a wall-clock timestamp.
# Subsequent calls within NEO4J_RETRY_COOLDOWN_S use the JSON store; after that
# we retry Neo4j once. If it fails again, the cooldown resets.
_NEO4J_LAST_FAIL_TS: float = 0.0
NEO4J_RETRY_COOLDOWN_S = float(os.getenv("NEO4J_RETRY_COOLDOWN_S", "60"))

_DATA_DIR = Path(__file__).parent.parent / "data"
_LOCAL_STORE_PATH = _DATA_DIR / "local_kg_store.json"

# Seed mapping shared by load + rebuild helpers
_SEED_FILES = {
    "cities": ("seed_cities.json", "name"),
    "routes": ("seed_routes.json", "route_id"),
    "hotels": ("seed_hotels.json", "hotel_id"),
    "activities": ("seed_activities.json", "activity_id"),
    "restaurants": ("seed_restaurants.json", "restaurant_id"),
    "transport": ("seed_transport.json", "transport_id"),
    "waypoints": ("seed_waypoints.json", "waypoint_id"),
}


def get_driver():
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "tripgraph123")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver


def close_driver():
    global _driver
    if _driver:
        try:
            _driver.close()
        except Exception:
            pass
        _driver = None


def _should_attempt_neo4j() -> bool:
    """True if cooldown has passed (or never failed). Always try first call."""
    if _NEO4J_LAST_FAIL_TS == 0.0:
        return True
    return (time.time() - _NEO4J_LAST_FAIL_TS) >= NEO4J_RETRY_COOLDOWN_S


def _mark_neo4j_failed():
    global _NEO4J_LAST_FAIL_TS, _driver
    _NEO4J_LAST_FAIL_TS = time.time()
    # Force driver re-init on next attempt — the existing driver may have stale state.
    if _driver is not None:
        try:
            _driver.close()
        except Exception:
            pass
        _driver = None


def _mark_neo4j_ok():
    global _NEO4J_LAST_FAIL_TS
    if _NEO4J_LAST_FAIL_TS != 0.0:
        print("  ✅ Neo4j is reachable again — switching back from local JSON fallback")
    _NEO4J_LAST_FAIL_TS = 0.0


def _read_seed(filename: str) -> list[dict]:
    path = _DATA_DIR / filename
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️  Failed to read seed file {filename}: {e}")
        return []


def _merge_seeds_into(store: dict) -> dict:
    """For each entity bucket, append any seed rows whose id is missing from the local store.

    This is additive: API-cached rows are preserved, and newly-added seed rows
    propagate without manual deletion of the local store.
    """
    for key, (filename, id_field) in _SEED_FILES.items():
        existing_ids = {
            (item.get(id_field) or "").lower()
            for item in store.get(key, [])
            if item.get(id_field)
        }
        for seed_item in _read_seed(filename):
            sid = (seed_item.get(id_field) or "").lower()
            if sid and sid not in existing_ids:
                store.setdefault(key, []).append(seed_item)
                existing_ids.add(sid)
    return store


def _empty_store() -> dict:
    return {k: [] for k in _SEED_FILES.keys()}


def _load_local_store() -> dict:
    """Load store from disk if present, else build from seeds. Always merges in
    any seed entries missing from the on-disk store before returning."""
    if _LOCAL_STORE_PATH.exists():
        try:
            with open(_LOCAL_STORE_PATH, "r", encoding="utf-8") as f:
                store = json.load(f)
        except Exception:
            store = _empty_store()
    else:
        store = _empty_store()

    store = _merge_seeds_into(store)
    _save_local_store(store)
    return store


def _save_local_store(store: dict):
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(_LOCAL_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, default=str)
    except Exception as e:
        print(f"  ⚠️  Failed to write local KG store: {e}")


def rebuild_local_store_from_seeds() -> dict:
    """Discard the current local store and rebuild it purely from seed files.

    Use this from the CLI when you want a clean slate (e.g. after API hallucinations
    polluted the cache). Re-runnable, idempotent.
    """
    store = _merge_seeds_into(_empty_store())
    _save_local_store(store)
    print(f"  ✅ Rebuilt local KG store from seeds at {_LOCAL_STORE_PATH}")
    return store


# ─── Local-store query/write implementations ──────────────────────────────────
def _execute_query_local(cypher: str, parameters: dict = None) -> list[dict]:
    """Mock Cypher queries against local JSON store."""
    params = parameters or {}
    store = _load_local_store()

    # 1. find_routes
    if "ORIGIN_OF" in cypher:
        origin_name = params.get("origin") or ""
        dest_type = params.get("dest_type") or ""

        results = []
        for r in store["routes"]:
            r_origin = r.get("origin") or ""
            if r_origin.lower() == origin_name.lower():
                r_dest = r.get("destination") or ""
                dest_city = next((c for c in store["cities"] if (c.get("name") or "").lower() == r_dest.lower()), None)
                dest_t = (dest_city.get("type") or "") if dest_city else (r.get("destination_type") or "")
                dest_lat = (dest_city.get("lat") or 0.0) if dest_city else (r.get("dest_lat") or 0.0)
                dest_lng = (dest_city.get("lng") or 0.0) if dest_city else (r.get("dest_lng") or 0.0)

                if dest_type and dest_t.lower() != dest_type.lower():
                    continue

                results.append({
                    "route": {
                        **r,
                        "origin": origin_name,
                        "destination": r.get("destination"),
                        "destination_type": dest_t,
                        "dest_lat": dest_lat,
                        "dest_lng": dest_lng
                    }
                })
        return results

    # 2. find_hotels
    elif "HAS_HOTEL" in cypher:
        destination = params.get("destination") or ""
        tier = params.get("tier") or ""

        results = []
        for h in store["hotels"]:
            h_dest = h.get("destination") or ""
            h_tier = h.get("tier") or ""
            if h_dest.lower() == destination.lower():
                if tier and h_tier.lower() != tier.lower():
                    continue
                results.append({"hotel": h})
        results.sort(key=lambda x: x["hotel"].get("price_per_night", 999999))
        return results

    # 3. find_activities
    elif "HAS_ACTIVITY" in cypher:
        destination = params.get("destination") or ""
        tags = params.get("tags") or []
        tags_lower = [str(t).lower() for t in tags if t]

        results = []
        for a in store["activities"]:
            a_dest = a.get("destination") or ""
            if a_dest.lower() == destination.lower():
                if tags:
                    act_tags = [str(t).lower() for t in (a.get("tags") or []) if t]
                    name = (a.get("name") or "").lower()
                    matched = any(t in act_tags for t in tags_lower) or any(t in name for t in tags_lower)
                    if not matched:
                        continue
                results.append({"activity": a})
        return results

    # 4. find_transport
    elif "HAS_TRANSPORT" in cypher:
        route_id = params.get("route_id") or ""
        modes = params.get("modes") or []
        modes_lower = [str(m).lower() for m in modes if m]

        results = []
        for t in store["transport"]:
            t_route = t.get("route_id") or ""
            t_mode = t.get("mode") or ""
            if t_route.lower() == route_id.lower():
                if modes and t_mode.lower() not in modes_lower:
                    continue
                results.append({"transport": t})
        results.sort(key=lambda x: x["transport"].get("cost_total", 999999))
        return results

    # 5. find_restaurants
    elif "HAS_RESTAURANT" in cypher:
        destination = params.get("destination") or ""
        route_id = params.get("route_id") or ""

        results = []
        for r in store["restaurants"]:
            r_dest = r.get("destination") or ""
            r_route = r.get("route_id") or ""

            is_dest = destination and r_dest.lower() == destination.lower()
            is_route = route_id and r_route.lower() == route_id.lower()
            if is_dest or is_route:
                results.append({
                    "restaurant": {
                        **r,
                        "location_type": "destination" if is_dest else "highway"
                    }
                })
        return results

    # 6. find_waypoints
    elif "PASSES_THROUGH" in cypher:
        route_id = params.get("route_id") or ""

        results = []
        for w in store["waypoints"]:
            w_route = w.get("route_id") or ""
            if w_route.lower() == route_id.lower():
                results.append({"waypoint": w})
        results.sort(key=lambda x: x["waypoint"].get("order", 0))
        return results

    return []


def _execute_write_local(cypher: str, parameters: dict = None):
    """Mock write Cypher queries against local JSON store.

    Symmetric ON CREATE / ON MATCH semantics: on match, fields supplied by the
    caller overwrite existing values when not None, so API refreshes correct
    stale data instead of being silently ignored.
    """
    params = parameters or {}
    store = _load_local_store()

    def _set_if(target: dict, key: str, value):
        """Only overwrite if caller provided a non-None / non-empty value."""
        if value is None:
            return
        if isinstance(value, str) and not value.strip():
            return
        target[key] = value

    # 1. merge_city
    if "MERGE (c:City" in cypher:
        name = params.get("name") or ""
        lat = params.get("lat")
        lng = params.get("lng")
        city_type = params.get("type") or "generic"

        existing = next((c for c in store["cities"] if (c.get("name") or "").lower() == name.lower()), None)
        if existing:
            # ON MATCH: refresh coordinates / type if caller supplied them
            _set_if(existing, "lat", lat)
            _set_if(existing, "lng", lng)
            if city_type != "generic":  # don't downgrade a real type to generic
                _set_if(existing, "type", city_type)
        else:
            store["cities"].append({
                "name": name,
                "lat": lat,
                "lng": lng,
                "type": city_type,
                "tags": [city_type] if city_type and city_type != "generic" else [],
            })

    # 2. merge_route
    elif "MERGE (r:Route" in cypher:
        origin = params.get("origin") or ""
        dest = params.get("dest") or ""
        route_id = params.get("route_id") or ""

        existing = next((r for r in store["routes"] if (r.get("route_id") or "").lower() == route_id.lower()), None)
        if existing:
            for k in ("distance_km", "duration_hours", "driving_distance", "driving_time", "polyline"):
                _set_if(existing, k, params.get(k))
        else:
            store["routes"].append({
                "route_id": route_id,
                "origin": origin,
                "destination": dest,
                "distance_km": params.get("distance_km"),
                "duration_hours": params.get("duration_hours"),
                "driving_distance": params.get("driving_distance"),
                "driving_time": params.get("driving_time"),
                "polyline": params.get("polyline"),
                "base_drive_minutes": int((params.get("duration_hours") or 0) * 60),
            })

    # 3. merge_hotel
    elif "MERGE (h:Hotel" in cypher:
        hotel_id = params.get("hotel_id") or ""

        existing = next((h for h in store["hotels"] if (h.get("hotel_id") or "").lower() == hotel_id.lower()), None)
        if existing:
            for k, v in [
                ("name", params.get("name")),
                ("lat", params.get("lat")),
                ("lng", params.get("lng")),
                ("tier", params.get("tier")),
                ("price_per_night", params.get("price")),
                ("address", params.get("address")),
                ("destination", params.get("destination")),
            ]:
                _set_if(existing, k, v)
        else:
            store["hotels"].append({
                "hotel_id": hotel_id,
                "name": params.get("name"),
                "lat": params.get("lat"),
                "lng": params.get("lng"),
                "tier": params.get("tier"),
                "price_per_night": params.get("price"),
                "address": params.get("address"),
                "destination": params.get("destination"),
            })

    # 4. merge_activity
    elif "MERGE (a:Activity" in cypher:
        activity_id = params.get("activity_id") or ""
        # Accept caller-provided tags list, else fall back to [category]
        tags = params.get("tags") or ([params["category"]] if params.get("category") else [])

        existing = next((a for a in store["activities"] if (a.get("activity_id") or "").lower() == activity_id.lower()), None)
        if existing:
            for k, v in [
                ("name", params.get("name")),
                ("lat", params.get("lat")),
                ("lng", params.get("lng")),
                ("category", params.get("category")),
                ("address", params.get("address")),
                ("destination", params.get("destination")),
            ]:
                _set_if(existing, k, v)
            if tags:
                merged = list({*(existing.get("tags") or []), *tags})
                existing["tags"] = merged
        else:
            store["activities"].append({
                "activity_id": activity_id,
                "name": params.get("name"),
                "lat": params.get("lat"),
                "lng": params.get("lng"),
                "category": params.get("category"),
                "address": params.get("address"),
                "tags": tags,
                "destination": params.get("destination"),
            })

    _save_local_store(store)


# ─── Public API: routes through Neo4j with JSON fallback ──────────────────────
def execute_query(cypher: str, parameters: dict = None) -> list[dict]:
    """Execute a Cypher query and return results as list of dicts. Falls back
    to the local JSON store if Neo4j is unreachable; retries Neo4j every
    NEO4J_RETRY_COOLDOWN_S seconds."""
    if _should_attempt_neo4j():
        try:
            driver = get_driver()
            with driver.session() as session:
                result = session.run(cypher, parameters or {})
                data = [record.data() for record in result]
                _mark_neo4j_ok()
                return data
        except Exception as e:
            if _NEO4J_LAST_FAIL_TS == 0.0:
                # Only log on first failure to avoid log spam — periodic retries are silent.
                print(f"  ⚠️  Neo4j unreachable ({e}). Using local JSON store; will retry every {NEO4J_RETRY_COOLDOWN_S:.0f}s.")
            _mark_neo4j_failed()

    return _execute_query_local(cypher, parameters)


def execute_write(cypher: str, parameters: dict = None):
    """Execute a write Cypher query. Same fallback + retry semantics as execute_query."""
    if _should_attempt_neo4j():
        try:
            driver = get_driver()
            with driver.session() as session:
                session.run(cypher, parameters or {})
                _mark_neo4j_ok()
                return
        except Exception as e:
            if _NEO4J_LAST_FAIL_TS == 0.0:
                print(f"  ⚠️  Neo4j unreachable ({e}). Using local JSON store; will retry every {NEO4J_RETRY_COOLDOWN_S:.0f}s.")
            _mark_neo4j_failed()

    _execute_write_local(cypher, parameters)
