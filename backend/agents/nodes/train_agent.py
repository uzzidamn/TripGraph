"""Train agent — surfaces rail options + the "nearest railhead" insight.

Especially useful for remote destinations (e.g. Dzukou Valley → nearest railhead
is Dimapur). Combines:
  - LLM rail knowledge: nearest major railhead to the destination, typical
    trains from the origin region, approximate fare/duration, and the
    onward-transfer note (railhead → final destination).
  - RailRadar live data (best-effort): actual trains between the resolved
    railhead stations, when the API responds.

Triggers on the same long-distance heuristic as flights, OR when the user
mentions train/rail. Silent for short road trips.

Output: state['trains'] = {
  "available": bool,                 # live RailRadar data present?
  "advisory_available": bool,
  "advisory": {
     "nearest_railhead": str,        # e.g. "Dimapur (DMV)"
     "onward_note": str,             # railhead → destination transfer
     "typical_trains": [str, ...],   # named trains from origin region
     "typical_fare_inr": [low, high],
     "typical_duration": str,
     "rationale": str,
  } | None,
  "live_trains": [ {train_no, train_name, departs, arrives, duration}, ... ] | None
}
"""
import json

from langchain_core.messages import HumanMessage, SystemMessage

from backend.api_clients.railradar_client import RailRadarClient
from backend.agents.llm_client import extract_text_content, get_llm, strip_code_fences, loads_loose
from backend.agents.state import TripState

# Reuse the flight distance helpers to decide relevance.
from backend.agents.nodes.flights_agent import _resolve_distance, FLIGHT_THRESHOLD_KM, LONG_DRIVE_HOURS

_SYSTEM = """You are an Indian Railways advisor for TripGraph AI.

Given a trip origin city and a (possibly remote) destination, identify the nearest
usable railhead to the DESTINATION, typical named trains from the origin region to
that railhead, an approximate sleeper/3AC fare band, typical journey duration, and
the onward transfer from railhead to the final destination.

OUTPUT RULES:
- Output ONLY one valid JSON object. No markdown.
- nearest_railhead: nearest major station to the destination with code, e.g. "Dimapur (DMV)".
- onward_note: one sentence on how to get from the railhead to the destination (shared taxi, bus, drive time).
- typical_trains: 1-3 well-known trains from the origin region to that railhead (names). [] if unsure.
- typical_fare_inr: [low, high] for a typical class. [null,null] if unknown.
- typical_duration: e.g. "~30h" or "26-32h".
- rationale: one sentence.

SCHEMA:
{
  "nearest_railhead": "...",
  "onward_note": "...",
  "typical_trains": ["..."],
  "typical_fare_inr": [int_or_null, int_or_null],
  "typical_duration": "...",
  "rationale": "..."
}
"""

_HUMAN = """Trip:
- Origin: {origin}
- Destination: {destination}
- Approx distance: {distance_km} km

Generate the rail advisory JSON."""


def _train_relevant(constraints: dict, distance_km: float, duration_h: float) -> bool:
    transport_pref = [t.lower() for t in (constraints.get("transport_preference") or [])]
    if any(t in transport_pref for t in ("train", "rail")):
        return True
    blob = json.dumps(constraints, default=str).lower()
    if any(term in blob for term in ("by train", "by rail", "take the train")):
        return True
    return distance_km >= FLIGHT_THRESHOLD_KM or duration_h >= LONG_DRIVE_HOURS


def _llm_advisory(origin, destination, distance_km):
    try:
        llm = get_llm()
        resp = llm.invoke([
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=_HUMAN.format(
                origin=origin, destination=destination, distance_km=int(distance_km),
            )),
        ])
        raw = extract_text_content(resp.content).strip()
        raw = strip_code_fences(raw)
        p = loads_loose(raw)
        return {
            "nearest_railhead": p.get("nearest_railhead") or "",
            "onward_note": p.get("onward_note") or "",
            "typical_trains": p.get("typical_trains") or [],
            "typical_fare_inr": p.get("typical_fare_inr") or [None, None],
            "typical_duration": p.get("typical_duration") or "",
            "rationale": p.get("rationale") or "",
        }
    except Exception as e:
        print(f"  ⚠️  train advisory LLM failed ({e})")
        return None


def train_agent_node(state: TripState) -> dict:
    constraints = state.get("extracted_constraints") or {}
    selected = state.get("selected_itinerary") or {}
    route = selected.get("route") or {}
    if not route:
        routes = state.get("route_candidates") or []
        if routes:
            route = max(routes, key=lambda r: float(r.get("distance_km") or 0))

    none_result = {"available": False, "advisory_available": False,
                   "advisory": None, "live_trains": None}

    distance_km, duration_h = _resolve_distance(constraints, route, state)
    if not _train_relevant(constraints, distance_km, duration_h):
        return {"trains": none_result}

    origin = constraints.get("origin") or route.get("origin") or "Delhi"
    destination = constraints.get("destination") or route.get("destination") or ""
    advisory = _llm_advisory(origin, destination, distance_km)

    # Best-effort live RailRadar lookup between origin and the resolved railhead.
    live_trains = None
    if RailRadarClient.available() and advisory:
        railhead = (advisory.get("nearest_railhead") or destination).split("(")[0].strip()
        try:
            live_trains = RailRadarClient.trains_between(origin, railhead)
            if live_trains:
                print(f"  ✅ RailRadar: {len(live_trains)} live trains {origin}→{railhead}")
        except Exception as e:
            print(f"  ⚠️  RailRadar lookup failed: {e}")

    return {"trains": {
        "available": bool(live_trains),
        "advisory_available": bool(advisory),
        "advisory": advisory,
        "live_trains": live_trains,
    }}
