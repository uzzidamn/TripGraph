"""Hotel-deals agent — surfaces current pricing & discount intelligence on top
of the KG/Geoapify hotel candidates. Used by the enricher to highlight
"unusually good rate" picks even when the user has a comfort/expedition tier.

Silent until a hotel-pricing provider key is configured
(see backend/api_clients/hotel_deals_client.py).
"""
from datetime import date, timedelta

from backend.api_clients.hotel_deals_client import HotelDealsClient
from backend.agents.state import TripState


def deals_agent_node(state: TripState) -> dict:
    """Look up live hotel deals at the trip's primary destination.

    Returns {'hotel_deals': APIResult}.
    """
    constraints = state.get("extracted_constraints") or {}
    destination = constraints.get("destination")
    if not destination:
        return {"hotel_deals": {"available": False, "reason": "NO_DESTINATION", "provider": "none", "data": None}}

    checkin = constraints.get("checkin_date") or (date.today() + timedelta(days=14)).isoformat()
    checkout = constraints.get("checkout_date") or (date.today() + timedelta(days=16)).isoformat()
    rooms = max(1, int(constraints.get("group_size") or 2) // 2)
    tier = constraints.get("hotel_tier")

    result = HotelDealsClient.find_deals(
        destination=destination,
        checkin_date=checkin,
        checkout_date=checkout,
        rooms=rooms,
        guests=int(constraints.get("group_size") or 2),
        tier=tier,
    )
    return {"hotel_deals": result}
