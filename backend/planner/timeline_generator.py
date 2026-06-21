"""
Generate a sequential timeline of events from a trip itinerary.
Supports multi-day trips by parsing trip_duration from constraints.
"""
import re
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Duration parsing
# ---------------------------------------------------------------------------

def _parse_days(trip_duration) -> int:
    """Return number of trip days from a trip_duration string.

    Handles: "2D1N", "3D2N", "7D6N", "weekend", "1 week", "10 days", int, None.
    """
    if not trip_duration:
        return 2
    if isinstance(trip_duration, int):
        return max(1, trip_duration)

    s = str(trip_duration).lower().strip()

    # "XD(Y)N" format  e.g. "3D2N", "7D6N"
    m = re.match(r"(\d+)\s*d", s)
    if m:
        return max(1, int(m.group(1)))

    # "X week(s)"
    m = re.match(r"(\d+)\s*week", s)
    if m:
        return int(m.group(1)) * 7

    # "X day(s)"
    m = re.match(r"(\d+)\s*day", s)
    if m:
        return max(1, int(m.group(1)))

    # "weekend"
    if "weekend" in s:
        return 2

    return 2


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_timeline(itinerary: dict, constraints: dict | None = None) -> list[dict]:
    """Create a chronological list of timeline events for the full trip duration.

    Args:
        itinerary:   Selected itinerary dict (route, transport, hotel, activities…).
        constraints: Extracted constraint dict; used for trip_duration and group_size.
    """
    if constraints is None:
        constraints = {}

    events: list[dict] = []
    route      = itinerary.get("route")      or {}
    transport  = itinerary.get("transport")  or {}
    hotel      = itinerary.get("hotel")      or {}
    activities = list(itinerary.get("activities") or [])
    restaurants= list(itinerary.get("restaurants") or [])
    waypoints  = list(itinerary.get("waypoints")  or [])

    n_days = _parse_days(constraints.get("trip_duration") or itinerary.get("trip_duration"))

    travel_minutes_raw = (
        transport.get("base_duration_minutes")
        or transport.get("duration_hours", 0) * 60
        or route.get("base_drive_minutes")
        or route.get("duration_hours", 0) * 60
        or 300
    )
    try:
        travel_minutes = int(travel_minutes_raw)
    except (ValueError, TypeError):
        travel_minutes = 300

    mode        = (transport.get("mode") or "cab").lower()
    is_flight   = mode == "flight"
    is_train    = mode in ("train", "bus")

    origin      = route.get("origin", "Origin")
    destination = route.get("destination", "Destination")
    group_size  = constraints.get("group_size") or 4
    price_night = hotel.get("price_per_night") or 0

    # Mode-specific verbs
    if is_flight:
        depart_verb = f"Fly from {origin} to {destination}"
        return_verb = f"Return flight to {origin}"
    elif is_train:
        depart_verb = f"{mode.capitalize()} from {origin} to {destination}"
        return_verb = f"Return {mode} to {origin}"
    else:
        depart_verb = f"Drive from {origin}"
        return_verb = f"Return drive to {origin}"

    dest_restaurants = [r for r in restaurants if r.get("destination") == destination]

    # ---------------------------------------------------------------------------
    # DAY 1 — Travel day
    # ---------------------------------------------------------------------------
    cur = datetime(2026, 1, 1, 6, 0)

    if is_flight or is_train:
        # Point-to-point: single journey event
        arrive = cur + timedelta(minutes=travel_minutes)
        events.append(_ev(1, cur, arrive, depart_verb, "travel"))
        cur = arrive
    else:
        # Road trip: two legs with optional waypoint breakfast stop
        half = travel_minutes // 2
        mid  = cur + timedelta(minutes=half)
        events.append(_ev(1, cur, mid, depart_verb, "travel"))
        cur = mid

        if waypoints:
            wp_end = cur + timedelta(minutes=45)
            events.append(_ev(1, cur, wp_end, f"Breakfast at {waypoints[0].get('name','Stop')}", "meal"))
            cur = wp_end

        arrive = cur + timedelta(minutes=half)
        events.append(_ev(1, cur, arrive, f"Continue drive to {destination}", "travel"))
        cur = arrive

    # Lunch on arrival
    if dest_restaurants:
        r = dest_restaurants[0]
        dur = _int(r.get("avg_duration_minutes"), 60)
        end = cur + timedelta(minutes=dur)
        events.append(_ev(1, cur, end, f"Lunch at {r.get('name','Restaurant')}", "meal",
                          cost=r.get("avg_cost_per_person", 0)))
        cur = end

    # Check-in
    ci = cur + timedelta(minutes=30)
    ci_end = ci + timedelta(minutes=60)
    events.append(_ev(1, ci, ci_end, f"Check-in: {hotel.get('name','Hotel')}", "hotel",
                      cost=price_night // group_size))
    cur = ci_end

    # Day 1 evening activity — only if we arrive early enough to enjoy it
    _ACTIVITY_CUTOFF = datetime(2026, 1, 1, 17, 0)
    if activities and cur <= _ACTIVITY_CUTOFF:
        act = activities[0]
        dur = _int(act.get("duration_minutes"), 90)
        end = cur + timedelta(minutes=dur)
        events.append(_ev(1, cur, end, act.get("name","Activity"), "activity",
                          cost=act.get("cost_per_person", 0)))
        cur = end

    # Dinner window: 19:00–21:00. Fill gap with free time if we finish early;
    # cap at 21:00 so late arrivals never show an unreasonable dinner slot.
    _DINNER_MIN = datetime(2026, 1, 1, 19, 0)
    _DINNER_CAP = datetime(2026, 1, 1, 21, 0)
    dinner_start = max(min(cur, _DINNER_CAP), _DINNER_MIN)
    if dinner_start > cur + timedelta(minutes=30):
        events.append(_ev(1, cur, dinner_start, f"Free time — explore {destination}", "activity"))
    events.append(_ev(1, dinner_start, dinner_start + timedelta(minutes=60), "Dinner", "meal"))

    # ---------------------------------------------------------------------------
    # MIDDLE DAYS (2 … N-1)  — Full activity days
    # Real activities are used once. When the pool is exhausted, generic
    # free-time fillers rotate so days are never meals-only.
    # ---------------------------------------------------------------------------
    day1_act_name = activities[0].get("name") if activities else None
    pool = [a for a in activities if a.get("name") != day1_act_name]
    used_names = {day1_act_name} if day1_act_name else set()

    _FILLERS = [
        {"name": f"Explore {destination} on foot",       "duration_minutes": 120, "cost_per_person": 0},
        {"name": "Visit local market & souvenirs",        "duration_minutes": 90,  "cost_per_person": 0},
        {"name": f"Leisure time at {hotel.get('name','hotel')}", "duration_minutes": 90, "cost_per_person": 0},
        {"name": "Day trip to nearby attractions",         "duration_minutes": 180, "cost_per_person": 0},
        {"name": "Photography walk around the city",       "duration_minutes": 120, "cost_per_person": 0},
        {"name": "Café hopping & local cuisine tasting",   "duration_minutes": 90,  "cost_per_person": 0},
        {"name": "Relaxation & spa / pool time",           "duration_minutes": 120, "cost_per_person": 0},
    ]
    filler_index = 0

    def _next_act():
        """Return next unused real activity, or a rotating filler if pool exhausted."""
        nonlocal filler_index
        for act in pool:
            name = act.get("name")
            if name not in used_names:
                used_names.add(name)
                return act
        # Pool exhausted — use a filler (rotate through, never repeat consecutively)
        filler = _FILLERS[filler_index % len(_FILLERS)]
        filler_index += 1
        return filler

    for day in range(2, n_days):          # days 2, 3, … N-1
        cur = datetime(2026, 1, day, 7, 30)
        events.append(_ev(day, cur, cur + timedelta(minutes=45), "Breakfast", "meal"))
        cur += timedelta(minutes=45)

        # Morning block — up to 3 activities
        for _ in range(3):
            act = _next_act()
            dur = _int(act.get("duration_minutes"), 150)
            end = cur + timedelta(minutes=dur)
            events.append(_ev(day, cur, end, act.get("name", "Activity"), "activity",
                              cost=act.get("cost_per_person", 0)))
            cur = end

        events.append(_ev(day, cur, cur + timedelta(minutes=90), "Lunch & rest", "meal"))
        cur += timedelta(minutes=90)

        # Afternoon activity
        act = _next_act()
        dur = _int(act.get("duration_minutes"), 120)
        end = cur + timedelta(minutes=dur)
        events.append(_ev(day, cur, end, act.get("name", "Activity"), "activity",
                          cost=act.get("cost_per_person", 0)))
        cur = end

        events.append(_ev(day, cur, cur + timedelta(minutes=60), "Dinner", "meal"))

    # ---------------------------------------------------------------------------
    # LAST DAY (Day N) — Checkout + return
    # ---------------------------------------------------------------------------
    last = n_days
    cur  = datetime(2026, 1, last, 7, 0)
    events.append(_ev(last, cur, cur + timedelta(minutes=45), "Breakfast", "meal"))
    cur += timedelta(minutes=45)

    # One final morning activity before checkout
    act = _next_act()
    if act:
        dur = _int(act.get("duration_minutes"), 120)
        end = cur + timedelta(minutes=dur)
        events.append(_ev(last, cur, end, act.get("name", "Activity"), "activity",
                          cost=act.get("cost_per_person", 0)))
        cur = end

    events.append(_ev(last, cur, cur + timedelta(minutes=30), f"Checkout: {hotel.get('name','Hotel')}", "hotel"))
    cur += timedelta(minutes=30)

    # Return journey
    return_end = cur + timedelta(minutes=travel_minutes)
    events.append(_ev(last, cur, return_end, return_verb, "travel"))

    return events


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _int(val, default: int) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _ev(day: int, start: datetime, end: datetime,
        title: str, event_type: str, cost: int = 0) -> dict:
    return {
        "day": day,
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "title": title,
        "type": event_type,
        **({"cost": _int(cost, 0)} if cost else {}),
    }
