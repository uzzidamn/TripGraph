"""Terminal Resolver — identifies the origin/destination terminals (airports,
railway stations) and computes first/last-mile travel times so the Architect
can plan realistic Day 1 departures and return-day transitions.

Runs AFTER mode_planner (which decides flight/train/drive) and BEFORE the
Architect. Only activates when the chosen mode is flight or train.

Uses Google Places Text Search to find the nearest commercial airport or
major railway station, then Google Routes to compute driving time from the
city center to the terminal.

Output → state['terminal_info']:
{
    "origin": {
        "city": "Chandigarh",
        "city_center": {"lat": 30.73, "lng": 76.77},
        "terminal": {
            "type": "airport",
            "name": "Chandigarh International Airport (IXC)",
            "lat": 30.67, "lng": 76.78,
            "travel_from_center_minutes": 25,
            "travel_from_center_km": 12.5
        }
    },
    "destination": { ... same shape ... }
}
"""
from backend.agents.state import TripState
from backend.api_clients.google_places_client import GooglePlacesClient, GOOGLE_MAPS_API_KEY
from backend.api_clients.ors_client import ORSClient


def _geocode_city(city_name: str) -> dict | None:
    geo = ORSClient.geocode(city_name)
    if geo:
        return {"lat": geo["lat"], "lng": geo["lng"]}
    return None


def _find_terminal(city_name: str, city_lat: float, city_lng: float,
                   mode: str) -> dict | None:
    if mode == "flight":
        query = f"airport near {city_name}"
        terminal_type = "airport"
    elif mode in ("train", "rail"):
        query = f"railway station {city_name}"
        terminal_type = "railway_station"
    else:
        return None

    if not GOOGLE_MAPS_API_KEY:
        return _fallback_terminal(city_name, mode, terminal_type)

    results = GooglePlacesClient._search(query, city_lat, city_lng,
                                         radius_m=50000, limit=3)
    if not results:
        return _fallback_terminal(city_name, mode, terminal_type)

    best = results[0]
    t_lat = best.get("lat")
    t_lng = best.get("lng")

    travel_minutes = 30
    travel_km = 15.0
    if t_lat and t_lng:
        try:
            from backend.api_clients.google_routes_client import GoogleRoutesClient
            matrix = GoogleRoutesClient.distance_matrix(
                [{"lat": city_lat, "lng": city_lng, "name": "center"},
                 {"lat": t_lat, "lng": t_lng, "name": best["name"]}],
                max_stops=2,
            )
            if matrix and matrix[0][1]:
                travel_minutes = matrix[0][1].get("minutes", 30)
                travel_km = matrix[0][1].get("km", 15.0)
        except Exception as e:
            print(f"  ⚠️  Terminal distance calc failed: {e}")
            import math
            dx = (t_lat - city_lat)
            dy = (t_lng - city_lng)
            travel_km = round(math.sqrt(dx**2 + dy**2) * 111 * 1.3, 1)
            travel_minutes = max(15, round(travel_km / 0.6))

    return {
        "type": terminal_type,
        "name": best.get("name", f"{city_name} {terminal_type}"),
        "lat": t_lat,
        "lng": t_lng,
        "travel_from_center_minutes": travel_minutes,
        "travel_from_center_km": round(travel_km, 1),
    }


def _fallback_terminal(city_name: str, mode: str, terminal_type: str) -> dict:
    geo = ORSClient.geocode(f"{city_name} {'airport' if mode == 'flight' else 'railway station'}")
    lat = geo["lat"] if geo else None
    lng = geo["lng"] if geo else None
    name = f"{city_name} {'Airport' if mode == 'flight' else 'Railway Station'}"
    return {
        "type": terminal_type,
        "name": name,
        "lat": lat,
        "lng": lng,
        "travel_from_center_minutes": 30,
        "travel_from_center_km": 15.0,
    }


def terminal_resolver_node(state: TripState) -> dict:
    constraints = state.get("extracted_constraints") or {}
    selected = state.get("selected_itinerary") or {}
    transport = selected.get("transport") or {}
    mode = (transport.get("mode") or "drive").lower()

    if mode not in ("flight", "train", "rail"):
        flights = state.get("flights") or {}
        adv = flights.get("advisory") or {}
        if adv.get("recommended_mode") == "fly":
            mode = "flight"
        else:
            return {}

    origin_name = constraints.get("origin") or "Delhi"
    dest_name = constraints.get("destination") or ""
    if not dest_name:
        routes = state.get("route_candidates") or []
        if routes:
            dest_name = routes[0].get("destination", "")

    info = {}

    origin_geo = _geocode_city(origin_name)
    if origin_geo:
        origin_terminal = _find_terminal(origin_name, origin_geo["lat"],
                                         origin_geo["lng"], mode)
        info["origin"] = {
            "city": origin_name,
            "city_center": origin_geo,
            "terminal": origin_terminal,
        }

    if dest_name:
        dest_geo = _geocode_city(dest_name)
        if dest_geo:
            dest_terminal = _find_terminal(dest_name, dest_geo["lat"],
                                           dest_geo["lng"], mode)
            info["destination"] = {
                "city": dest_name,
                "city_center": dest_geo,
                "terminal": dest_terminal,
            }

    if info:
        o = info.get("origin", {}).get("terminal", {})
        d = info.get("destination", {}).get("terminal", {})
        print(f"  🚏 Terminal resolver: {o.get('name', '?')} ({o.get('travel_from_center_minutes', '?')} min from center) "
              f"→ {d.get('name', '?')} ({d.get('travel_from_center_minutes', '?')} min to center)")

    return {"terminal_info": info} if info else {}
