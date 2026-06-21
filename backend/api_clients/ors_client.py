"""OpenRouteService client — geocoding (region-biased) and driving directions.

All geocoding is biased to India (`boundary.country=IND`) and prefers populated
places (`layers=locality,region,county`) to avoid mis-resolution like
"Manali" → "Manali, Chennai" that polluted the local KG cache previously.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ORS_API_KEY = os.getenv("ORS_API_KEY")

# Region biasing — comma-separated country codes (ISO 3166-1 alpha-3).
# Override via env if the user wants to plan international trips.
ORS_GEOCODE_COUNTRY = os.getenv("ORS_GEOCODE_COUNTRY", "IND")
ORS_GEOCODE_LAYERS = os.getenv(
    "ORS_GEOCODE_LAYERS",
    "locality,region,county,localadmin,macroregion,borough",
)

# Ranking tier for ORS `layer` field — higher wins. "neighbourhood" is
# deliberately low so e.g. "Manali" (Chennai neighbourhood) doesn't outrank
# Manali, Himachal Pradesh (locality).
_LAYER_TIER = {
    "macroregion":  6,
    "region":       6,
    "county":       5,
    "localadmin":   5,
    "city":         5,
    "locality":     5,
    "borough":      3,
    "neighbourhood": 1,
    "address":      0,
    "venue":        0,
}


class ORSClient:
    BASE_URL = "https://api.openrouteservice.org"

    @classmethod
    def geocode(cls, city_name: str) -> dict | None:
        """Geocode a city / town / region name with population-biased reranking.

        Pelias (which powers ORS geocoding) often returns small Chennai suburbs
        like "Manali" with higher confidence than the actual Himachal Pradesh
        hill town because they're tagged as `neighbourhood` records. We rerank
        results so locality / city / region records outrank neighbourhoods,
        then break ties on Pelias confidence."""
        if not ORS_API_KEY:
            print("  ⚠️  ORS_API_KEY missing — geocode skipped")
            return None
        url = f"{cls.BASE_URL}/geocode/search"
        params = {
            "api_key": ORS_API_KEY,
            "text": city_name,
            "size": 10,                                # broader pool for reranking
            "boundary.country": ORS_GEOCODE_COUNTRY,
            "layers": ORS_GEOCODE_LAYERS,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            features = data.get("features") or []
            if not features:
                print(f"  ⚠️  ORS geocode returned no features for '{city_name}'")
                return None

            needle = city_name.strip().lower()
            scored = []
            for idx, f in enumerate(features):
                props = f.get("properties") or {}
                label = (props.get("label") or "").lower()
                name = (props.get("name") or "").lower()
                layer = (props.get("layer") or "").lower()
                confidence = float(props.get("confidence") or 0.0)
                layer_tier = _LAYER_TIER.get(layer, 2)
                exact = 1 if needle == name else 0
                substr = 1 if (needle in label or needle in name) else 0
                # Tuple order = sort priority (all descending)
                scored.append((exact, layer_tier, substr, confidence, -idx))

            scored.sort(reverse=True)
            best_idx = -scored[0][4]
            best_props = features[best_idx].get("properties") or {}
            coords = features[best_idx]["geometry"]["coordinates"]  # [lng, lat]
            print(f"  ✅ ORS geocode '{city_name}' → "
                  f"{best_props.get('label')} (layer={best_props.get('layer')}, "
                  f"confidence={best_props.get('confidence')})")
            return {"lng": coords[0], "lat": coords[1]}
        except Exception as e:
            print(f"  ⚠️  ORS Geocode error for '{city_name}': {e}")
            return None

    @classmethod
    def get_route(cls, origin_lng: float, origin_lat: float, dest_lng: float, dest_lat: float) -> dict | None:
        """Get driving route between two points, including the full polyline geometry.

        Returns:
            {
              "distance_km": float,
              "duration_hours": float,
              "driving_distance": "<n> km",
              "driving_time": "<n> hours",
              "polyline": [[lat, lng], ...]   # GeoJSON coordinates reordered to lat,lng for Leaflet
            }
        """
        if not ORS_API_KEY:
            return None
        url = f"{cls.BASE_URL}/v2/directions/driving-car/geojson"
        # POST is the recommended way to get geometry without param-length issues.
        body = {
            "coordinates": [[origin_lng, origin_lat], [dest_lng, dest_lat]],
            "instructions": False,
        }
        headers = {
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(url, json=body, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            features = data.get("features") or []
            if not features:
                return None

            feature = features[0]
            properties = feature.get("properties") or {}
            summary = (properties.get("summary") or {})
            distance_km = (summary.get("distance") or 0.0) / 1000.0
            duration_hours = (summary.get("duration") or 0.0) / 3600.0

            # Geometry is GeoJSON coords [[lng,lat],...] — Leaflet wants [[lat,lng],...].
            geom = feature.get("geometry") or {}
            raw_coords = geom.get("coordinates") or []
            polyline = [[lat, lng] for lng, lat in raw_coords]

            return {
                "distance_km": round(distance_km, 2),
                "duration_hours": round(duration_hours, 2),
                "driving_distance": f"{round(distance_km)} km",
                "driving_time": f"{round(duration_hours, 1)} hours",
                "polyline": polyline,
            }
        except Exception as e:
            print(f"  ⚠️  ORS Route error: {e}")
            return None
