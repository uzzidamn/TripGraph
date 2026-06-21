"""Flights search client — STUB until a provider key is configured.

Future provider candidates: Skyscanner Rapid, Amadeus self-service, Duffel, Kiwi.

Set ONE of these env vars to enable:
    SKYSCANNER_RAPID_API_KEY
    AMADEUS_API_KEY  (+ AMADEUS_API_SECRET)
    DUFFEL_API_KEY

Until then every call returns an unavailable stub so the planner can call
unconditionally and the UI silently no-ops the flights panel.
"""
import os
from typing import Optional
from ._stub import stub_unavailable


def _provider_in_use() -> Optional[str]:
    if os.getenv("SKYSCANNER_RAPID_API_KEY"):
        return "skyscanner"
    if os.getenv("AMADEUS_API_KEY"):
        return "amadeus"
    if os.getenv("DUFFEL_API_KEY"):
        return "duffel"
    return None


class FlightsClient:
    """Search flights between cities/airports for a date window."""

    @classmethod
    def search(
        cls,
        origin: str,
        destination: str,
        depart_date: str,           # ISO YYYY-MM-DD
        return_date: Optional[str] = None,
        passengers: int = 1,
        cabin: str = "economy",
    ) -> dict:
        provider = _provider_in_use()
        if provider is None:
            return stub_unavailable("flights")

        # ─── Real implementations go here when keys land ─────────────────────
        # Expected `data` shape (frozen — UI relies on this):
        #   {
        #     "outbound": [{carrier, flight_no, depart_iso, arrive_iso,
        #                   origin_iata, dest_iata, stops, fare_inr, fare_class}, ...],
        #     "return":   [...] | None,
        #     "deal_flag": "below_average" | "average" | "above_average" | "much_higher",
        #     "avg_price_inr": int,
        #     "current_price_inr": int,
        #   }
        return stub_unavailable("flights", reason=f"NOT_IMPLEMENTED:{provider}")
