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
                    places.append({
                        "name": props.get("name", "Unknown Place"),
                        "category": categories.split(".")[0],
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
