"""Google Routes API client — Compute Route Matrix.

We use this to give the Itinerary Architect a *real* travel-time matrix between
candidate stops so it can cluster the day geographically (no more backtracking
across the city). Free tier is small, so callers cap N stops and cache per trip.

API:  POST https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix
Auth: X-Goog-Api-Key header (GOOGLE_MAPS_API_KEY)
FieldMask: only the fields we actually use, to stay in the cheap billing tier.
"""
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
_FIELD_MASK = "originIndex,destinationIndex,duration,distanceMeters,status"


class GoogleRoutesClient:
    @classmethod
    def available(cls) -> bool:
        return bool(GOOGLE_MAPS_API_KEY)

    @classmethod
    def distance_matrix(cls, stops: list[dict], travel_mode: str = "DRIVE",
                        max_stops: int = 10) -> Optional[list[list[dict]]]:
        """Compute pairwise driving time/distance for up to `max_stops` stops.

        Args:
            stops: list of {lat, lng} (and optionally {name} for logging).
            travel_mode: "DRIVE" | "WALK" | "BICYCLE" | "TRANSIT" | "TWO_WHEELER".
            max_stops: hard cap to control billing (NxN pairs).

        Returns:
            matrix[i][j] = {"minutes": int, "km": float} or None on error.
        """
        if not GOOGLE_MAPS_API_KEY:
            return None
        stops = [s for s in (stops or []) if s.get("lat") is not None and s.get("lng") is not None]
        stops = stops[:max_stops]
        n = len(stops)
        if n < 2:
            return None

        waypoints = [
            {"waypoint": {"location": {"latLng": {"latitude": s["lat"], "longitude": s["lng"]}}}}
            for s in stops
        ]
        body = {
            "origins": waypoints,
            "destinations": waypoints,
            "travelMode": travel_mode,
            "routingPreference": "TRAFFIC_AWARE" if travel_mode == "DRIVE" else "ROUTING_PREFERENCE_UNSPECIFIED",
        }
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": _FIELD_MASK,
        }
        try:
            r = requests.post(_URL, json=body, headers=headers, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  ⚠️  Routes matrix failed: {e}")
            return None

        # Response is a flat list of {originIndex, destinationIndex, duration, distanceMeters}
        matrix = [[{"minutes": 0, "km": 0.0} for _ in range(n)] for _ in range(n)]
        rows = data if isinstance(data, list) else data.get("rows", [])
        for cell in rows:
            i = cell.get("originIndex")
            j = cell.get("destinationIndex")
            if i is None or j is None:
                continue
            if cell.get("status", {}).get("code", 0) != 0:
                continue
            # duration arrives as "1234s" — strip the trailing s.
            dur = cell.get("duration", "0s")
            try:
                secs = int(str(dur).rstrip("s"))
            except ValueError:
                secs = 0
            km = float(cell.get("distanceMeters") or 0) / 1000.0
            matrix[i][j] = {"minutes": round(secs / 60.0), "km": round(km, 1)}
        return matrix
