"""Flights agent — surfaces flight options/advisory for trips that involve air travel.

Trigger rules (in priority order):
  1. User explicitly asked for flights → always advise.
  2. User said "by road" / "self drive" / "by train" → suppress (they've chosen a mode).
  3. Great-circle distance origin→destination >= FLIGHT_THRESHOLD_KM (default 500)
     OR drive duration >= LONG_DRIVE_HOURS → advise.

Data sources (no flight API yet):
  - LLM general knowledge produces a typical price band, carriers, book-ahead note.
  - When a real flight provider key lands, FlightsClient.search() supersedes the advisory.

Output (frozen shape — UI renders either case identically):
    {
      "available": bool,            # real provider data?
      "advisory_available": bool,
      "reason": str,
      "provider": str,
      "data": dict | None,
      "advisory": {
        "recommended_mode": "fly" | "drive" | "train" | "either",
        "typical_one_way_inr": [low, high],
        "typical_duration": str,            # e.g. "2h 15m nonstop"
        "carrier_hints": [str, ...],
        "nearest_airport": str,             # e.g. "Dimapur (DMU)"
        "book_ahead_note": str,
        "rationale": str,
      } | None
    }
"""
import json
import math
from datetime import date, timedelta

from langchain_core.messages import HumanMessage, SystemMessage

from backend.api_clients.flights_client import FlightsClient
from backend.api_clients.duckduckgo_search_client import DuckDuckGoSearchClient
from backend.api_clients.ors_client import ORSClient
from backend.agents.llm_client import extract_text_content, get_llm, strip_code_fences, loads_loose
from backend.agents.state import TripState

FLIGHT_THRESHOLD_KM = 500
LONG_DRIVE_HOURS = 9

# Phrases that mean the user has committed to a ground mode → don't push flights.
_GROUND_ONLY_TERMS = (
    "by road", "road trip", "self drive", "self-drive", "drive there",
    "by train", "by rail", "take the train", "overnight train", "road only",
)


_ADVISORY_SYSTEM = """You are a travel-mode advisor for TripGraph AI with strong knowledge of Indian domestic aviation.

Given a trip's origin city, destination, drive distance/hours, and departure date,
decide whether flying makes sense and produce a realistic price band, the nearest
usable airport to the destination, likely carriers, typical flight duration, and a
book-ahead note — all from your general knowledge.

OUTPUT RULES:
- Output ONLY one valid JSON object. No markdown, no fences.
- recommended_mode ∈ {"fly","drive","train","either"}.
- typical_one_way_inr is [low, high] INR. Use realistic 2024-era domestic fares. [null,null] if truly unknown.
- nearest_airport: the closest commercial airport to the DESTINATION with its IATA code, e.g. "Dimapur (DMU)". "" if none.
- carrier_hints: 1-3 Indian carriers likely on this route (IndiGo, Air India, Vistara, Akasa, SpiceJet). [] if uncertain.
- typical_duration: e.g. "2h 20m nonstop" or "1 stop, ~5h".
- book_ahead_note: one sentence on price sensitivity for a 3-4 day advance booking.
- rationale: one sentence why.

SCHEMA:
{
  "recommended_mode": "...",
  "typical_one_way_inr": [int_or_null, int_or_null],
  "typical_duration": "...",
  "nearest_airport": "...",
  "carrier_hints": ["..."],
  "book_ahead_note": "...",
  "rationale": "..."
}
"""

_ADVISORY_HUMAN = """Trip:
- Origin: {origin}
- Destination: {destination}
- Approx straight-line distance: {distance_km} km
- Approx drive duration: {duration_h:.1f} hours
- Departure: {depart_date}
- Group size: {group_size}

Live web snippets (use these to anchor typical_one_way_inr — if numbers
appear in these snippets they are MORE reliable than your training data):
{snippets}

Generate the advisory JSON."""


def _haversine_km(lat1, lng1, lat2, lng2):
    try:
        lat1, lng1, lat2, lng2 = map(float, (lat1, lng1, lat2, lng2))
    except (TypeError, ValueError):
        return 0.0
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _ground_only(constraints: dict) -> bool:
    blob = json.dumps(constraints, default=str).lower()
    transport_pref = [t.lower() for t in (constraints.get("transport_preference") or [])]
    if any(t in transport_pref for t in ("self_drive", "cab_with_driver", "road", "train", "rail", "bike")):
        return True
    return any(term in blob for term in _GROUND_ONLY_TERMS)


def _wants_flight(constraints: dict) -> bool:
    transport_pref = [t.lower() for t in (constraints.get("transport_preference") or [])]
    if any(t in transport_pref for t in ("flight", "flights", "air", "plane", "fly")):
        return True
    blob = json.dumps(constraints, default=str).lower()
    return any(term in blob for term in ("by flight", "by air", "fly there", "take a flight"))


def _resolve_distance(constraints: dict, route: dict, state: TripState) -> tuple[float, float]:
    """Return (distance_km, duration_hours), computing from coords if route lacks them."""
    d_km = 0.0
    d_h = 0.0
    try:
        d_km = float(route.get("distance_km") or 0)
        d_h = float(route.get("duration_hours") or (route.get("base_drive_minutes") or 0) / 60.0)
    except (TypeError, ValueError):
        pass

    if d_km >= 1:
        return d_km, d_h

    # Compute great-circle from origin/destination coords.
    dest_lat = route.get("dest_lat")
    dest_lng = route.get("dest_lng")
    if dest_lat is None or dest_lng is None:
        # try map_points
        for p in (state.get("map_points") or []):
            if p.get("type") == "destination":
                dest_lat, dest_lng = p.get("lat"), p.get("lng")
                break

    origin_lat = route.get("origin_lat")
    origin_lng = route.get("origin_lng")
    if (origin_lat is None or origin_lng is None):
        for p in (state.get("map_points") or []):
            if p.get("type") == "origin":
                origin_lat, origin_lng = p.get("lat"), p.get("lng")
                break
    if (origin_lat is None or origin_lng is None) and constraints.get("origin"):
        geo = ORSClient.geocode(constraints["origin"])
        if geo:
            origin_lat, origin_lng = geo["lat"], geo["lng"]

    if all(v is not None for v in (origin_lat, origin_lng, dest_lat, dest_lng)):
        d_km = _haversine_km(origin_lat, origin_lng, dest_lat, dest_lng)
        if d_h < 0.1:
            d_h = d_km / 45.0  # ~45 km/h effective for Indian highways/hills
    return d_km, d_h


def _fetch_price_snippets(origin: str, destination: str) -> str:
    """Pull 3 DDG snippets so the LLM can ground typical_one_way_inr in real data."""
    try:
        query = f"flight {origin} to {destination} price IndiGo Air India"
        snips = DuckDuckGoSearchClient.snippets(query, max_results=3)
        if not snips:
            return "(no live snippets available)"
        return "\n".join(f"- {s['title']}: {s['snippet'][:200]}" for s in snips)
    except Exception as e:
        print(f"  ⚠️  DDG price scrape failed: {e}")
        return "(snippet fetch failed)"


def _llm_advisory(origin, destination, distance_km, duration_h, depart_date, group_size):
    snippets_text = _fetch_price_snippets(origin, destination)
    try:
        llm = get_llm()
        resp = llm.invoke([
            SystemMessage(content=_ADVISORY_SYSTEM),
            HumanMessage(content=_ADVISORY_HUMAN.format(
                origin=origin, destination=destination,
                distance_km=int(distance_km), duration_h=duration_h,
                depart_date=depart_date, group_size=group_size,
                snippets=snippets_text,
            )),
        ])
        raw = extract_text_content(resp.content).strip()
        raw = strip_code_fences(raw)
        p = loads_loose(raw)
        return {
            "recommended_mode": p.get("recommended_mode") or "either",
            "typical_one_way_inr": p.get("typical_one_way_inr") or [None, None],
            "typical_duration": p.get("typical_duration") or "",
            "nearest_airport": p.get("nearest_airport") or "",
            "carrier_hints": p.get("carrier_hints") or [],
            "book_ahead_note": p.get("book_ahead_note") or "",
            "rationale": p.get("rationale") or "",
        }
    except Exception as e:
        print(f"  ⚠️  flight advisory LLM failed ({e})")
        return None


def flights_agent_node(state: TripState) -> dict:
    constraints = state.get("extracted_constraints") or {}
    selected = state.get("selected_itinerary") or {}
    route = selected.get("route") or {}
    if not route:
        routes = state.get("route_candidates") or []
        if routes:
            route = max(routes, key=lambda r: float(r.get("distance_km") or 0))

    none_result = {
        "available": False, "advisory_available": False,
        "reason": "NOT_NEEDED", "provider": "none", "data": None, "advisory": None,
    }

    wants = _wants_flight(constraints)
    if not wants and _ground_only(constraints):
        print("  [Flights] user committed to a ground mode — suppressing flight advisory")
        return {"flights": none_result}

    distance_km, duration_h = _resolve_distance(constraints, route, state)
    trigger = wants or distance_km >= FLIGHT_THRESHOLD_KM or duration_h >= LONG_DRIVE_HOURS
    print(f"  [Flights] distance={distance_km:.0f}km duration={duration_h:.1f}h wants={wants} → trigger={trigger}")
    if not trigger:
        return {"flights": none_result}

    depart_date = constraints.get("depart_date") or (date.today() + timedelta(days=14)).isoformat()
    origin = constraints.get("origin") or route.get("origin") or "Delhi"
    destination = constraints.get("destination") or route.get("destination") or ""
    group_size = int(constraints.get("group_size") or 1)

    live = FlightsClient.search(
        origin=origin, destination=destination,
        depart_date=depart_date, return_date=constraints.get("return_date"),
        passengers=group_size,
    )
    advisory = _llm_advisory(origin, destination, distance_km, duration_h, depart_date, group_size)

    return {"flights": {
        "available": bool(live.get("available")),
        "advisory_available": bool(advisory),
        "reason": live.get("reason"),
        "provider": live.get("provider"),
        "data": live.get("data"),
        "advisory": advisory,
    }}
