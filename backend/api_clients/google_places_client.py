"""Google Places API (New) client — Text Search for hotels & activities.

Returns richer data than Geoapify (ratings, user-rating counts, price level,
real display names) which lets the planner price hotels sensibly and rank by
quality. Free-tier aware: callers cache aggressively and cap calls per trip.

Endpoint: POST https://places.googleapis.com/v1/places:searchText
Auth:     X-Goog-Api-Key header (GOOGLE_MAPS_API_KEY)
FieldMask limits which fields are billed — we request only what we render.

Price level mapping → approximate INR/night for hotels (used when the planner
needs a number; clearly an estimate):
    PRICE_LEVEL_INEXPENSIVE  → 2000
    PRICE_LEVEL_MODERATE     → 4500
    PRICE_LEVEL_EXPENSIVE    → 8000
    PRICE_LEVEL_VERY_EXPENSIVE → 15000
"""
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

_PRICE_TO_INR = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 2000,
    "PRICE_LEVEL_MODERATE": 4500,
    "PRICE_LEVEL_EXPENSIVE": 8000,
    "PRICE_LEVEL_VERY_EXPENSIVE": 15000,
}

_FIELD_MASK = ",".join([
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.priceLevel",
    "places.priceRange",
    "places.types",
    "places.primaryType",
    "places.photos",
    "places.editorialSummary",
    "places.regularOpeningHours",
    "places.websiteUri",
])


class GooglePlacesClient:
    @classmethod
    def available(cls) -> bool:
        return bool(GOOGLE_MAPS_API_KEY)

    @classmethod
    def _search(cls, text_query: str, lat: float, lng: float,
                radius_m: int = 6000, limit: int = 5) -> list[dict]:
        if not GOOGLE_MAPS_API_KEY:
            return []
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": _FIELD_MASK,
        }
        body = {
            "textQuery": text_query,
            "maxResultCount": limit,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": float(radius_m),
                }
            },
        }
        try:
            r = requests.post(_SEARCH_URL, json=body, headers=headers, timeout=12)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  ⚠️  Google Places error for {text_query!r}: {e}")
            return []

        out = []
        for p in (data.get("places") or [])[:limit]:
            name = ((p.get("displayName") or {}).get("text") or "").strip()
            if not name:
                continue
            loc = p.get("location") or {}
            types = p.get("types") or []
            tags = []
            for t in types:
                for part in str(t).split("_"):
                    if part and part not in tags and part not in ("point", "of", "interest", "establishment"):
                        tags.append(part)
            price_level = p.get("priceLevel")
            # First photo's resource name → the frontend builds the media URL.
            photos = p.get("photos") or []
            photo_name = photos[0].get("name") if photos else None
            editorial = (p.get("editorialSummary") or {}).get("text")

            # Compress opening hours into a 7-line array the architect prompt
            # can read cheaply ("Mon: 9:00–17:00"). Skip when unavailable.
            hours = None
            roh = p.get("regularOpeningHours") or {}
            weekday_texts = roh.get("weekdayDescriptions")
            if isinstance(weekday_texts, list) and weekday_texts:
                hours = weekday_texts

            # Real price range (per-person, currency-tagged). Falls back to
            # the price-level → INR estimate when Google doesn't supply a range.
            price_range = None
            pr = p.get("priceRange")
            if pr:
                lo = (pr.get("startPrice") or {}).get("units")
                hi = (pr.get("endPrice") or {}).get("units")
                cur = (pr.get("startPrice") or {}).get("currencyCode") or "INR"
                if lo is not None or hi is not None:
                    price_range = {"low": lo, "high": hi, "currency": cur}

            out.append({
                "name": name,
                "lat": loc.get("latitude"),
                "lng": loc.get("longitude"),
                "address": p.get("formattedAddress", ""),
                "rating": p.get("rating"),
                "rating_count": p.get("userRatingCount"),
                "price_level": price_level,
                "price_inr_estimate": _PRICE_TO_INR.get(price_level),
                "price_range": price_range,
                "category": (p.get("primaryType") or (types[0] if types else "place")),
                "tags": tags[:8],
                "photo_name": photo_name,
                "editorial_summary": editorial,
                "opening_hours": hours,
                "website": p.get("websiteUri"),
            })
        return out

    @classmethod
    def get_hotels(cls, lat: float, lng: float, destination: str = "", limit: int = 5) -> list[dict]:
        q = f"hotels in {destination}".strip() or "hotels"
        return cls._search(q, lat, lng, radius_m=8000, limit=limit)

    @classmethod
    def get_activities(cls, lat: float, lng: float, destination: str = "",
                       interest: Optional[str] = None, limit: int = 6) -> list[dict]:
        base = f"{interest} in {destination}" if interest else f"top things to do in {destination}"
        return cls._search(base.strip() or "tourist attractions", lat, lng, radius_m=12000, limit=limit)
