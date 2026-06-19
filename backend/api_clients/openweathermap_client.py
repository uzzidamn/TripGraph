import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

class OpenWeatherMapClient:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    @classmethod
    def get_weather(cls, lat: float, lng: float) -> dict | None:
        """Fetch current weather for a specific lat/lng."""
        params = {
            "lat": lat,
            "lon": lng,
            "appid": OPENWEATHERMAP_API_KEY,
            "units": "metric"
        }
        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "temp": data["main"]["temp"],
                "description": data["weather"][0]["description"]
            }
        except Exception as e:
            print(f"OpenWeatherMap error: {e}")
            return None
