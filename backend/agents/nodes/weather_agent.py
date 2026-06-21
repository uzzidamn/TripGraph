"""Weather agent — fetches a 3-day forecast for the trip's destination and
key waypoints so the timeline can render weather chips per day and the
fatigue adjuster can factor in rain/heat.

Returns state.weather_forecast = {
    "destination": {<YYYY-MM-DD>: {temp_min, temp_max, description, summary, pop_max}},
    "waypoints":   {<waypoint_id>: <same shape>}
}
"""
from backend.api_clients.openweathermap_client import OpenWeatherMapClient
from backend.agents.state import TripState


def weather_agent_node(state: TripState) -> dict:
    routes = state.get("route_candidates") or []
    if not routes:
        return {"weather_forecast": {}}

    out: dict = {}
    # Use the first route's destination as the primary forecast target
    primary = routes[0]
    dest_lat = primary.get("dest_lat")
    dest_lng = primary.get("dest_lng")
    if dest_lat is not None and dest_lng is not None:
        forecast = OpenWeatherMapClient.get_forecast(dest_lat, dest_lng, days=3)
        if forecast:
            out["destination"] = forecast

    # Best-effort per-waypoint snapshots (current weather only — forecast quota is precious)
    waypoints = (state.get("waypoint_candidates") or [])[:3]
    wp_weather: dict = {}
    for w in waypoints:
        wp_id = w.get("waypoint_id")
        if not wp_id or w.get("lat") is None or w.get("lng") is None:
            continue
        cur = OpenWeatherMapClient.get_weather(w["lat"], w["lng"])
        if cur:
            wp_weather[wp_id] = cur
    if wp_weather:
        out["waypoints"] = wp_weather

    return {"weather_forecast": out}
