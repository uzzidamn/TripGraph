"""Hotel deals client — STUB until a provider key is configured.

This is distinct from `geoapify_client.get_hotels` which only returns hotel
metadata. Deals = current pricing intelligence (price drops, "great rate
for this tier" detection).

Future provider candidates: Booking.com (Rapid), Agoda affiliate, Hotelbeds,
EAN/Expedia partner. Set one of:
    BOOKING_RAPID_API_KEY
    AGODA_PARTNER_API_KEY
    HOTELBEDS_API_KEY
"""
import os
from typing import Optional
from ._stub import stub_unavailable


def _provider_in_use() -> Optional[str]:
    if os.getenv("BOOKING_RAPID_API_KEY"):
        return "booking_rapid"
    if os.getenv("AGODA_PARTNER_API_KEY"):
        return "agoda"
    if os.getenv("HOTELBEDS_API_KEY"):
        return "hotelbeds"
    return None


class HotelDealsClient:
    """Live pricing + deal detection for hotels in a destination."""

    @classmethod
    def find_deals(
        cls,
        destination: str,
        checkin_date: str,            # ISO YYYY-MM-DD
        checkout_date: str,
        rooms: int = 1,
        guests: int = 2,
        tier: Optional[str] = None,   # "budget" | "comfort" | "expedition"
    ) -> dict:
        provider = _provider_in_use()
        if provider is None:
            return stub_unavailable("hotel_deals")

        # ─── Real implementations go here when keys land ─────────────────────
        # Expected `data` shape (frozen):
        #   {
        #     "deals": [
        #       {hotel_id, name, tier, nightly_price_inr,
        #        avg_price_inr, discount_pct, deal_score: 0-100,
        #        is_unusual_drop: bool, valid_until_iso, lat, lng}
        #     ]
        #   }
        return stub_unavailable("hotel_deals", reason=f"NOT_IMPLEMENTED:{provider}")
