"""
Tool: get_activities — returns activities matching destination and optional tags.

Discovery order when the KG has nothing:
    1. Google Places (New) — real attraction names + ratings, biased by the
       user's interest (must_include) so e.g. "trekking" surfaces treks.
    2. Geoapify — fallback.
"""
import uuid

from backend.knowledge_graph.connection import execute_query, execute_write
from backend.knowledge_graph.queries import TravelQueries, IngestionQueries
from backend.api_clients.geoapify_client import GeoapifyClient
from backend.api_clients.google_places_client import GooglePlacesClient
from backend.api_clients.ors_client import ORSClient


def get_activities(destination: str, tags: list[str] | None = None, *, kg_only: bool = False) -> list[dict]:
    """Returns activities at a destination, optionally filtered by preference tags.

    When kg_only=True, never calls external APIs — only reads from the KG.
    """
    cypher, params = TravelQueries.find_activities(destination, tags)
    try:
        results = execute_query(cypher, params)
        activities = [r["activity"] for r in results]
    except Exception:
        activities = []

    # Drop any activity without a real name — they render as "Unknown Place" pins
    activities = [a for a in activities if (a.get("name") or "").strip()]

    if activities or kg_only:
        return activities

    dest_geo = ORSClient.geocode(destination)
    if not dest_geo:
        return activities

    interest = (tags or [None])[0]  # bias the search toward the user's top interest

    # 1) Google Places (New) — preferred
    api_activities = []
    if GooglePlacesClient.available():
        print(f"  [API] Activities for {destination} not in KG. Fetching from Google Places...")
        api_activities = GooglePlacesClient.get_activities(
            dest_geo["lat"], dest_geo["lng"], destination, interest=interest, limit=6)

    # 2) Geoapify fallback
    if not api_activities:
        print(f"  [API] Falling back to Geoapify for activities at {destination}...")
        api_activities = GeoapifyClient.get_activities(dest_geo["lat"], dest_geo["lng"], limit=5)

    fallback_activities = []
    for a in api_activities:
        if not (a.get("name") or "").strip():
            continue
        activity_id = f"activity_{uuid.uuid4().hex[:8]}"
        a_tags = list(dict.fromkeys(
            (a.get("tags") or [a.get("category", "attraction")]) + (tags or [])
        ))
        a_obj = {
            "activity_id": activity_id,
            "name": a["name"],
            "lat": a.get("lat"),
            "lng": a.get("lng"),
            "category": a.get("category", "attraction"),
            "address": a.get("address", ""),
            "rating": a.get("rating"),
            "photo_name": a.get("photo_name"),
            "editorial_summary": a.get("editorial_summary"),
            "tags": a_tags,
            "destination": destination,
        }
        fallback_activities.append(a_obj)

        cypher_a, p_a = IngestionQueries.merge_activity(
            destination, activity_id, a["name"], a.get("lat"), a.get("lng"),
            a_obj["category"], a_obj["address"]
        )
        try:
            execute_write(cypher_a, p_a)
        except Exception as e:
            print(f"  ⚠️  Failed to cache activity: {e}")

    return fallback_activities or activities
