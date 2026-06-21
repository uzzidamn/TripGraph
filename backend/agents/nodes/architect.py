"""Itinerary Architect — the brain of TripGraph AI.

ONE structured LLM call that replaces the deterministic template emitter
(timeline_generator), the slim enricher pass, the per-event fatigue scorer,
and the prose explainer. Given grounded candidates + travel-time matrix +
weather + the user's constraints, the architect produces a fully-reasoned
day-by-day plan in JSON:

  - chosen activities sequenced + clustered per day so people don't
    backtrack across the city
  - each stop has time, duration, why-visit reasoning, fatigue note,
    skippability, "tips for here"
  - excluded places with explicit reasons ("too far from rest of day")
  - gear checklist derived from the actual weather forecast
  - booking lead times + permits
  - the headline explanation prose
  - the AI's confidence + caveats

This is the closest thing to a human travel-planner's reasoning we can
afford. The deterministic Python layer still owns cost math + final
validation; the LLM owns sequencing, selection, narrative.
"""
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.llm_client import extract_text_content, get_llm
from backend.agents.state import TripState
from backend.api_clients.google_routes_client import GoogleRoutesClient


_SYSTEM = """You are the lead travel planner at TripGraph AI — equivalent to a
human who has spent a week researching this trip across blogs, YouTube, Reddit,
official tourism sites, and reviews. You build the *full* day-by-day plan.

You receive:
- The user's constraints (origin, destination, days, group, budget, preferences)
- The chosen transport mode (flight/train/drive — already decided)
- The chosen hotel (already picked from a tier-filtered shortlist)
- A pool of candidate activities + restaurants (each with coords, rating, editorial
  blurb, opening hours when known, est duration & cost)
- A real driving-time matrix between the top N candidates (minutes & km)
- The day-by-day weather forecast
- Brief insights from DuckDuckGo about the destination

YOUR JOB:
1. Select WHICH activities to include — not all of them. Skip lower-rated /
   geographically inconvenient ones unless they're must-includes. Aim for 2-3
   substantive stops per full day plus meals.
2. SEQUENCE them per day so consecutive stops are geographically clustered.
   Use the distance matrix. Don't ping-pong across the city.
3. RESPECT opening hours when known (don't schedule a fort at 6am if it opens at 9).
4. WRITE WHY each stop is worth it (1 sentence; reference what makes it special).
5. NOTE FATIGUE: rate each event 0-10 fatigue + 0-10 morale, and give it a
   skippability rating ("must" | "recommend" | "optional"). Cumulative fatigue
   matters — a day with 2 long treks should warn about the second one.
6. EMIT GEAR CHECKLIST from weather (rain → waterproofs; cold → layers; sun → SPF).
7. EMIT BOOKING LEAD TIMES for things that need advance reservation (trekking
   permits, popular restaurants, etc.) — use general knowledge.
8. EMIT LOCAL TIPS the KG can't know (cash-only spots, best time of day for X,
   shortcut routes, neighbourhoods to avoid after dark).
9. EMIT EXCLUDED items with reasons so the user understands the trade-offs.
10. INTER-CITY TRANSPORTATION TRANSITIONS (FLIGHT/TRAIN):
    - If the chosen mode is "flight", the Day 1 timeline MUST start with:
      - Event 1: Travel from the origin city to the departing airport (type: "travel", e.g. "Cab to Chandigarh Airport (IXC)"). Show duration: travel time + 120 min check-in/security buffer.
      - Event 2: Flight journey (type: "travel", e.g. "Flight to Goa (GOI)"). Show typical flight duration.
      - Event 3: Travel from destination airport to the hotel (type: "travel", e.g. "Cab/Bus from Goa Airport to Hotel"). Show travel time + 20-30 min buffer.
    - If the chosen mode is "train", similar transition events to/from train stations MUST be created on Day 1.
    - On the return day, you MUST include similar transition events returning to the origin city.
11. INTRA-CITY TRAVEL & TRAFFIC BUFFERS:
    - Include explicit "travel" type events between physical stops if the travel time is >15 minutes.
    - Calculate the travel duration from the provided driving-time matrix.
    - Add a realistic traffic buffer (e.g. 10-20 minutes depending on distance) and state this in the event's "why" field (e.g. "45 min drive via cab, includes 15 min buffer for peak traffic").

OUTPUT — exactly ONE valid JSON object, no markdown, matching this schema:

{
  "headline": "1-2 sentence summary of the plan and what makes it special",
  "confidence": "high" | "medium" | "low",
  "caveats": ["..."],
  "days": [
    {
      "day": 1,
      "theme": "short label e.g. 'Heritage downtown' or 'Arrival + sunset'",
      "weather_note": "1 line about the day's forecast and what it means",
      "events": [
        {
          "seq": 1,
          "start_time": "HH:MM",
          "end_time": "HH:MM",
          "type": "travel" | "hotel" | "activity" | "meal" | "rest",
          "title": "human-readable title shown on the pin",
          "place_id": "activity_id / hotel_id / null",
          "lat": float | null, "lng": float | null,
          "why": "one sentence on what makes this stop worth it",
          "tips": "one optional tip OR empty string",
          "fatigue": int 0-10,
          "morale": int 0-10,
          "skippability": "must" | "recommend" | "optional",
          "estimated_cost_pp": int,   // INR per person, 0 for included/free
          "transport_mode": "flight" | "train" | "cab" | "walk" | null // for type "travel"
        }
      ],
      "day_summary": "one sentence on the day's arc"
    }
  ],
  "excluded": [
    {"name": "...", "reason": "...", "consider_if": "..."}
  ],
  "gear_checklist": ["raincoat", "trekking shoes", ...],
  "booking_lead_times": [
    {"item": "Sinhagad permits", "how_far": "1 day", "where": "Forest dept booth at trailhead"}
  ],
  "local_tips": ["..."],
  "cost_summary": {
    "transport_pp": int,
    "hotel_pp_total": int,
    "activities_pp_total": int,
    "food_pp_total": int,
    "miscellaneous_pp": int,
    "total_pp": int
  }
}

HARD RULES:
- Every event MUST have lat/lng if it's a physical stop (pull from the candidate
  it references; null only for generic "Breakfast at Hotel" etc.).
- start_time / end_time always in 24h HH:MM; events never cross 23:00.
- Day count = user's trip_duration. Do not add/skip days.
- Activities pool is the source of truth — don't invent places not provided.
  (Exception: generic meals like "Lunch" or "Dinner" without a specific
  restaurant are allowed.)
- "headline" is shown to the user as the trip's tagline. Make it vivid.
- You are allowed (and encouraged) to add airports, train stations, and local transport terminals as transition stops in the timeline. Leave their lat/lng as null or 0; the backend geocoder will automatically resolve them by name.
"""


_HUMAN = """USER CONSTRAINTS:
{constraints}

CHOSEN MODE: {mode}
CHOSEN HOTEL: {hotel}

DAYS: {days}
GROUP: {group_size}

CANDIDATE ACTIVITIES (use only these; pick 2-3 per full day, sequenced):
{activities}

CANDIDATE RESTAURANTS (pick one per meal slot when relevant):
{restaurants}

DRIVING-TIME MATRIX between top stops (minutes; -1 = unknown):
{matrix}

WEATHER FORECAST:
{weather}

DESTINATION INSIGHTS (DDG):
{insights}

FLIGHT advisory (when relevant): {flight_advisory}
TRAIN advisory (when relevant):  {train_advisory}

TERMINAL INFO (airports/stations with real travel times from city center):
{terminal_info}

Produce the full day-by-day plan. Output ONLY the JSON object."""


def _slim_activities(acts: list[dict]) -> list[dict]:
    out = []
    for i, a in enumerate(acts[:20]):
        out.append({
            "i": i,
            "id": a.get("activity_id") or a.get("name"),
            "name": a.get("name"),
            "lat": a.get("lat"), "lng": a.get("lng"),
            "rating": a.get("rating"),
            "duration_min": a.get("duration_minutes"),
            "cost_pp": a.get("cost_per_person") or a.get("price_inr_estimate"),
            "tags": (a.get("tags") or [])[:5],
            "why": a.get("editorial_summary"),
            "hours": (a.get("opening_hours") or [None])[0],
        })
    return out


def _slim_restaurants(rs: list[dict]) -> list[dict]:
    return [
        {
            "id": r.get("restaurant_id") or r.get("name"),
            "name": r.get("name"),
            "lat": r.get("lat"), "lng": r.get("lng"),
            "meal_types": r.get("meal_types"),
            "cost_pp": r.get("avg_cost_per_person"),
        }
        for r in (rs or [])[:10]
    ]


def _slim_matrix(matrix: list[list[dict]] | None, places: list[dict]) -> list[dict]:
    """Flatten the matrix into a compact list the LLM can scan quickly."""
    if not matrix:
        return []
    rows = []
    n = len(matrix)
    for i in range(n):
        for j in range(n):
            if i == j or i >= len(places) or j >= len(places):
                continue
            cell = matrix[i][j]
            rows.append({
                "from": places[i].get("name", f"#{i}")[:30],
                "to":   places[j].get("name", f"#{j}")[:30],
                "minutes": cell.get("minutes", -1),
            })
    return rows


def architect_node(state: TripState) -> dict:
    """Produce the day-by-day plan + reasoning + cost in one structured call."""
    constraints = state.get("extracted_constraints") or {}
    selected = state.get("selected_itinerary") or {}
    activities = state.get("activity_candidates") or []
    restaurants = state.get("food_candidates") or []
    weather = state.get("weather_forecast") or {}
    insights = state.get("insights_per_place") or {}

    hotel = selected.get("hotel") or {}
    transport = selected.get("transport") or {}
    route = selected.get("route") or {}
    mode = (transport.get("mode") or "drive").lower()

    days = _parse_days(constraints.get("trip_duration"))

    # Build distance matrix for the top activities (+ hotel) so the architect
    # has real travel time signal.
    matrix_places = [hotel] + [a for a in activities if (a.get("name") or "").strip()][:9]
    matrix = GoogleRoutesClient.distance_matrix(matrix_places, max_stops=10) if matrix_places else None

    flight_adv = (state.get("flights") or {}).get("advisory") or {}
    train_adv = (state.get("trains") or {}).get("advisory") or {}
    terminal = state.get("terminal_info") or {}

    payload = _HUMAN.format(
        constraints=json.dumps({k: v for k, v in constraints.items() if v is not None}, default=str),
        mode=mode,
        hotel=json.dumps({"name": hotel.get("name"), "tier": hotel.get("tier"),
                          "price_per_night": hotel.get("price_per_night"),
                          "lat": hotel.get("lat"), "lng": hotel.get("lng")}, default=str),
        days=days, group_size=int(constraints.get("group_size") or 4),
        activities=json.dumps(_slim_activities(activities), default=str),
        restaurants=json.dumps(_slim_restaurants(restaurants), default=str),
        matrix=json.dumps(_slim_matrix(matrix, matrix_places), default=str),
        weather=json.dumps(weather, default=str)[:1500],
        insights=json.dumps({k: (v.get("abstract") or "")[:200] for k, v in insights.items()}, default=str),
        flight_advisory=json.dumps(flight_adv, default=str),
        train_advisory=json.dumps(train_adv, default=str),
        terminal_info=json.dumps(terminal, default=str),
    )

    last_review = state.get("last_review_feedback")
    if last_review:
        feedback_str = "\n\n⚠️ PREVIOUS PLAN CRITIQUE (You MUST fix these issues in the new plan):\n"
        feedback_str += f"Summary: {last_review.get('summary')}\n"
        for note in last_review.get("notes") or []:
            feedback_str += f"- Issue: {note.get('issue')} | Recommendation: {note.get('recommendation')}\n"
        payload += feedback_str

    try:
        llm = get_llm()
        resp = llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=payload)])
        raw = extract_text_content(resp.content).strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[-1]
            if raw.lstrip().startswith("json"):
                raw = raw.lstrip()[4:]
            raw = raw.rsplit("```", 1)[0]
        plan = json.loads(raw.strip())
    except Exception as e:
        print(f"  ⚠️  Architect LLM failed ({e}) — falling back to deterministic template")
        return _fallback_to_template(state)

    # ── Convert the architect's structured plan into the shapes the rest of
    # the system expects (timeline + map_points + cost_breakdown + explanation
    # + fatigue_per_event + selected_itinerary enrichment).
    timeline: list[dict] = []
    fatigue: dict[str, Any] = {}
    point_id_by_event: dict[str, str] = {}
    map_points: list[dict] = _seed_map_points(route, constraints, hotel)
    points_by_id = {p["id"]: p for p in map_points}

    for d in plan.get("days") or []:
        day_n = int(d.get("day") or 1)
        for ev in d.get("events") or []:
            seq = ev.get("seq") or len(timeline)
            etype = (ev.get("type") or "activity").lower()
            title = (ev.get("title") or "Event").strip()
            start = ev.get("start_time") or "09:00"
            end = ev.get("end_time") or start
            event_id = f"d{day_n}_{seq:02d}_{etype}_{_slug(title)[:24]}"

            # Figure out the matching map point — prefer the architect's lat/lng,
            # else look up by place_id, else by geocoding transit terminal (airport/station).
            pt_id = None
            lat = ev.get("lat")
            lng = ev.get("lng")
            if lat is None or lng is None or (lat == 0 and lng == 0):
                title_l = title.lower()
                if any(k in title_l for k in ("airport", "station", "railway", "junction", "terminal")):
                    try:
                        from backend.api_clients.ors_client import ORSClient
                        search_term = title
                        if "airport" in title_l:
                            search_term = f"{title}, India"
                        geo = ORSClient.geocode(search_term)
                        if geo:
                            lat = geo["lat"]
                            lng = geo["lng"]
                            ev["lat"] = lat
                            ev["lng"] = lng
                    except Exception:
                        pass

            t_mode = ev.get("transport_mode") or ev.get("mode")
            if lat is not None and lng is not None and not (lat == 0 and lng == 0):
                place_key = (ev.get("place_id") or _slug(title))
                pt_id = f"{etype}:{place_key}"
                if pt_id not in points_by_id:
                    p = {"id": pt_id, "lat": lat, "lng": lng, "label": title, "type": etype,
                         "day": day_n, "seq": seq, "mode": t_mode}
                    map_points.append(p)
                    points_by_id[pt_id] = p
                else:
                    points_by_id[pt_id]["day"] = day_n
                    points_by_id[pt_id]["seq"] = seq
                    if t_mode:
                        points_by_id[pt_id]["mode"] = t_mode

            tl_event = {
                "id": event_id,
                "day": day_n,
                "start_time": start,
                "end_time": end,
                "title": title,
                "type": etype,
                "seq": seq,
                "why": ev.get("why") or "",
                "tips": ev.get("tips") or "",
                "skippability": ev.get("skippability") or "recommend",
                "lat": lat, "lng": lng,
                "point_id": pt_id,
                "transport_mode": t_mode,
            }
            cost = ev.get("estimated_cost_pp")
            if cost:
                tl_event["cost"] = int(cost)

            # Carry through enrichment fields from the original candidate so the
            # popover gets the photo / rating / opening hours.
            cand = _find_candidate(activities, restaurants, ev.get("place_id"), title)
            if cand:
                for k in ("photo_name", "editorial_summary", "rating", "rating_count",
                          "opening_hours", "tags", "address", "website"):
                    if cand.get(k) and not tl_event.get(k):
                        tl_event[k] = cand[k]

            timeline.append(tl_event)
            fatigue[event_id] = {
                "base_fatigue": int(ev.get("fatigue") or 4),
                "base_morale": int(ev.get("morale") or 6),
                "adjusted_fatigue": int(ev.get("fatigue") or 4),
                "adjusted_morale": int(ev.get("morale") or 6),
                "skippability": ev.get("skippability") or "recommend",
                "note": ev.get("tips") or "",
            }
            point_id_by_event[event_id] = pt_id

    cost = plan.get("cost_summary") or {}
    cost_breakdown = {
        "transport": int(cost.get("transport_pp") or 0),
        "hotel": int(cost.get("hotel_pp_total") or 0),
        "activities": int(cost.get("activities_pp_total") or 0),
        "food": int(cost.get("food_pp_total") or 0),
        "miscellaneous": int(cost.get("miscellaneous_pp") or 1500),
        "total": int(cost.get("total_pp") or 0) or _sum_cost(cost),
        "budget_limit": int(constraints.get("budget_per_person") or 0),
    }

    # Merge architect enrichment into selected_itinerary
    enriched = dict(selected)
    enriched["architect_plan"] = plan
    enriched["cost_breakdown"] = cost_breakdown
    enriched["total_cost_per_person"] = cost_breakdown["total"]
    enriched["headline"] = plan.get("headline")
    enriched["gear_checklist"] = plan.get("gear_checklist") or []
    enriched["booking_lead_times"] = plan.get("booking_lead_times") or []
    enriched["local_tips"] = plan.get("local_tips") or []
    enriched["excluded_places"] = plan.get("excluded") or []
    enriched["day_themes"] = [{"day": d.get("day"), "theme": d.get("theme"),
                               "summary": d.get("day_summary"),
                               "weather_note": d.get("weather_note")} for d in (plan.get("days") or [])]

    print(f"  🧠 Architect: {len(timeline)} events across {len(plan.get('days') or [])} days, "
          f"cost ₹{cost_breakdown['total']}/pp, confidence={plan.get('confidence')}")

    return {
        "selected_itinerary": enriched,
        "timeline": timeline,
        "map_points": map_points,
        "cost_breakdown": cost_breakdown,
        "fatigue_per_event": fatigue,
        "explanation": plan.get("headline") or "",
        "architect_plan": plan,
    }


# ─── helpers ───────────────────────────────────────────────────────────────
def _parse_days(td) -> int:
    import re
    if isinstance(td, int):
        return max(1, td)
    text = str(td or "").strip().lower()
    if "long" in text and "weekend" in text:
        return 3
    if "weekend" in text:
        return 2
    m = re.search(r"(\d+)\s*d", text) or re.search(r"(\d+)\s*(?:day|night)", text) or re.search(r"\b(\d+)\b", text)
    return max(1, int(m.group(1))) if m else 2


def _slug(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in (s or "")).strip("_") or "evt"


def _sum_cost(c: dict) -> int:
    return sum(int(c.get(k) or 0) for k in ("transport_pp", "hotel_pp_total", "activities_pp_total",
                                            "food_pp_total", "miscellaneous_pp"))


def _seed_map_points(route: dict, constraints: dict, hotel: dict) -> list[dict]:
    """Seed origin/destination/hotel pins so they always show up on the map."""
    pts = []
    if route.get("origin"):
        olabel = route.get("origin")
        lat = route.get("origin_lat")
        lng = route.get("origin_lng")
        if lat is None or lng is None or (lat == 0 and lng == 0):
            try:
                from backend.api_clients.ors_client import ORSClient
                geo = ORSClient.geocode(olabel)
                if geo:
                    lat, lng = geo["lat"], geo["lng"]
            except Exception:
                pass
        if not lat or not lng:
            lat, lng = 28.4595, 77.0266
        pts.append({"id": f"origin:{olabel}", "lat": lat, "lng": lng, "label": olabel,
                    "type": "origin", "day": 1, "seq": 0})
    if route.get("dest_lat") and route.get("dest_lng"):
        dlabel = route.get("destination") or "Destination"
        pts.append({"id": f"destination:{dlabel}", "lat": route["dest_lat"],
                    "lng": route["dest_lng"], "label": dlabel, "type": "destination",
                    "day": 1, "seq": 1})
    if hotel.get("lat") and hotel.get("lng"):
        hid = hotel.get("hotel_id") or hotel.get("name") or "hotel"
        pts.append({"id": f"hotel:{hid}", "lat": hotel["lat"], "lng": hotel["lng"],
                    "label": hotel.get("name", "Hotel"), "type": "hotel", "day": 1, "seq": 2})
    return pts


def _find_candidate(activities: list[dict], restaurants: list[dict], place_id, title: str):
    title_l = (title or "").lower().strip()
    for src in (activities, restaurants):
        for c in src:
            if place_id and (c.get("activity_id") == place_id or c.get("restaurant_id") == place_id
                             or c.get("name") == place_id):
                return c
            if c.get("name") and c["name"].lower() in title_l:
                return c
    return None


def _fallback_to_template(state: TripState) -> dict:
    """When the architect LLM call fails, fall back to the old deterministic
    template generator so the trip still renders."""
    from backend.planner.timeline_generator import generate_timeline
    selected = state.get("selected_itinerary") or {}
    constraints = state.get("extracted_constraints") or {}
    timeline = generate_timeline(selected, constraints)
    return {"timeline": timeline}
