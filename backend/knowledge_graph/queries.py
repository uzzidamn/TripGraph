"""
Reusable Cypher queries for the knowledge graph.
Each function returns a Cypher string and parameters dict.
"""

class TravelQueries:
    """Cypher queries organized by entity type."""

    @staticmethod
    def find_routes(origin: str, destination_type: str | None = None) -> tuple[str, dict]:
        if destination_type:
            return (
                """
                MATCH (origin:City {name: $origin})-[:ORIGIN_OF]->(r:Route)-[:ARRIVES_AT]->(dest:City)
                WHERE dest.type = $dest_type
                RETURN r {.*, origin: origin.name, destination: dest.name, destination_type: dest.type,
                          dest_lat: dest.lat, dest_lng: dest.lng} AS route
                """,
                {"origin": origin, "dest_type": destination_type},
            )
        return (
            """
            MATCH (origin:City {name: $origin})-[:ORIGIN_OF]->(r:Route)-[:ARRIVES_AT]->(dest:City)
            RETURN r {.*, origin: origin.name, destination: dest.name, destination_type: dest.type,
                      dest_lat: dest.lat, dest_lng: dest.lng} AS route
            """,
            {"origin": origin},
        )

    @staticmethod
    def find_hotels(destination: str, tier: str | None = None) -> tuple[str, dict]:
        if tier:
            return (
                """
                MATCH (c:City {name: $destination})-[:HAS_HOTEL]->(h:Hotel {tier: $tier})
                RETURN h {.*} AS hotel
                ORDER BY h.price_per_night ASC
                """,
                {"destination": destination, "tier": tier},
            )
        return (
            """
            MATCH (c:City {name: $destination})-[:HAS_HOTEL]->(h:Hotel)
            RETURN h {.*} AS hotel
            ORDER BY h.tier, h.price_per_night ASC
            """,
            {"destination": destination},
        )

    @staticmethod
    def find_activities(destination: str, tags: list[str] | None = None) -> tuple[str, dict]:
        if tags:
            return (
                """
                MATCH (c:City {name: $destination})-[:HAS_ACTIVITY]->(a:Activity)
                WHERE any(tag IN $tags WHERE tag IN a.tags)
                RETURN a {.*} AS activity
                """,
                {"destination": destination, "tags": tags},
            )
        return (
            """
            MATCH (c:City {name: $destination})-[:HAS_ACTIVITY]->(a:Activity)
            RETURN a {.*} AS activity
            """,
            {"destination": destination},
        )

    @staticmethod
    def find_transport(route_id: str, modes: list[str] | None = None) -> tuple[str, dict]:
        if modes:
            return (
                """
                MATCH (r:Route {route_id: $route_id})-[:HAS_TRANSPORT]->(t:TransportOption)
                WHERE t.mode IN $modes
                RETURN t {.*} AS transport
                ORDER BY t.cost_total ASC
                """,
                {"route_id": route_id, "modes": modes},
            )
        return (
            """
            MATCH (r:Route {route_id: $route_id})-[:HAS_TRANSPORT]->(t:TransportOption)
            RETURN t {.*} AS transport
            ORDER BY t.cost_total ASC
            """,
            {"route_id": route_id},
        )

    @staticmethod
    def find_restaurants(destination: str, route_id: str | None = None) -> tuple[str, dict]:
        if route_id:
            # Get both destination restaurants and highway stops
            return (
                """
                MATCH (c:City {name: $destination})-[:HAS_RESTAURANT]->(r:Restaurant)
                RETURN r {.*, location_type: 'destination'} AS restaurant
                UNION
                MATCH (route:Route {route_id: $route_id})<-[:ON_ROUTE]-(r:Restaurant)
                RETURN r {.*, location_type: 'highway'} AS restaurant
                """,
                {"destination": destination, "route_id": route_id},
            )
        return (
            """
            MATCH (c:City {name: $destination})-[:HAS_RESTAURANT]->(r:Restaurant)
            RETURN r {.*} AS restaurant
            """,
            {"destination": destination},
        )

    @staticmethod
    def find_waypoints(route_id: str) -> tuple[str, dict]:
        return (
            """
            MATCH (r:Route {route_id: $route_id})-[:PASSES_THROUGH]->(w:Waypoint)
            RETURN w {.*} AS waypoint
            ORDER BY w.order ASC
            """,
            {"route_id": route_id},
        )

    @staticmethod
    def full_route_data(origin: str, destination_type: str | None = None) -> tuple[str, dict]:
        """Get complete route data with all connected entities."""
        params = {"origin": origin}
        where_clause = ""
        if destination_type:
            where_clause = "WHERE dest.type = $dest_type"
            params["dest_type"] = destination_type

        return (
            f"""
            MATCH (origin:City {{name: $origin}})-[:ORIGIN_OF]->(r:Route)-[:ARRIVES_AT]->(dest:City)
            {where_clause}
            OPTIONAL MATCH (dest)-[:HAS_HOTEL]->(h:Hotel)
            OPTIONAL MATCH (dest)-[:HAS_ACTIVITY]->(a:Activity)
            OPTIONAL MATCH (r)-[:HAS_TRANSPORT]->(t:TransportOption)
            OPTIONAL MATCH (dest)-[:HAS_RESTAURANT]->(rest:Restaurant)
            OPTIONAL MATCH (r)-[:PASSES_THROUGH]->(w:Waypoint)
            RETURN r {{.*, origin: origin.name}} AS route,
                   dest {{.*}} AS destination,
                   collect(DISTINCT h {{.*}}) AS hotels,
                   collect(DISTINCT a {{.*}}) AS activities,
                   collect(DISTINCT t {{.*}}) AS transport,
                   collect(DISTINCT rest {{.*}}) AS restaurants,
                   collect(DISTINCT w {{.*}}) AS waypoints
            """,
            params,
        )

class IngestionQueries:
    """Cypher queries for inserting/merging new API data into the KG."""

    @staticmethod
    def merge_city(name: str, lat: float, lng: float, city_type: str = "generic") -> tuple[str, dict]:
        return (
            """
            MERGE (c:City {name: $name})
            ON CREATE SET c.lat = $lat, c.lng = $lng, c.type = $type
            ON MATCH SET c.lat = coalesce(c.lat, $lat), c.lng = coalesce(c.lng, $lng), c.type = case when c.type is null then $type else c.type end
            RETURN c {.*} AS city
            """,
            {"name": name, "lat": lat, "lng": lng, "type": city_type}
        )

    @staticmethod
    def merge_route(origin: str, dest: str, route_id: str, distance_km: float, duration_hours: float, driving_distance: str, driving_time: str) -> tuple[str, dict]:
        return (
            """
            MATCH (orig:City {name: $origin})
            MATCH (dest:City {name: $dest})
            MERGE (r:Route {route_id: $route_id})
            ON CREATE SET r.distance_km = $distance_km, r.duration_hours = $duration_hours,
                          r.driving_distance = $driving_distance, r.driving_time = $driving_time
            MERGE (orig)-[:ORIGIN_OF]->(r)
            MERGE (r)-[:ARRIVES_AT]->(dest)
            RETURN r {.*} AS route
            """,
            {
                "origin": origin, "dest": dest, "route_id": route_id,
                "distance_km": distance_km, "duration_hours": duration_hours,
                "driving_distance": driving_distance, "driving_time": driving_time
            }
        )

    @staticmethod
    def merge_hotel(destination: str, hotel_id: str, name: str, lat: float, lng: float, tier: str = "comfort", price: int = 5000, address: str = "") -> tuple[str, dict]:
        return (
            """
            MATCH (c:City {name: $destination})
            MERGE (h:Hotel {hotel_id: $hotel_id})
            ON CREATE SET h.name = $name, h.lat = $lat, h.lng = $lng, h.tier = $tier, 
                          h.price_per_night = $price, h.address = $address, h.destination = $destination
            MERGE (c)-[:HAS_HOTEL]->(h)
            RETURN h {.*} AS hotel
            """,
            {
                "destination": destination, "hotel_id": hotel_id, "name": name,
                "lat": lat, "lng": lng, "tier": tier, "price": price, "address": address
            }
        )

    @staticmethod
    def merge_activity(destination: str, activity_id: str, name: str, lat: float, lng: float, category: str, address: str = "") -> tuple[str, dict]:
        return (
            """
            MATCH (c:City {name: $destination})
            MERGE (a:Activity {activity_id: $activity_id})
            ON CREATE SET a.name = $name, a.lat = $lat, a.lng = $lng, a.category = $category,
                          a.address = $address, a.tags = [$category]
            MERGE (c)-[:HAS_ACTIVITY]->(a)
            RETURN a {.*} AS activity
            """,
            {
                "destination": destination, "activity_id": activity_id, "name": name,
                "lat": lat, "lng": lng, "category": category, "address": address
            }
        )

