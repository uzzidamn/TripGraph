"""OpenWeatherMap client — current weather + 3-day forecast.

Uses the free 5-day / 3-hour forecast endpoint (`/forecast`) and condenses it
into per-day summaries the planner can render on timeline cards.
"""
import os
from collections import defaultdict
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")


class OpenWeatherMapClient:
    BASE_URL = "https://api.openweathermap.org/data/2.5"

    @classmethod
    def get_weather(cls, lat: float, lng: float) -> dict | None:
        """Fetch current weather for a specific lat/lng."""
        if not OPENWEATHERMAP_API_KEY:
            return None
        url = f"{cls.BASE_URL}/weather"
        params = {"lat": lat, "lon": lng, "appid": OPENWEATHERMAP_API_KEY, "units": "metric"}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "temp": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "summary": (data["weather"][0]["main"] or "").lower(),  # e.g. "rain","clouds"
            }
        except Exception as e:
            print(f"  ⚠️  OpenWeatherMap current weather error: {e}")
            return None

    @classmethod
    def get_forecast(cls, lat: float, lng: float, days: int = 7) -> dict | None:
        """Fetch a per-day condensed forecast.

        Tries One Call API 3.0 first (gives 8 days of daily data). Falls back
        to the legacy 5-day/3-hour endpoint when One Call isn't subscribed.

        Returns:
            {
              "<YYYY-MM-DD>": {
                "temp_min": float, "temp_max": float,
                "description": "...",
                "summary": "rain|clouds|clear|...",
                "pop_max": float
              }
            }
        """
        if not OPENWEATHERMAP_API_KEY:
            return None

        out = cls._fetch_onecall(lat, lng, days)
        if out:
            return out
        # One Call 3.0 not subscribed on this key — fall back to /forecast
        return cls._fetch_5day(lat, lng, min(days, 5))

    @classmethod
    def _fetch_onecall(cls, lat: float, lng: float, days: int) -> dict | None:
        """One Call API 3.0 — 8-day daily forecast in a single call."""
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": lat, "lon": lng,
            "appid": OPENWEATHERMAP_API_KEY,
            "units": "metric",
            "exclude": "minutely,hourly,alerts,current",
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code in (401, 403, 429):
                # Key not subscribed to One Call 3.0
                return None
            response.raise_for_status()
            data = response.json()
            daily = data.get("daily") or []
            if not daily:
                return None
            out: dict[str, dict] = {}
            for d in daily[:days]:
                ts = d.get("dt")
                if not ts:
                    continue
                day = datetime.utcfromtimestamp(ts).date().isoformat()
                w = (d.get("weather") or [{}])[0]
                temp = d.get("temp") or {}
                out[day] = {
                    "temp_min": round(temp.get("min", 0), 1),
                    "temp_max": round(temp.get("max", 0), 1),
                    "description": w.get("description", ""),
                    "summary": (w.get("main") or "").lower(),
                    "pop_max": round(d.get("pop", 0.0), 2),
                }
            return out
        except Exception:
            return None

    @classmethod
    def _fetch_5day(cls, lat: float, lng: float, days: int) -> dict | None:
        """Legacy 5-day / 3-hour forecast — condense per day."""
        url = f"{cls.BASE_URL}/forecast"
        params = {"lat": lat, "lon": lng, "appid": OPENWEATHERMAP_API_KEY, "units": "metric"}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            slots = data.get("list") or []
            if not slots:
                return None

            by_day: dict[str, list] = defaultdict(list)
            for s in slots:
                ts = s.get("dt")
                if not ts:
                    continue
                day = datetime.utcfromtimestamp(ts).date().isoformat()
                by_day[day].append(s)

            out: dict[str, dict] = {}
            for day in sorted(by_day.keys())[:days]:
                slots_for_day = by_day[day]
                temps = [s["main"]["temp"] for s in slots_for_day if "main" in s]
                pops = [s.get("pop", 0.0) for s in slots_for_day]
                midday = min(slots_for_day, key=lambda s: abs(
                    datetime.utcfromtimestamp(s["dt"]).hour - 13
                ))
                w = (midday.get("weather") or [{}])[0]
                out[day] = {
                    "temp_min": round(min(temps), 1) if temps else None,
                    "temp_max": round(max(temps), 1) if temps else None,
                    "description": w.get("description", ""),
                    "summary": (w.get("main") or "").lower(),
                    "pop_max": round(max(pops), 2) if pops else 0.0,
                }
            return out
        except Exception as e:
            print(f"  ⚠️  OpenWeatherMap forecast error: {e}")
            return None
