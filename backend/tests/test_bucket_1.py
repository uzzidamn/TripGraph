"""
Bucket 1 Validation Script.
Validates JSON seed files for schema compliance and data quality.

Run: PYTHONPATH=. python backend/tests/test_bucket_1.py

Does NOT require Neo4j to be running.
"""
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PASS = 0
FAIL = 0


def check(condition: bool, msg: str) -> None:
    """Record a pass or fail and print the result."""
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {msg}")
    else:
        FAIL += 1
        print(f"  ❌ {msg}")


def load(filename: str) -> list:
    """Load a JSON seed file. Exits with error if file is missing."""
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  ❌ File not found: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


print("=" * 60)
print("Bucket 1 — Seed Data Validation")
print("=" * 60)

# --- Cities ---
print("\n📍 Cities:")
cities = load("seed_cities.json")
check(len(cities) == 4, f"Exactly 4 cities (found {len(cities)})")
check(
    all("name" in c and "type" in c and "lat" in c and "lng" in c and "description" in c for c in cities),
    "All cities have required fields (name, type, lat, lng, description)",
)
check(any(c["name"] == "Gurugram" and c["type"] == "origin" for c in cities), "Gurugram exists with type=origin")
check(any(c["name"] == "Jaipur" for c in cities), "Jaipur exists")
check(any(c["name"] == "Rishikesh" for c in cities), "Rishikesh exists")
check(any(c["name"] == "Tirthan Valley" for c in cities), "Tirthan Valley exists")
check(all(isinstance(c.get("tags"), list) and len(c["tags"]) > 0 for c in cities), "All cities have non-empty tags list")
check(
    all(t == t.lower() and " " not in t for c in cities for t in c.get("tags", [])),
    "All city tags are lowercase with no spaces",
)
city_names = {c["name"] for c in cities}

# --- Routes ---
print("\n🛣️  Routes:")
routes = load("seed_routes.json")
check(len(routes) == 3, f"Exactly 3 routes (found {len(routes)})")
check(
    all("route_id" in r and "origin" in r and "destination" in r and
        "distance_km" in r and "base_drive_minutes" in r and
        "risk_level" in r and "scenic_score" in r for r in routes),
    "All routes have required fields",
)
check(
    all(r["origin"] in city_names and r["destination"] in city_names for r in routes),
    "All route origin/destination reference valid city names",
)
check(
    all(r["risk_level"] in {"low", "medium", "high"} for r in routes),
    "All route risk_levels are valid (low/medium/high)",
)
check(
    all(1 <= r["scenic_score"] <= 10 for r in routes),
    "All scenic_scores are in range 1–10",
)
route_ids = {r["route_id"] for r in routes}

# --- Hotels ---
print("\n🏨 Hotels:")
hotels = load("seed_hotels.json")
check(len(hotels) >= 9, f"At least 9 hotels (found {len(hotels)})")
check(
    all("hotel_id" in h and "destination" in h and "tier" in h and
        "price_per_night" in h and "comfort_score" in h and
        "lat" in h and "lng" in h for h in hotels),
    "All hotels have required fields",
)
check(
    all(h["tier"] in {"budget", "comfort", "expedition"} for h in hotels),
    "All hotel tiers are valid (budget/comfort/expedition)",
)
for dest in ["Jaipur", "Rishikesh", "Tirthan Valley"]:
    dest_hotels = [h for h in hotels if h["destination"] == dest]
    tiers = {h["tier"] for h in dest_hotels}
    check({"budget", "comfort", "expedition"}.issubset(tiers), f"{dest} has all 3 tiers")
check(
    all(1 <= h["comfort_score"] <= 10 for h in hotels),
    "All comfort_scores are in range 1–10",
)
check(
    all(h["price_per_night"] > 0 for h in hotels),
    "All hotel prices are positive",
)

# --- Activities ---
print("\n🎯 Activities:")
activities = load("seed_activities.json")
check(len(activities) >= 9, f"At least 9 activities (found {len(activities)})")
check(
    all("activity_id" in a and "destination" in a and "category" in a and
        "duration_minutes" in a and "cost_per_person" in a and
        "available_slots" in a and "lat" in a and "lng" in a for a in activities),
    "All activities have required fields",
)
check(
    all(a["risk_level"] in {"low", "medium", "high"} for a in activities),
    "All activity risk_levels are valid",
)
check(
    all(isinstance(a["available_slots"], list) and len(a["available_slots"]) > 0 for a in activities),
    "All activities have non-empty available_slots",
)
check(
    all(a["destination"] in {"Jaipur", "Rishikesh", "Tirthan Valley"} for a in activities),
    "All activities belong to a valid destination",
)
for dest in ["Jaipur", "Rishikesh", "Tirthan Valley"]:
    dest_acts = [a for a in activities if a["destination"] == dest]
    check(len(dest_acts) >= 3, f"{dest} has at least 3 activities (found {len(dest_acts)})")

# --- Restaurants ---
print("\n🍽️  Restaurants:")
restaurants = load("seed_restaurants.json")
check(len(restaurants) >= 9, f"At least 9 restaurants (found {len(restaurants)})")
check(
    all("restaurant_id" in r and "meal_types" in r and
        "avg_cost_per_person" in r and "lat" in r and "lng" in r for r in restaurants),
    "All restaurants have required fields",
)
highway = [r for r in restaurants if r.get("route_id") and not r.get("destination")]
check(len(highway) >= 3, f"At least 3 highway restaurants (found {len(highway)})")
check(
    all("km_from_origin" in r for r in highway),
    "All highway restaurants have km_from_origin",
)
check(
    all(r.get("route_id") in route_ids for r in highway),
    "All highway restaurants reference valid route_ids",
)

# --- Transport ---
print("\n🚗 Transport:")
transport = load("seed_transport.json")
check(len(transport) >= 9, f"At least 9 transport options (found {len(transport)})")
check(
    all("transport_id" in t and "route_id" in t and "mode" in t and
        "tier" in t and "cost_total" in t and "night_driving_allowed" in t for t in transport),
    "All transport options have required fields",
)
check(
    all(t["tier"] in {"budget", "comfort", "expedition"} for t in transport),
    "All transport tiers are valid",
)
check(
    all(t["route_id"] in route_ids for t in transport),
    "All transport options reference valid route_ids",
)
for rid in route_ids:
    rt = [t for t in transport if t["route_id"] == rid]
    tiers = {t["tier"] for t in rt}
    check({"budget", "comfort", "expedition"}.issubset(tiers), f"Route {rid} has all 3 transport tiers")
check(
    all(isinstance(t["night_driving_allowed"], bool) for t in transport),
    "All night_driving_allowed values are boolean",
)

# --- Waypoints ---
print("\n📌 Waypoints:")
waypoints = load("seed_waypoints.json")
check(len(waypoints) >= 6, f"At least 6 waypoints (found {len(waypoints)})")
check(
    all("waypoint_id" in w and "route_id" in w and "order" in w and
        "km_from_origin" in w and "lat" in w and "lng" in w and
        "typical_stop_minutes" in w for w in waypoints),
    "All waypoints have required fields",
)
check(
    all(w["route_id"] in route_ids for w in waypoints),
    "All waypoints reference valid route_ids",
)
check(
    all(w["type"] in {"breakfast_stop", "fuel_stop", "viewpoint", "rest_stop"} for w in waypoints),
    "All waypoint types are valid",
)
for rid in route_ids:
    route_wps = sorted([w for w in waypoints if w["route_id"] == rid], key=lambda x: x["order"])
    orders = [w["order"] for w in route_wps]
    check(
        orders == list(range(1, len(orders) + 1)),
        f"Route {rid} waypoint orders are sequential starting at 1 (found {orders})",
    )

# --- Global ID uniqueness ---
print("\n🔑 Uniqueness:")
all_ids = (
    [h["hotel_id"] for h in hotels]
    + [a["activity_id"] for a in activities]
    + [r["restaurant_id"] for r in restaurants]
    + [t["transport_id"] for t in transport]
    + [w["waypoint_id"] for w in waypoints]
    + list(route_ids)
)
check(len(all_ids) == len(set(all_ids)), f"All IDs are globally unique ({len(all_ids)} total)")

# --- Summary ---
print("\n" + "=" * 60)
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("🎉 ALL CHECKS PASSED — Bucket 1 data is valid!")
else:
    print("⚠️  Some checks failed. Review the output above.")
    sys.exit(1)
