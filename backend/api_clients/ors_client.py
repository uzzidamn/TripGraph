import os
import requests
from dotenv import load_dotenv

load_dotenv()

ORS_API_KEY = os.getenv("ORS_API_KEY")

class ORSClient:
    BASE_URL = "https://api.openrouteservice.org"

    @classmethod
    def geocode(cls, city_name: str) -> dict | None:
        """Get lat/lng for a city name."""
        url = f"{cls.BASE_URL}/geocode/search"
        params = {
            "api_key": ORS_API_KEY,
            "text": city_name,
            "size": 1
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("features"):
                coords = data["features"][0]["geometry"]["coordinates"] # [lng, lat]
                return {"lng": coords[0], "lat": coords[1]}
        except Exception as e:
            print(f"ORS Geocode error: {e}")
        return None

    @classmethod
    def get_route(cls, origin_lng: float, origin_lat: float, dest_lng: float, dest_lat: float) -> dict | None:
        """Get driving route details between two points."""
        url = f"{cls.BASE_URL}/v2/directions/driving-car"
        params = {
            "api_key": ORS_API_KEY,
            "start": f"{origin_lng},{origin_lat}",
            "end": f"{dest_lng},{dest_lat}"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "features" in data and len(data["features"]) > 0:
                properties = data["features"][0]["properties"]
                summary = properties["summary"]
                distance_km = summary["distance"] / 1000.0
                duration_hours = summary["duration"] / 3600.0
                return {
                    "distance_km": round(distance_km, 2),
                    "duration_hours": round(duration_hours, 2),
                    "driving_distance": f"{round(distance_km)} km",
                    "driving_time": f"{round(duration_hours, 1)} hours"
                }
        except Exception as e:
            print(f"ORS Route error: {e}")
        return None
