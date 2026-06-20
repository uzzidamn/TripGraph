"""
Neo4j connection manager. Singleton driver for the application.
With automatic fallback to a local JSON knowledge graph database when Neo4j is offline.
"""
import os
import json
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

_driver = None
USE_LOCAL_KG = False

_DATA_DIR = Path(__file__).parent.parent / "data"
_LOCAL_STORE_PATH = _DATA_DIR / "local_kg_store.json"

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

def _load_local_store() -> dict:
    if _LOCAL_STORE_PATH.exists():
        try:
            with open(_LOCAL_STORE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Initialize from seed files
    store = {
        "cities": [],
        "routes": [],
        "hotels": [],
        "activities": [],
        "restaurants": [],
        "transport": [],
        "waypoints": []
    }
    
    seed_mapping = {
        "cities": "seed_cities.json",
        "routes": "seed_routes.json",
        "hotels": "seed_hotels.json",
        "activities": "seed_activities.json",
        "restaurants": "seed_restaurants.json",
        "transport": "seed_transport.json",
        "waypoints": "seed_waypoints.json"
    }
    
    for key, filename in seed_mapping.items():
        filepath = _DATA_DIR / filename
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    store[key] = json.load(f)
            except Exception as e:
                print(f"  ⚠️  Failed to read seed file {filename}: {e}")
                
    _save_local_store(store)
    return store

def _save_local_store(store: dict):
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(_LOCAL_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, default=str)
    except Exception as e:
        print(f"  ⚠️  Failed to write local KG store: {e}")

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
                # Resolve destination type/lat/lng from cities list
                r_dest = r.get("destination") or ""
                dest_city = next((c for c in store["cities"] if (c.get("name") or "").lower() == r_dest.lower()), None)
                dest_t = dest_city.get("type") or "" if dest_city else (r.get("destination_type") or "")
                dest_lat = dest_city.get("lat") or 0.0 if dest_city else (r.get("dest_lat") or 0.0)
                dest_lng = dest_city.get("lng") or 0.0 if dest_city else (r.get("dest_lng") or 0.0)
                
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
        # Sort by price_per_night ASC
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
    """Mock write Cypher queries against local JSON store."""
    params = parameters or {}
    store = _load_local_store()
    
    # 1. merge_city
    if "MERGE (c:City" in cypher:
        name = params.get("name") or ""
        lat = params.get("lat")
        lng = params.get("lng")
        city_type = params.get("type", "generic") or "generic"
        
        existing = next((c for c in store["cities"] if (c.get("name") or "").lower() == name.lower()), None)
        if existing:
            existing["lat"] = lat if lat is not None else existing.get("lat")
            existing["lng"] = lng if lng is not None else existing.get("lng")
            if "type" not in existing or existing["type"] == "generic":
                existing["type"] = city_type
        else:
            store["cities"].append({
                "name": name,
                "lat": lat,
                "lng": lng,
                "type": city_type
            })
            
    # 2. merge_route
    elif "MERGE (r:Route" in cypher:
        origin = params.get("origin") or ""
        dest = params.get("dest") or ""
        route_id = params.get("route_id") or ""
        
        existing = next((r for r in store["routes"] if (r.get("route_id") or "").lower() == route_id.lower()), None)
        if existing:
            existing["distance_km"] = params.get("distance_km")
            existing["duration_hours"] = params.get("duration_hours")
            existing["driving_distance"] = params.get("driving_distance")
            existing["driving_time"] = params.get("driving_time")
        else:
            store["routes"].append({
                "route_id": route_id,
                "origin": origin,
                "destination": dest,
                "distance_km": params.get("distance_km"),
                "duration_hours": params.get("duration_hours"),
                "driving_distance": params.get("driving_distance"),
                "driving_time": params.get("driving_time"),
            })
            
    # 3. merge_hotel
    elif "MERGE (h:Hotel" in cypher:
        hotel_id = params.get("hotel_id") or ""
        
        existing = next((h for h in store["hotels"] if (h.get("hotel_id") or "").lower() == hotel_id.lower()), None)
        if existing:
            existing["name"] = params.get("name")
            existing["lat"] = params.get("lat")
            existing["lng"] = params.get("lng")
            existing["tier"] = params.get("tier")
            existing["price_per_night"] = params.get("price")
            existing["address"] = params.get("address")
        else:
            store["hotels"].append({
                "hotel_id": hotel_id,
                "name": params.get("name"),
                "lat": params.get("lat"),
                "lng": params.get("lng"),
                "tier": params.get("tier"),
                "price_per_night": params.get("price"),
                "address": params.get("address"),
                "destination": params.get("destination")
            })
            
    # 4. merge_activity
    elif "MERGE (a:Activity" in cypher:
        activity_id = params.get("activity_id") or ""
        
        existing = next((a for a in store["activities"] if (a.get("activity_id") or "").lower() == activity_id.lower()), None)
        if existing:
            existing["name"] = params.get("name")
            existing["lat"] = params.get("lat")
            existing["lng"] = params.get("lng")
            existing["category"] = params.get("category")
            existing["address"] = params.get("address")
            existing["tags"] = [params.get("category")]
        else:
            store["activities"].append({
                "activity_id": activity_id,
                "name": params.get("name"),
                "lat": params.get("lat"),
                "lng": params.get("lng"),
                "category": params.get("category"),
                "address": params.get("address"),
                "tags": [params.get("category")],
                "destination": params.get("destination")
            })
            
    _save_local_store(store)

def execute_query(cypher: str, parameters: dict = None) -> list[dict]:
    """Execute a Cypher query and return results as list of dicts."""
    global USE_LOCAL_KG
    if not USE_LOCAL_KG:
        try:
            driver = get_driver()
            with driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"  ⚠️  Neo4j connection or query failed ({e}). Falling back to local JSON store.")
            USE_LOCAL_KG = True
            
    return _execute_query_local(cypher, parameters)

def execute_write(cypher: str, parameters: dict = None):
    """Execute a write Cypher query."""
    global USE_LOCAL_KG
    if not USE_LOCAL_KG:
        try:
            driver = get_driver()
            with driver.session() as session:
                session.run(cypher, parameters or {})
                return
        except Exception as e:
            print(f"  ⚠️  Neo4j connection or write failed ({e}). Falling back to local JSON store.")
            USE_LOCAL_KG = True
            
    _execute_write_local(cypher, parameters)
