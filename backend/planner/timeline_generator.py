"""
Generate a sequential timeline of events from a trip graph.
Places events in chronological order with calculated start/end times.
"""
from datetime import datetime, timedelta


def generate_timeline(itinerary: dict) -> list[dict]:
    """
    Create a chronological list of timeline events from the itinerary.
    Each event has: day, start_time, end_time, title, type, cost (optional).
    """
    events = []
    route = itinerary.get("route") or {}
    transport = itinerary.get("transport") or {}
    hotel = itinerary.get("hotel") or {}
    activities = itinerary.get("activities") or []
    restaurants = itinerary.get("restaurants") or []
    waypoints = itinerary.get("waypoints") or []

    drive_minutes_raw = transport.get("base_duration_minutes") or route.get("base_drive_minutes") or 300
    try:
        drive_minutes = int(drive_minutes_raw)
    except (ValueError, TypeError):
        drive_minutes = 300
        
    group_size = 4

    # Day 1
    current = datetime(2026, 1, 1, 6, 0)  # 06:00 departure

    # Departure
    depart_end = current + timedelta(minutes=drive_minutes // 2)
    events.append(_event(1, current, depart_end, f"Drive from {route.get('origin', 'Origin')}", "travel"))

    # Breakfast waypoint
    current = depart_end
    breakfast_end = current + timedelta(minutes=45)
    if waypoints:
        wp = waypoints[0]
        events.append(_event(1, current, breakfast_end, f"Breakfast at {wp.get('name', 'Highway Stop')}", "meal"))
    current = breakfast_end

    # Continue drive
    arrive_time = current + timedelta(minutes=drive_minutes // 2)
    events.append(_event(1, current, arrive_time, f"Continue drive to {route.get('destination', 'Destination')}", "travel"))
    current = arrive_time

    # Lunch
    if restaurants:
        dest_restaurants = [r for r in restaurants if r.get("destination") == route.get("destination")]
        if dest_restaurants:
            lunch_dur_raw = dest_restaurants[0].get("avg_duration_minutes") or 60
            try:
                lunch_dur = int(lunch_dur_raw)
            except (ValueError, TypeError):
                lunch_dur = 60
            lunch_end = current + timedelta(minutes=lunch_dur)
            events.append(_event(1, current, lunch_end, f"Lunch at {dest_restaurants[0].get('name', 'Restaurant')}", "meal",
                                 cost=dest_restaurants[0].get("avg_cost_per_person", 0)))
            current = lunch_end

    # Hotel check-in
    checkin = current + timedelta(minutes=30)
    rest_end = checkin + timedelta(minutes=90)
    price_night = hotel.get("price_per_night") or 0
    events.append(_event(1, checkin, rest_end, f"Check-in at {hotel.get('name', 'Hotel')}", "hotel",
                         cost=price_night // group_size))
    current = rest_end

    # Evening activities (Day 1)
    evening_acts = [a for a in activities if "evening" in (a.get("tags") or []) or "cultural" == a.get("category")]
    for act in evening_acts[:1]:
        act_dur_raw = act.get("duration_minutes") or 90
        try:
            act_dur = int(act_dur_raw)
        except (ValueError, TypeError):
            act_dur = 90
        act_end = current + timedelta(minutes=act_dur)
        events.append(_event(1, current, act_end, act.get("name", "Activity"), "activity",
                             cost=act.get("cost_per_person", 0)))
        current = act_end

    # Dinner
    events.append(_event(1, current, current + timedelta(minutes=60), "Dinner", "meal"))

    # Day 2
    current = datetime(2026, 1, 2, 7, 30)
    events.append(_event(2, current, current + timedelta(minutes=45), "Breakfast", "meal"))
    current += timedelta(minutes=45)

    # Morning activities (Day 2)
    morning_acts = [a for a in activities if a not in evening_acts]
    for act in morning_acts[:1]:
        act_dur_raw = act.get("duration_minutes") or 180
        try:
            act_dur = int(act_dur_raw)
        except (ValueError, TypeError):
            act_dur = 180
        act_end = current + timedelta(minutes=act_dur)
        events.append(_event(2, current, act_end, act.get("name", "Activity"), "activity",
                             cost=act.get("cost_per_person", 0)))
        current = act_end

    # Rest + lunch
    events.append(_event(2, current, current + timedelta(minutes=60), "Freshen up", "rest"))
    current += timedelta(minutes=60)
    events.append(_event(2, current, current + timedelta(minutes=60), "Lunch", "meal"))
    current += timedelta(minutes=60)

    # Return journey
    return_end = current + timedelta(minutes=drive_minutes)
    events.append(_event(2, current, return_end, f"Return to {route.get('origin', 'Origin')}", "travel"))

    return events


def _event(day: int, start: datetime, end: datetime, title: str, event_type: str, cost: int = 0) -> dict:
    try:
        cost = int(cost)
    except (ValueError, TypeError):
        cost = 0
    return {
        "day": day,
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "title": title,
        "type": event_type,
        **({"cost": cost} if cost else {}),
    }
