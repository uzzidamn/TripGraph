"""Mode planner — decides the primary travel mode and, when flying is the right
call, injects a synthetic flight transport option so the planner actually
builds a flight-based itinerary (instead of an impossible 28-hour drive).

Runs AFTER flights_agent/train_agent (which set state['flights'] advisory) and
BEFORE planner_orchestrator. Mutates state['transport_candidates'] in place.
"""
import re

from backend.agents.state import TripState


def _flight_minutes(advisory: dict) -> int:
    """Parse typical_duration like '2h 30m nonstop' / '1 stop, ~5h' → minutes.
    Falls back to 150 (2.5h) when unparseable."""
    text = (advisory.get("typical_duration") or "").lower()
    h = re.search(r"(\d+)\s*h", text)
    m = re.search(r"(\d+)\s*m", text)
    total = 0
    if h:
        total += int(h.group(1)) * 60
    if m:
        total += int(m.group(1))
    return total or 150


def _fare_per_person(advisory: dict) -> int:
    band = advisory.get("typical_one_way_inr") or [None, None]
    lo, hi = (band + [None, None])[:2]
    vals = [v for v in (lo, hi) if isinstance(v, (int, float))]
    if vals:
        return int(sum(vals) / len(vals))
    return 6000  # sane default domestic one-way


def mode_planner_node(state: TripState) -> dict:
    """If flight is recommended, inject a flight transport option for the
    selected route so the planner can pick it. Returns updated transport_candidates."""
    flights = state.get("flights") or {}
    advisory = flights.get("advisory") or {}
    recommended = advisory.get("recommended_mode")

    if recommended != "fly" or not advisory:
        return {}  # no change

    routes = state.get("route_candidates") or []
    if not routes:
        return {}

    constraints = state.get("extracted_constraints") or {}
    group_size = int(constraints.get("group_size") or 4)
    fare_pp = _fare_per_person(advisory)
    fmin = _flight_minutes(advisory)

    transport = list(state.get("transport_candidates") or [])

    # Inject a flight option for EVERY route candidate so whichever route the
    # planner selects has flight available (duplicate ORS routes were causing
    # the planner to pick a route with no flight and fall back to a drive).
    for route in routes:
        route_id = route.get("route_id")
        if not route_id:
            continue
        tid = f"flight_{route_id}"
        if any(t.get("transport_id") == tid for t in transport):
            continue
        transport.insert(0, {
            "transport_id": tid,
            "route_id": route_id,
            "mode": "flight",
            "tier": constraints.get("hotel_tier") or "comfort",
            "cost_total": fare_pp * 2 * group_size,
            "cost_per_person_roundtrip": fare_pp * 2,
            "capacity": group_size,
            "base_duration_minutes": fmin + 240,
            "flight_minutes": fmin,
            "night_driving_allowed": True,
            "comfort_score": 8,
            "fatigue_score": 2,
            "tags": ["flight", "fast", "recommended"],
            "nearest_airport": advisory.get("nearest_airport", ""),
            "carrier_hints": advisory.get("carrier_hints", []),
        })

    print(f"  ✈️  Mode planner: injected flight transport for {len(routes)} route(s) "
          f"(₹{fare_pp}/pp one-way, {fmin}min air)")
    return {"transport_candidates": transport}
