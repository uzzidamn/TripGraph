"""Generate a sequential timeline of events from a trip graph.

Honors `constraints.trip_duration` (e.g. "4 days", "3D2N", "weekend") so a
3- or 4-day plan actually produces 3-4 days of events instead of a hardcoded
2-day round trip.

Pattern for an N-day trip:
    Day 1     : depart → highway breakfast → drive → arrival lunch → check-in → optional cultural activity → dinner
    Day 2..N-1: breakfast → morning activity → lunch → afternoon activity → dinner
    Day N     : breakfast → morning activity → checkout → lunch → return drive

If N == 2, this collapses to the original behaviour (Day 1 = arrival + 1 activity, Day 2 = 1 activity + return).
"""
import re
from datetime import datetime, timedelta


def _parse_days(constraints: dict | None) -> int:
    """Coerce trip_duration into a number of days (default 2)."""
    if not constraints:
        return 2
    raw = constraints.get("trip_duration") or constraints.get("days")
    if isinstance(raw, int):
        return max(1, raw)
    if not raw:
        return 2
    text = str(raw).strip().lower()
    # "weekend" → 2, "long weekend" → 3
    if "long" in text and "weekend" in text:
        return 3
    if "weekend" in text:
        return 2
    # "3D2N", "4D3N" — pick the larger of D / N+1
    m = re.search(r"(\d+)\s*d", text)
    if m:
        return max(1, int(m.group(1)))
    # "4 days", "3 day", "4-day"
    m = re.search(r"(\d+)\s*(?:day|night)", text)
    if m:
        n = int(m.group(1))
        return max(1, n + 1 if "night" in text and "day" not in text else n)
    # "4" alone
    m = re.search(r"\b(\d+)\b", text)
    if m:
        return max(1, int(m.group(1)))
    return 2


def generate_timeline(itinerary: dict, constraints: dict | None = None) -> list[dict]:
    """Create a chronological list of timeline events sized to trip_duration."""
    transport = itinerary.get("transport") or {}
    # Flight itineraries get a completely different (realistic) shape so a
    # 1600 km trip isn't rendered as an 18-hour overnight drive.
    if (transport.get("mode") or "").lower() == "flight":
        return _flight_timeline(itinerary, constraints)

    events: list[dict] = []
    route = itinerary.get("route") or {}
    hotel = itinerary.get("hotel") or {}
    activities = itinerary.get("activities") or []
    restaurants = itinerary.get("restaurants") or []
    waypoints = itinerary.get("waypoints") or []

    drive_minutes_raw = transport.get("base_duration_minutes") or route.get("base_drive_minutes") or 300
    try:
        drive_minutes = int(drive_minutes_raw)
    except (ValueError, TypeError):
        drive_minutes = 300
    # Cap a single day's driving so events don't spill past midnight. Anything
    # longer should have been a flight (mode_planner handles >500 km).
    drive_minutes = min(drive_minutes, 600)

    group_size = int((constraints or {}).get("group_size") or 4)
    n_days = _parse_days(constraints)
    print(f"  [Timeline] trip_duration={constraints.get('trip_duration') if constraints else '-'} → {n_days} days (drive)")

    # Activities pool — try to spread across days
    activities_pool = [a for a in activities if (a.get("name") or "").strip()]
    used_activity_ids: set[str] = set()

    def _take_activity(prefer_tags: list[str] | None = None):
        """Pop next best activity from the pool, filtering by used + optional tag preference."""
        for act in activities_pool:
            key = act.get("activity_id") or act.get("name")
            if key in used_activity_ids:
                continue
            if prefer_tags:
                act_tags = [t.lower() for t in (act.get("tags") or [])]
                if not any(pt.lower() in act_tags for pt in prefer_tags):
                    continue
            used_activity_ids.add(key)
            return act
        # Fall back to any unused activity if tag filter failed
        if prefer_tags:
            return _take_activity(None)
        return None

    def _restaurants_for(meal_label: str):
        """Pick a restaurant matching the destination, biased to meal type."""
        dest_name = route.get("destination")
        candidates = [r for r in restaurants if r.get("destination") == dest_name]
        for r in candidates:
            meal_types = [m.lower() for m in (r.get("meal_types") or [])]
            if meal_label.lower() in meal_types:
                return r
        return candidates[0] if candidates else None

    # ─── Day 1: depart → arrive → check-in ─────────────────────────────────
    current = datetime(2026, 1, 1, 6, 0)
    depart_end = current + timedelta(minutes=drive_minutes // 2)
    events.append(_event(1, current, depart_end, f"Drive from {route.get('origin', 'Origin')}", "travel"))
    current = depart_end

    if waypoints:
        wp = waypoints[0]
        bkfst_end = current + timedelta(minutes=45)
        events.append(_event(1, current, bkfst_end, f"Breakfast at {wp.get('name', 'Highway Stop')}", "meal", point_ref=wp))
        current = bkfst_end

    arrive_time = current + timedelta(minutes=drive_minutes // 2)
    events.append(_event(1, current, arrive_time, f"Continue drive to {route.get('destination', 'Destination')}", "travel"))
    current = arrive_time

    lunch_dest = _restaurants_for("lunch")
    if lunch_dest:
        lunch_dur = int(lunch_dest.get("avg_duration_minutes") or 60)
        lunch_end = current + timedelta(minutes=lunch_dur)
        events.append(_event(1, current, lunch_end, f"Lunch at {lunch_dest.get('name', 'Restaurant')}", "meal",
                             cost=lunch_dest.get("avg_cost_per_person", 0), point_ref=lunch_dest))
        current = lunch_end

    # Hotel check-in (Day 1 only — N nights are inferred by trip_duration)
    checkin = current + timedelta(minutes=30)
    rest_end = checkin + timedelta(minutes=60)
    price_night = hotel.get("price_per_night") or 0
    events.append(_event(1, checkin, rest_end, f"Check-in at {hotel.get('name', 'Hotel')}", "hotel",
                         cost=(price_night * (n_days - 1)) // max(group_size, 1), point_ref=hotel))
    current = rest_end

    # Day 1 evening activity (cultural / casual preferred)
    evening_act = _take_activity(prefer_tags=["cultural", "evening", "spiritual", "viewpoint", "scenic"])
    if evening_act:
        act_dur = int(evening_act.get("duration_minutes") or 90)
        act_end = current + timedelta(minutes=act_dur)
        events.append(_event(1, current, act_end, evening_act["name"], "activity",
                             cost=evening_act.get("cost_per_person", 0), point_ref=evening_act))
        current = act_end

    # Day 1 dinner
    dinner_dur = 60
    events.append(_event(1, current, current + timedelta(minutes=dinner_dur), "Dinner", "meal"))

    # ─── Days 2..N-1: full activity days ──────────────────────────────────
    for day in range(2, n_days):
        current = datetime(2026, 1, day, 7, 30)

        bk_end = current + timedelta(minutes=45)
        events.append(_event(day, current, bk_end, "Breakfast at Hotel", "meal"))
        current = bk_end + timedelta(minutes=15)

        # Morning activity — prefer high-morale / adventurous
        morning_act = _take_activity(prefer_tags=["adventure", "trekking", "hike", "rafting", "nature", "wildlife"])
        if morning_act:
            act_dur = int(morning_act.get("duration_minutes") or 180)
            act_end = current + timedelta(minutes=act_dur)
            events.append(_event(day, current, act_end, morning_act["name"], "activity",
                                 cost=morning_act.get("cost_per_person", 0), point_ref=morning_act))
            current = act_end

        # Lunch
        lunch_act = _restaurants_for("lunch")
        if lunch_act and day == 2:  # avoid showing the same restaurant every day
            lunch_dur = int(lunch_act.get("avg_duration_minutes") or 60)
            l_end = current + timedelta(minutes=lunch_dur)
            events.append(_event(day, current, l_end, f"Lunch at {lunch_act.get('name')}", "meal",
                                 cost=lunch_act.get("avg_cost_per_person", 0), point_ref=lunch_act))
            current = l_end
        else:
            events.append(_event(day, current, current + timedelta(minutes=60), "Lunch", "meal"))
            current += timedelta(minutes=60)

        # Afternoon activity — prefer cafes / cultural / shopping
        afternoon_act = _take_activity(prefer_tags=["cafe", "cultural", "shopping", "heritage", "market"])
        if afternoon_act:
            act_dur = int(afternoon_act.get("duration_minutes") or 120)
            a_end = current + timedelta(minutes=act_dur)
            events.append(_event(day, current, a_end, afternoon_act["name"], "activity",
                                 cost=afternoon_act.get("cost_per_person", 0), point_ref=afternoon_act))
            current = a_end

        # Dinner
        events.append(_event(day, current, current + timedelta(minutes=60), "Dinner", "meal"))

    # ─── Day N: morning activity → checkout → return drive ────────────────
    if n_days >= 2:
        last = n_days
        current = datetime(2026, 1, last, 7, 30)
        bk_end = current + timedelta(minutes=45)
        events.append(_event(last, current, bk_end, "Breakfast at Hotel", "meal"))
        current = bk_end + timedelta(minutes=15)

        # One last activity if any remain
        last_act = _take_activity()
        if last_act:
            act_dur = int(last_act.get("duration_minutes") or 120)
            a_end = current + timedelta(minutes=act_dur)
            events.append(_event(last, current, a_end, last_act["name"], "activity",
                                 cost=last_act.get("cost_per_person", 0), point_ref=last_act))
            current = a_end

        # Checkout + light lunch
        co_end = current + timedelta(minutes=30)
        events.append(_event(last, current, co_end, "Checkout & freshen up", "rest"))
        current = co_end

        l_end = current + timedelta(minutes=60)
        events.append(_event(last, current, l_end, "Lunch", "meal"))
        current = l_end

        # Return journey
        return_end = current + timedelta(minutes=drive_minutes)
        events.append(_event(last, current, return_end, f"Return to {route.get('origin', 'Origin')}", "travel"))

    return events


def _flight_timeline(itinerary: dict, constraints: dict | None = None) -> list[dict]:
    """Realistic flight-based itinerary.

    Day 1:  depart for origin airport → flight → arrive & transfer → check-in →
            optional light activity → dinner
    Days 2..N-1:  breakfast → morning activity → lunch → afternoon activity → dinner
    Day N:  breakfast → activity → checkout → transfer to airport → return flight
    """
    events: list[dict] = []
    route = itinerary.get("route") or {}
    transport = itinerary.get("transport") or {}
    hotel = itinerary.get("hotel") or {}
    activities = [a for a in (itinerary.get("activities") or []) if (a.get("name") or "").strip()]

    origin = route.get("origin", "Origin")
    destination = route.get("destination", "Destination")
    airport = transport.get("nearest_airport") or f"{destination} airport"
    flight_min = int(transport.get("flight_minutes") or 150)
    group_size = int((constraints or {}).get("group_size") or 4)
    n_days = _parse_days(constraints)
    print(f"  [Timeline] trip_duration={constraints.get('trip_duration') if constraints else '-'} → {n_days} days (flight)")

    used: set[str] = set()

    def take(prefer=None):
        for a in activities:
            key = a.get("activity_id") or a.get("name")
            if key in used:
                continue
            if prefer:
                tags = [t.lower() for t in (a.get("tags") or [])]
                if not any(p.lower() in tags for p in prefer):
                    continue
            used.add(key)
            return a
        if prefer:
            return take(None)
        return None

    # ── Day 1: travel by air ──────────────────────────────────────────────
    cur = datetime(2026, 1, 1, 8, 0)
    e = cur + timedelta(minutes=120)
    events.append(_event(1, cur, e, f"Depart for {origin} airport", "travel"))
    cur = e
    e = cur + timedelta(minutes=flight_min)
    fare_pp = transport.get("cost_per_person_roundtrip")
    events.append(_event(1, cur, e, f"Flight to {destination}", "travel",
                         cost=(fare_pp // 2) if fare_pp else 0))
    cur = e
    e = cur + timedelta(minutes=90)
    events.append(_event(1, cur, e, f"Arrive at {airport} & transfer to hotel", "travel"))
    cur = e
    e = cur + timedelta(minutes=45)
    price_night = hotel.get("price_per_night") or 0
    events.append(_event(1, cur, e, f"Check-in at {hotel.get('name', 'Hotel')}", "hotel",
                         cost=(price_night * (n_days - 1)) // max(group_size, 1), point_ref=hotel))
    cur = e
    act = take(prefer=["cultural", "viewpoint", "scenic", "cafe", "evening"])
    if act:
        e = cur + timedelta(minutes=int(act.get("duration_minutes") or 90))
        events.append(_event(1, cur, e, act["name"], "activity",
                             cost=act.get("cost_per_person", 0), point_ref=act))
        cur = e
    events.append(_event(1, cur, cur + timedelta(minutes=60), "Dinner", "meal"))

    # ── Days 2..N-1: full activity days ──────────────────────────────────
    for day in range(2, n_days):
        cur = datetime(2026, 1, day, 8, 0)
        e = cur + timedelta(minutes=45)
        events.append(_event(day, cur, e, "Breakfast at Hotel", "meal"))
        cur = e + timedelta(minutes=15)
        m = take(prefer=["adventure", "trekking", "hike", "nature", "wildlife", "heritage"])
        if m:
            e = cur + timedelta(minutes=int(m.get("duration_minutes") or 180))
            events.append(_event(day, cur, e, m["name"], "activity",
                                 cost=m.get("cost_per_person", 0), point_ref=m))
            cur = e
        events.append(_event(day, cur, cur + timedelta(minutes=60), "Lunch", "meal"))
        cur += timedelta(minutes=60)
        a2 = take(prefer=["cafe", "cultural", "shopping", "market", "heritage"])
        if a2:
            e = cur + timedelta(minutes=int(a2.get("duration_minutes") or 120))
            events.append(_event(day, cur, e, a2["name"], "activity",
                                 cost=a2.get("cost_per_person", 0), point_ref=a2))
            cur = e
        events.append(_event(day, cur, cur + timedelta(minutes=60), "Dinner", "meal"))

    # ── Day N: last activity → fly home ──────────────────────────────────
    if n_days >= 2:
        last = n_days
        cur = datetime(2026, 1, last, 8, 0)
        e = cur + timedelta(minutes=45)
        events.append(_event(last, cur, e, "Breakfast at Hotel", "meal"))
        cur = e + timedelta(minutes=15)
        la = take()
        if la:
            e = cur + timedelta(minutes=int(la.get("duration_minutes") or 120))
            events.append(_event(last, cur, e, la["name"], "activity",
                                 cost=la.get("cost_per_person", 0), point_ref=la))
            cur = e
        e = cur + timedelta(minutes=45)
        events.append(_event(last, cur, e, "Checkout & transfer to airport", "rest"))
        cur = e + timedelta(minutes=90)
        e = cur + timedelta(minutes=flight_min)
        events.append(_event(last, cur, e, f"Return flight to {origin}", "travel",
                             cost=(fare_pp // 2) if fare_pp else 0))

    return events


def _event(day: int, start: datetime, end: datetime, title: str, event_type: str,
           cost: int = 0, point_ref: dict | None = None) -> dict:
    """Build a single timeline event with a stable id deterministic from
    (day, start_time, type, title)."""
    try:
        cost = int(cost)
    except (ValueError, TypeError):
        cost = 0
    start_str = start.strftime("%H:%M")
    end_str = end.strftime("%H:%M")
    safe_title = "".join(ch.lower() if ch.isalnum() else "_" for ch in (title or ""))[:32].strip("_")
    event_id = f"d{day}_{start_str.replace(':', '')}_{event_type}_{safe_title}"
    out = {
        "id": event_id,
        "day": day,
        "start_time": start_str,
        "end_time": end_str,
        "title": title,
        "type": event_type,
    }
    if cost:
        out["cost"] = cost
    if point_ref:
        for k in ("lat", "lng", "tags", "name", "address",
                  "hotel_id", "activity_id", "waypoint_id", "restaurant_id",
                  "price_per_night", "tier", "cost_per_person", "category",
                  "fatigue_score_base", "morale_score_base",
                  "rating", "rating_count", "photo_name", "editorial_summary"):
            if k in point_ref and point_ref[k] is not None:
                out[k] = point_ref[k]
    return out
