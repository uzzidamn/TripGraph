"""
Tool: get_activities — returns activities matching destination and optional tags.
"""
import uuid
from backend.knowledge_graph.connection import execute_query, execute_write
from backend.knowledge_graph.queries import TravelQueries, IngestionQueries
from backend.api_clients.geoapify_client import GeoapifyClient
from backend.api_clients.ors_client import ORSClient

def get_activities(destination: str, tags: list[str] | None = None) -> list[dict]:
    """
    Returns activities at a destination, optionally filtered by preference tags.
    Falls back to Geoapify API if none are found in the Knowledge Graph.
    """
    cypher, params = TravelQueries.find_activities(destination, tags)
    try:
        results = execute_query(cypher, params)
        activities = [r["activity"] for r in results]
    except Exception:
        activities = []
        
    if not activities:
        print(f"  [API] Activities for {destination} not in KG. Fetching from Geoapify...")
        dest_geo = ORSClient.geocode(destination)
        if dest_geo:
            api_activities = GeoapifyClient.get_activities(dest_geo['lat'], dest_geo['lng'], limit=5)
            fallback_activities = []
            for a in api_activities:
                activity_id = f"activity_{uuid.uuid4().hex[:8]}"
                a_obj = {
                    "activity_id": activity_id,
                    "name": a["name"],
                    "lat": a["lat"],
                    "lng": a["lng"],
                    "category": a.get("category", "attraction"),
                    "address": a.get("address", ""),
                    "tags": [a.get("category", "attraction")],
                    "destination": destination
                }
                fallback_activities.append(a_obj)
                
                cypher_a, p_a = IngestionQueries.merge_activity(
                    destination, activity_id, a["name"], a["lat"], a["lng"], a_obj["category"], a_obj["address"]
                )
                try:
                    execute_write(cypher_a, p_a)
                except Exception as e:
                    print(f"  ⚠️  Failed to cache activity in Neo4j: {e}")
                    
            if fallback_activities:
                activities = fallback_activities
                
    return activities
