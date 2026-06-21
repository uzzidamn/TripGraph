"""
Tool: get_hotels — returns hotels matching destination and optional tier.

Discovery order when the KG has nothing:
    1. Google Places (New) — rich data: real names, ratings, price level → INR estimate
    2. Geoapify — fallback when Google returns nothing / key missing
The fetched hotels are cached into the KG so the next run is instant.
"""
import uuid

from backend.knowledge_graph.connection import execute_query, execute_write
from backend.knowledge_graph.queries import TravelQueries, IngestionQueries
from backend.api_clients.geoapify_client import GeoapifyClient
from backend.api_clients.google_places_client import GooglePlacesClient
from backend.api_clients.ors_client import ORSClient

# Tier → fallback nightly price when the provider gives no price level.
_TIER_PRICE = {"budget": 1800, "comfort": 4500, "expedition": 3000}


def _tier_from_price(price_inr: int | None, default_tier: str) -> str:
    if price_inr is None:
        return default_tier
    if price_inr <= 2500:
        return "budget"
    if price_inr >= 8000:
        return "expedition"
    return "comfort"


def get_hotels(destination: str, tier: str | None = None, *, kg_only: bool = False) -> list[dict]:
    """Returns hotels at a destination, optionally filtered by comfort tier.

    When kg_only=True, never calls external APIs — only reads from the KG.
    """
    cypher, params = TravelQueries.find_hotels(destination, tier)
    try:
        results = execute_query(cypher, params)
        hotels = [r["hotel"] for r in results]
    except Exception:
        hotels = []

    if hotels or kg_only:
        return hotels

    dest_geo = ORSClient.geocode(destination)
    if not dest_geo:
        return hotels

    # 1) Google Places (New) — preferred
    api_hotels = []
    source = "google"
    if GooglePlacesClient.available():
        print(f"  [API] Hotels for {destination} not in KG. Fetching from Google Places...")
        api_hotels = GooglePlacesClient.get_hotels(dest_geo["lat"], dest_geo["lng"], destination, limit=5)

    # 2) Geoapify fallback
    if not api_hotels:
        print(f"  [API] Falling back to Geoapify for hotels at {destination}...")
        source = "geoapify"
        api_hotels = GeoapifyClient.get_hotels(dest_geo["lat"], dest_geo["lng"], limit=4)

    default_tier = tier or "comfort"
    fallback_hotels = []
    for h in api_hotels:
        if not (h.get("name") or "").strip():
            continue
        hotel_id = f"hotel_{uuid.uuid4().hex[:8]}"
        price = h.get("price_inr_estimate") or _TIER_PRICE.get(default_tier, 4500)
        h_tier = _tier_from_price(h.get("price_inr_estimate"), default_tier)
        h_obj = {
            "hotel_id": hotel_id,
            "name": h["name"],
            "lat": h.get("lat"),
            "lng": h.get("lng"),
            "tier": h_tier,
            "price_per_night": price,
            "address": h.get("address", ""),
            "rating": h.get("rating"),
            "rating_count": h.get("rating_count"),
            "photo_name": h.get("photo_name"),
            "editorial_summary": h.get("editorial_summary"),
            "source": source,
            "destination": destination,
        }
        # tier filter (if caller requested one and we could classify)
        if tier and h_tier != tier and h.get("price_inr_estimate") is not None:
            continue
        fallback_hotels.append(h_obj)

        cypher_h, p_h = IngestionQueries.merge_hotel(
            destination, hotel_id, h["name"], h.get("lat"), h.get("lng"),
            h_obj["tier"], price, h_obj["address"],
        )
        try:
            execute_write(cypher_h, p_h)
        except Exception as e:
            print(f"  ⚠️  Failed to cache hotel: {e}")

    return fallback_hotels or hotels
