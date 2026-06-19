"""
Tool: get_routes — returns matching routes from the knowledge graph.
"""
import uuid
from backend.knowledge_graph.connection import execute_query, execute_write
from backend.knowledge_graph.queries import TravelQueries, IngestionQueries
from backend.api_clients.ors_client import ORSClient

def get_routes(origin: str, destination_type: str | None = None, destination: str | None = None) -> list[dict]:
    """
    Returns route options matching origin and optional destination type/name.
    Falls back to OpenRouteService API if not found and destination is provided.
    """
    cypher, params = TravelQueries.find_routes(origin, destination_type)
    try:
        results = execute_query(cypher, params)
        routes = [r["route"] for r in results]
    except Exception as e:
        print(f"  ⚠️  Neo4j read failed in route_tool: {e}")
        routes = []
    
    if destination:
        # Filter routes by specific destination if required by KG query results
        routes = [r for r in routes if r.get("destination") == destination]
        
    if not routes and destination:
        print(f"  [API] Route {origin} -> {destination} not in KG. Fetching from ORS...")
        orig_geo = ORSClient.geocode(origin)
        dest_geo = ORSClient.geocode(destination)
        
        if orig_geo and dest_geo:
            route_data = ORSClient.get_route(orig_geo['lng'], orig_geo['lat'], dest_geo['lng'], dest_geo['lat'])
            if route_data:
                # Merge into KG
                route_id = f"route_{uuid.uuid4().hex[:8]}"
                cypher_c1, p_c1 = IngestionQueries.merge_city(origin, orig_geo['lat'], orig_geo['lng'])
                cypher_c2, p_c2 = IngestionQueries.merge_city(destination, dest_geo['lat'], dest_geo['lng'], destination_type or "generic")
                cypher_r, p_r = IngestionQueries.merge_route(origin, destination, route_id, route_data['distance_km'], route_data['duration_hours'], route_data['driving_distance'], route_data['driving_time'])
                
                try:
                    execute_write(cypher_c1, p_c1)
                    execute_write(cypher_c2, p_c2)
                    execute_write(cypher_r, p_r)
                    
                    # Fetch again from KG to get the standard format
                    cypher, params = TravelQueries.find_routes(origin, destination_type)
                    results = execute_query(cypher, params)
                    routes = [r["route"] for r in results if r["route"].get("destination") == destination]
                except Exception as e:
                    print(f"  ⚠️  Failed to cache route in Neo4j: {e}")
                    # If Neo4j is down, just return the raw object
                    routes = [{
                        "route_id": route_id,
                        "origin": origin,
                        "destination": destination,
                        "destination_type": destination_type or "generic",
                        "dest_lat": dest_geo['lat'],
                        "dest_lng": dest_geo['lng'],
                        "distance_km": route_data['distance_km'],
                        "duration_hours": route_data['duration_hours'],
                        "driving_distance": route_data['driving_distance'],
                        "driving_time": route_data['driving_time']
                    }]
    return routes
