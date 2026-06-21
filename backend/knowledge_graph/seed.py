"""
Seed script: Loads all JSON data files into the Neo4j knowledge graph.

Usage:
    PYTHONPATH=. python -m backend.knowledge_graph.seed

Requires:
    Neo4j running at bolt://localhost:7687 (configure via .env)
    Environment variables: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
"""
import json
import sys
from pathlib import Path

from backend.knowledge_graph.connection import get_driver
from backend.knowledge_graph.schema import create_schema

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename: str) -> list[dict]:
    """Load a JSON seed file from the data directory. Exits on missing file."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def seed_cities(tx) -> None:
    """Create City nodes and their TAGGED relationships to Tag nodes."""
    cities = load_json("seed_cities.json")
    for city in cities:
        tx.run(
            "MERGE (c:City {name: $name}) "
            "SET c.type = $type, c.lat = $lat, c.lng = $lng, "
            "c.description = $description, c.confidence_pct = $confidence_pct, "
            "c.verification_status = $verification_status, c.data_source = $data_source, "
            "c.last_verified = $last_verified",
            name=city["name"],
            type=city["type"],
            lat=city["lat"],
            lng=city["lng"],
            description=city["description"],
            confidence_pct=city.get("confidence_pct", 100),
            verification_status=city.get("verification_status", "verified"),
            data_source=city.get("data_source", "manual"),
            last_verified=city.get("last_verified", "2026-06-22"),
        )
        for tag in city.get("tags", []):
            tx.run(
                "MERGE (t:Tag {name: $tag}) "
                "WITH t "
                "MATCH (c:City {name: $city_name}) "
                "MERGE (c)-[:TAGGED]->(t)",
                tag=tag,
                city_name=city["name"],
            )
    print(f"  ✅ Seeded {len(cities)} cities")


def seed_routes(tx) -> None:
    """Create Route nodes and ORIGIN_OF / ARRIVES_AT relationships to City nodes.

    Cities must be seeded before routes. The origin and destination fields in JSON
    are used to create relationships and are not stored on the Route node itself.
    """
    routes = load_json("seed_routes.json")
    for route in routes:
        tx.run(
            "MERGE (r:Route {route_id: $route_id}) "
            "SET r.distance_km = $distance_km, "
            "r.base_drive_minutes = $base_drive_minutes, "
            "r.risk_level = $risk_level, "
            "r.scenic_score = $scenic_score, "
            "r.recommended_for = $recommended_for, "
            "r.highway = $highway, "
            "r.flight_available = $flight_available, "
            "r.flight_duration_minutes = $flight_duration_minutes, "
            "r.train_available = $train_available, "
            "r.train_duration_minutes = $train_duration_minutes, "
            "r.confidence_pct = $confidence_pct, "
            "r.verification_status = $verification_status, "
            "r.data_source = $data_source, "
            "r.last_verified = $last_verified",
            route_id=route["route_id"],
            distance_km=route["distance_km"],
            base_drive_minutes=route["base_drive_minutes"],
            risk_level=route["risk_level"],
            scenic_score=route["scenic_score"],
            recommended_for=route["recommended_for"],
            highway=route.get("highway"),
            flight_available=route.get("flight_available", False),
            flight_duration_minutes=route.get("flight_duration_minutes", 0),
            train_available=route.get("train_available", False),
            train_duration_minutes=route.get("train_duration_minutes", 0),
            confidence_pct=route.get("confidence_pct", 100),
            verification_status=route.get("verification_status", "verified"),
            data_source=route.get("data_source", "manual"),
            last_verified=route.get("last_verified", "2026-06-22"),
        )
        tx.run(
            "MATCH (origin:City {name: $origin}), (r:Route {route_id: $route_id}) "
            "MERGE (origin)-[:ORIGIN_OF]->(r)",
            origin=route["origin"],
            route_id=route["route_id"],
        )
        tx.run(
            "MATCH (dest:City {name: $destination}), (r:Route {route_id: $route_id}) "
            "MERGE (r)-[:ARRIVES_AT]->(dest)",
            destination=route["destination"],
            route_id=route["route_id"],
        )
    print(f"  ✅ Seeded {len(routes)} routes")


def seed_hotels(tx) -> None:
    """Create Hotel nodes and HAS_HOTEL relationships from destination City nodes."""
    hotels = load_json("seed_hotels.json")
    for hotel in hotels:
        tx.run(
            "MERGE (h:Hotel {hotel_id: $hotel_id}) "
            "SET h.name = $name, h.tier = $tier, "
            "h.price_per_night = $price_per_night, "
            "h.rooms_required = $rooms_required, "
            "h.checkin_time = $checkin_time, "
            "h.checkout_time = $checkout_time, "
            "h.comfort_score = $comfort_score, "
            "h.lat = $lat, h.lng = $lng, "
            "h.amenities = $amenities, h.tags = $tags, "
            "h.editorial_summary = $editorial_summary, "
            "h.price_confidence = $price_confidence, "
            "h.confidence_pct = $confidence_pct, "
            "h.verification_status = $verification_status, "
            "h.data_source = $data_source, "
            "h.last_verified = $last_verified",
            hotel_id=hotel["hotel_id"],
            name=hotel["name"],
            tier=hotel["tier"],
            price_per_night=hotel["price_per_night"],
            rooms_required=hotel["rooms_required"],
            checkin_time=hotel["checkin_time"],
            checkout_time=hotel["checkout_time"],
            comfort_score=hotel["comfort_score"],
            lat=hotel["lat"],
            lng=hotel["lng"],
            amenities=hotel["amenities"],
            tags=hotel["tags"],
            editorial_summary=hotel.get("editorial_summary", ""),
            price_confidence=hotel.get("price_confidence", "medium"),
            confidence_pct=hotel.get("confidence_pct", 100),
            verification_status=hotel.get("verification_status", "verified"),
            data_source=hotel.get("data_source", "manual"),
            last_verified=hotel.get("last_verified", "2026-06-22"),
        )
        tx.run(
            "MATCH (c:City {name: $destination}), (h:Hotel {hotel_id: $hotel_id}) "
            "MERGE (c)-[:HAS_HOTEL]->(h)",
            destination=hotel["destination"],
            hotel_id=hotel["hotel_id"],
        )
    print(f"  ✅ Seeded {len(hotels)} hotels")


def seed_activities(tx) -> None:
    """Create Activity nodes, HAS_ACTIVITY relationships, and TAGGED relationships."""
    activities = load_json("seed_activities.json")
    for act in activities:
        tx.run(
            "MERGE (a:Activity {activity_id: $activity_id}) "
            "SET a.name = $name, a.category = $category, "
            "a.duration_minutes = $duration_minutes, "
            "a.cost_per_person = $cost_per_person, "
            "a.available_slots = $available_slots, "
            "a.risk_level = $risk_level, "
            "a.tags = $tags, a.lat = $lat, a.lng = $lng, "
            "a.fatigue_score_base = $fatigue_score_base, "
            "a.morale_score_base = $morale_score_base, "
            "a.editorial_summary = $editorial_summary, "
            "a.opening_hours = $opening_hours, "
            "a.skip_if = $skip_if, "
            "a.insider_tip = $insider_tip, "
            "a.confidence_pct = $confidence_pct, "
            "a.verification_status = $verification_status, "
            "a.data_source = $data_source, "
            "a.last_verified = $last_verified",
            activity_id=act["activity_id"],
            name=act["name"],
            category=act["category"],
            duration_minutes=act["duration_minutes"],
            cost_per_person=act["cost_per_person"],
            available_slots=act["available_slots"],
            risk_level=act["risk_level"],
            tags=act["tags"],
            lat=act["lat"],
            lng=act["lng"],
            fatigue_score_base=act.get("fatigue_score_base", 5),
            morale_score_base=act.get("morale_score_base", 5),
            editorial_summary=act.get("editorial_summary", ""),
            opening_hours=act.get("opening_hours", []),
            skip_if=act.get("skip_if", ""),
            insider_tip=act.get("insider_tip", ""),
            confidence_pct=act.get("confidence_pct", 100),
            verification_status=act.get("verification_status", "verified"),
            data_source=act.get("data_source", "manual"),
            last_verified=act.get("last_verified", "2026-06-22"),
        )
        tx.run(
            "MATCH (c:City {name: $destination}), (a:Activity {activity_id: $activity_id}) "
            "MERGE (c)-[:HAS_ACTIVITY]->(a)",
            destination=act["destination"],
            activity_id=act["activity_id"],
        )
        for tag in act.get("tags", []):
            tx.run(
                "MERGE (t:Tag {name: $tag}) "
                "WITH t "
                "MATCH (a:Activity {activity_id: $activity_id}) "
                "MERGE (a)-[:TAGGED]->(t)",
                tag=tag,
                activity_id=act["activity_id"],
            )
    print(f"  ✅ Seeded {len(activities)} activities")


def seed_restaurants(tx) -> None:
    """Create Restaurant nodes with appropriate relationships.

    Destination restaurants: City -[:HAS_RESTAURANT]-> Restaurant
    Highway restaurants:     Restaurant -[:ON_ROUTE {km_from_origin}]-> Route

    Detection rule: if route_id is set and destination is null → highway restaurant.
    """
    restaurants = load_json("seed_restaurants.json")
    for rest in restaurants:
        tx.run(
            "MERGE (r:Restaurant {restaurant_id: $restaurant_id}) "
            "SET r.name = $name, r.meal_types = $meal_types, "
            "r.avg_cost_per_person = $avg_cost_per_person, "
            "r.avg_duration_minutes = $avg_duration_minutes, "
            "r.tags = $tags, r.lat = $lat, r.lng = $lng, "
            "r.signature_dish = $signature_dish, "
            "r.insider_tip = $insider_tip, "
            "r.confidence_pct = $confidence_pct, "
            "r.verification_status = $verification_status, "
            "r.data_source = $data_source, "
            "r.last_verified = $last_verified",
            restaurant_id=rest["restaurant_id"],
            name=rest["name"],
            meal_types=rest["meal_types"],
            avg_cost_per_person=rest["avg_cost_per_person"],
            avg_duration_minutes=rest["avg_duration_minutes"],
            tags=rest["tags"],
            lat=rest["lat"],
            lng=rest["lng"],
            signature_dish=rest.get("signature_dish", ""),
            insider_tip=rest.get("insider_tip", ""),
            confidence_pct=rest.get("confidence_pct", 100),
            verification_status=rest.get("verification_status", "verified"),
            data_source=rest.get("data_source", "manual"),
            last_verified=rest.get("last_verified", "2026-06-22"),
        )
        if rest.get("destination"):
            tx.run(
                "MATCH (c:City {name: $destination}), (r:Restaurant {restaurant_id: $rid}) "
                "MERGE (c)-[:HAS_RESTAURANT]->(r)",
                destination=rest["destination"],
                rid=rest["restaurant_id"],
            )
        elif rest.get("route_id"):
            tx.run(
                "MATCH (route:Route {route_id: $route_id}), "
                "(r:Restaurant {restaurant_id: $rid}) "
                "MERGE (r)-[:ON_ROUTE {km_from_origin: $km}]->(route)",
                route_id=rest["route_id"],
                rid=rest["restaurant_id"],
                km=rest.get("km_from_origin", 0),
            )
        for tag in rest.get("tags", []):
            tx.run(
                "MERGE (t:Tag {name: $tag}) "
                "WITH t "
                "MATCH (r:Restaurant {restaurant_id: $rid}) "
                "MERGE (r)-[:TAGGED]->(t)",
                tag=tag,
                rid=rest["restaurant_id"],
            )
    print(f"  ✅ Seeded {len(restaurants)} restaurants")


def seed_transport(tx) -> None:
    """Create TransportOption nodes and HAS_TRANSPORT relationships from Route nodes."""
    transport = load_json("seed_transport.json")
    for t in transport:
        tx.run(
            "MERGE (to:TransportOption {transport_id: $transport_id}) "
            "SET to.mode = $mode, to.tier = $tier, "
            "to.cost_total = $cost_total, to.capacity = $capacity, "
            "to.base_duration_minutes = $base_duration_minutes, "
            "to.night_driving_allowed = $night_driving_allowed, "
            "to.comfort_score = $comfort_score, "
            "to.fatigue_score = $fatigue_score, "
            "to.tags = $tags, "
            "to.confidence_pct = $confidence_pct, "
            "to.verification_status = $verification_status, "
            "to.data_source = $data_source, "
            "to.last_verified = $last_verified",
            transport_id=t["transport_id"],
            mode=t["mode"],
            tier=t["tier"],
            cost_total=t["cost_total"],
            capacity=t["capacity"],
            base_duration_minutes=t["base_duration_minutes"],
            night_driving_allowed=t["night_driving_allowed"],
            comfort_score=t["comfort_score"],
            fatigue_score=t["fatigue_score"],
            tags=t["tags"],
            confidence_pct=t.get("confidence_pct", 100),
            verification_status=t.get("verification_status", "verified"),
            data_source=t.get("data_source", "manual"),
            last_verified=t.get("last_verified", "2026-06-22"),
        )
        tx.run(
            "MATCH (r:Route {route_id: $route_id}), "
            "(to:TransportOption {transport_id: $tid}) "
            "MERGE (r)-[:HAS_TRANSPORT]->(to)",
            route_id=t["route_id"],
            tid=t["transport_id"],
        )
    print(f"  ✅ Seeded {len(transport)} transport options")


def seed_waypoints(tx) -> None:
    """Create Waypoint nodes and PASSES_THROUGH relationships with order and km properties."""
    waypoints = load_json("seed_waypoints.json")
    for wp in waypoints:
        tx.run(
            "MERGE (w:Waypoint {waypoint_id: $waypoint_id}) "
            "SET w.name = $name, w.type = $type, "
            "w.km_from_origin = $km_from_origin, "
            "w.lat = $lat, w.lng = $lng, "
            "w.typical_stop_minutes = $typical_stop_minutes, "
            "w.order = $order",
            waypoint_id=wp["waypoint_id"],
            name=wp["name"],
            type=wp["type"],
            km_from_origin=wp["km_from_origin"],
            lat=wp["lat"],
            lng=wp["lng"],
            typical_stop_minutes=wp["typical_stop_minutes"],
            order=wp["order"],
        )
        tx.run(
            "MATCH (r:Route {route_id: $route_id}), (w:Waypoint {waypoint_id: $wid}) "
            "MERGE (r)-[:PASSES_THROUGH {order: $order, km_from_origin: $km}]->(w)",
            route_id=wp["route_id"],
            wid=wp["waypoint_id"],
            order=wp["order"],
            km=wp["km_from_origin"],
        )
    print(f"  ✅ Seeded {len(waypoints)} waypoints")


def seed_all() -> None:
    """Run the complete seed pipeline: schema creation then all entity loaders."""
    try:
        driver = get_driver()
        driver.verify_connectivity()
        print("🔗 Connected to Neo4j")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        sys.exit(1)

    create_schema()

    with driver.session() as session:
        # Order matters: cities and routes must exist before entities that reference them
        session.execute_write(seed_cities)
        session.execute_write(seed_routes)
        session.execute_write(seed_hotels)
        session.execute_write(seed_activities)
        session.execute_write(seed_restaurants)
        session.execute_write(seed_transport)
        session.execute_write(seed_waypoints)

    print("\n✅ All seed data loaded into Neo4j successfully!")


if __name__ == "__main__":
    seed_all()
