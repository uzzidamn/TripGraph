"""
Delay-aware replanning engine.
Takes an existing itinerary + delay event → produces adjusted itinerary.
"""
from datetime import datetime, timedelta


def replan_itinerary(itinerary: dict, delay_event: dict, constraints: dict) -> dict:
    """
    Adjust itinerary after a delay event.
    Returns updated itinerary and list of changes made.
    """
    from backend.planner.timeline_generator import generate_timeline

    delay_minutes_raw = delay_event.get("delay_minutes", 0)
    try:
        delay_minutes = int(delay_minutes_raw)
    except (ValueError, TypeError):
        delay_minutes = 0
        
    delay_type = delay_event.get("delay_type", "departure_delay")
    changes = []

    # Re-generate timeline
    timeline = generate_timeline(itinerary)

    # Shift all events by delay amount sequentially
    shifted_timeline = []
    total_slack_recovered = 0
    
    current_delay = delay_minutes
    prev_end = None
    prev_day = None
    new_prev_end = None

    for event in timeline:
        try:
            start = datetime.strptime(event["start_time"], "%H:%M")
            end = datetime.strptime(event["end_time"], "%H:%M")
        except (KeyError, ValueError):
            # Skip invalid events or append as is
            shifted_timeline.append(event)
            continue
            
        duration = (end - start).total_seconds() / 60
        day = event.get("day", 1)

        # Calculate original gap and new start time
        if prev_end is not None and day == prev_day:
            gap = (start - prev_end).total_seconds() / 60
            new_start = new_prev_end + timedelta(minutes=gap)
        else:
            new_start = start + timedelta(minutes=current_delay)

        # Compress if flexible
        if event.get("type") in ["rest", "meal"] and event.get("title") not in ["Breakfast"]:
            # Flexible: compress by up to 50%
            compress = min(current_delay, duration * 0.5)
            if compress > 0:
                duration -= compress
                current_delay -= compress
                total_slack_recovered += compress
                changes.append(f"{event.get('title')} shortened by {int(compress)} minutes")

        new_end = new_start + timedelta(minutes=duration)

        shifted_timeline.append({
            **event,
            "start_time": new_start.strftime("%H:%M"),
            "end_time": new_end.strftime("%H:%M"),
        })

        new_prev_end = new_end
        prev_end = end
        prev_day = day

    # Check if optional events need to be dropped
    if current_delay > 0:
        # Drop optional events
        final_timeline = []
        for event in shifted_timeline:
            # Keep mandatory, drop optional if still over time
            if event.get("type") in ["activity"] and "optional" in event.get("title", "").lower():
                changes.append(f"{event.get('title')} removed due to time constraints")
                continue
            final_timeline.append(event)
        shifted_timeline = final_timeline

    if not changes:
        changes.append(f"All events shifted by {delay_minutes} minutes")

    return {
        "updated_itinerary": {
            **itinerary,
            "timeline": shifted_timeline,
        },
        "changes": changes,
        "delay_absorbed": total_slack_recovered,
        "delay_remaining": current_delay,
    }
