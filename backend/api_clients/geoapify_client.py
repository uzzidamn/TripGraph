import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

class GeoapifyClient:
    BASE_URL = "https://api.geoapify.com/v2/places"

    @classmethod
    def get_places(cls, lat: float, lng: float, categories: str, radius_meters: int = 5000, limit: int = 5) -> list[dict]:
        """Fetch places around a specific lat/lng from Geoapify."""
        params = {
            "categories": categories,
            "filter": f"circle:{lng},{lat},{radius_meters}",
            "limit": limit,
            "apiKey": GEOAPIFY_API_KEY
        }
        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            places = []
            if "features" in data:
                for feature in data["features"]:
                    props = feature["properties"]
                    # Skip features without a real name — they show up in the UI as
                    # "Unknown Place" pins floating in the middle of nowhere otherwise.
                    raw_name = (props.get("name") or "").strip()
                    if not raw_name:
                        # Fall back to a street/address if Geoapify provides one,
                        # else drop the entry entirely.
                        fallback = (props.get("street") or props.get("address_line1") or "").strip()
                        if not fallback or len(fallback) < 3:
                            continue
                        raw_name = fallback
                    # Geoapify returns a `categories` array like
                    #   ["tourism", "tourism.attraction", "tourism.attraction.themed_park"]
                    # Flatten that into a clean tag list (e.g. ["tourism", "attraction", "themed_park"])
                    # and de-dup, preserving order.
                    raw_cats = props.get("categories") or [categories]
                    tags: list[str] = []
                    seen = set()
                    for raw in raw_cats:
                        for part in str(raw).split("."):
                            part = part.strip()
                            if part and part not in seen:
                                seen.add(part)
                                tags.append(part)
                    primary = categories.split(".")[0]
                    places.append({
                        "name": raw_name,
                        "category": primary,
                        "tags": tags,
                        "lat": props.get("lat"),
                        "lng": props.get("lon"),
                        "address": props.get("address_line2", "")
                    })
            return places
        except Exception as e:
            print(f"Geoapify Places error: {e}")
            return []
        
    @classmethod
    def get_hotels(cls, lat: float, lng: float, limit: int = 5) -> list[dict]:
        """Fetch hotels using Geoapify as an alternative to Amadeus."""
        return cls.get_places(lat, lng, categories="accommodation.hotel", limit=limit)

    @classmethod
    def get_activities(cls, lat: float, lng: float, limit: int = 5) -> list[dict]:
        """Fetch tourist attractions."""
        return cls.get_places(lat, lng, categories="tourism.attraction", limit=limit)
