"""
Tool: get_hotels — returns hotels matching destination and optional tier.
"""
import uuid
from backend.knowledge_graph.connection import execute_query, execute_write
from backend.knowledge_graph.queries import TravelQueries, IngestionQueries
from backend.api_clients.geoapify_client import GeoapifyClient
from backend.api_clients.ors_client import ORSClient

def get_hotels(destination: str, tier: str | None = None) -> list[dict]:
    """
    Returns hotels at a destination, optionally filtered by comfort tier.
    Falls back to Geoapify API if none are found in the Knowledge Graph.
    """
    cypher, params = TravelQueries.find_hotels(destination, tier)
    try:
        results = execute_query(cypher, params)
        hotels = [r["hotel"] for r in results]
    except Exception:
        hotels = []
        
    if not hotels:
        print(f"  [API] Hotels for {destination} not in KG. Fetching from Geoapify...")
        dest_geo = ORSClient.geocode(destination)
        if dest_geo:
            api_hotels = GeoapifyClient.get_hotels(dest_geo['lat'], dest_geo['lng'], limit=3)
            fallback_hotels = []
            for h in api_hotels:
                hotel_id = f"hotel_{uuid.uuid4().hex[:8]}"
                h_obj = {
                    "hotel_id": hotel_id,
                    "name": h["name"],
                    "lat": h["lat"],
                    "lng": h["lng"],
                    "tier": tier or "comfort",
                    "price_per_night": 5000,
                    "address": h.get("address", ""),
                    "destination": destination
                }
                fallback_hotels.append(h_obj)
                
                cypher_h, p_h = IngestionQueries.merge_hotel(
                    destination, hotel_id, h["name"], h["lat"], h["lng"], h_obj["tier"], h_obj["price_per_night"], h_obj["address"]
                )
                try:
                    execute_write(cypher_h, p_h)
                except Exception as e:
                    print(f"  ⚠️  Failed to cache hotel in Neo4j: {e}")
                    
            if fallback_hotels:
                hotels = fallback_hotels
                
    return hotels
