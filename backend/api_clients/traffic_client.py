"""Traffic conditions client — STUB until a provider key is configured.

Reports current + historical typical traffic for a route, so the planner can
warn about predictable congestion windows (e.g. Friday-evening Delhi exit).

Future provider candidates: TomTom Traffic Stats, HERE Traffic, Google Roads.
Set one of:
    TOMTOM_API_KEY
    HERE_API_KEY
    GOOGLE_MAPS_API_KEY
"""
import os
from typing import Optional
from ._stub import stub_unavailable


def _provider_in_use() -> Optional[str]:
    if os.getenv("TOMTOM_API_KEY"):
        return "tomtom"
    if os.getenv("HERE_API_KEY"):
        return "here"
    if os.getenv("GOOGLE_MAPS_API_KEY"):
        return "google"
    return None


class TrafficClient:
    """Look up current and historical typical traffic on a route segment."""

    @classmethod
    def conditions(
        cls,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        depart_iso: Optional[str] = None,   # ISO 8601 datetime
    ) -> dict:
        provider = _provider_in_use()
        if provider is None:
            return stub_unavailable("traffic")

        # ─── Real implementations go here when keys land ─────────────────────
        # Expected `data` shape (frozen):
        #   {
        #     "current_delay_minutes": int,
        #     "expected_delay_minutes": int,
        #     "level": "free_flow" | "light" | "moderate" | "heavy" | "standstill",
        #     "historical_typical_minutes": int,
        #     "advice": "Leave 30 minutes earlier to beat the typical 4pm slowdown"
        #   }
        return stub_unavailable("traffic", reason=f"NOT_IMPLEMENTED:{provider}")
