"""
Agent: Web Enricher
Fires between data_retriever and plan_itinerary when the requested destination
has fewer than 2 hotels in seed data (i.e., it is not a pre-seeded location).

Runs 4 targeted searches (hotels, activities, transport, weather/events),
asks Claude to structure the raw snippets into our schema, then merges the
live results into the candidate lists that the planner will score.
"""
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.agents.state import TripState
from backend.tools.web_search_tool import web_search
from backend.utils.currency import get_currency

_SCHEMA_TEMPLATE = """\
{{
  "hotels": [
    {{"name": "...", "tier": "budget|comfort|luxury", "price_per_night": 2500, "destination": "{dest}"}}
  ],
  "activities": [
    {{"name": "...", "type": "adventure|cultural|sightseeing|food", "cost_per_person": 800,
      "destination": "{dest}", "duration_hours": 2, "tags": ["..."]}}
  ],
  "transport": [
    {{"mode": "{transport_mode}", "tier": "budget|comfort|luxury",
      "cost_per_person": 5000, "duration_hours": {travel_hours}, "route_id": "{route_id}"}}
  ],
  "route": {{
    "route_id": "{route_id}",
    "origin": "{origin}",
    "destination": "{dest}",
    "distance_km": {distance_km},
    "duration_hours": {travel_hours},
    "destination_type": "mountains|beach|heritage|pilgrimage|wildlife|hill_station",
    "origin_lat": 0.0,
    "origin_lng": 0.0,
    "dest_lat": 0.0,
    "dest_lng": 0.0
  }},
  "weather": "Mild, 18-28°C in June.",
  "events": ["Annual festival in July"]
}}"""


# Approximate thresholds to pick sensible default transport
_FLIGHT_THRESHOLD_KM = 700   # force flight above this distance or for international
_TRAIN_THRESHOLD_KM  = 300   # prefer train between 300-700 km


_CITY_COUNTRY: dict[str, str] = {}
_CC_GROUPS = [
    ("IN", {"delhi","new delhi","mumbai","bangalore","bengaluru","chennai","hyderabad",
            "kolkata","pune","ahmedabad","jaipur","surat","lucknow","kanpur","nagpur",
            "indore","bhopal","patna","vadodara","goa","panaji","kochi","coimbatore",
            "visakhapatnam","vijayawada","agra","varanasi","allahabad","prayagraj",
            "amritsar","chandigarh","ludhiana","jalandhar","rishikesh","haridwar",
            "dehradun","mussoorie","nainital","manali","shimla","dharamshala","kasol",
            "darjeeling","gangtok","leh","ladakh","srinagar","jammu","kargil",
            "ooty","kodaikanal","coorg","madikeri","chikmagalur","mysore","mysuru",
            "gurugram","gurgaon","noida","faridabad","ghaziabad","meerut",
            "ranchi","bhubaneswar","puri","guwahati","shillong","imphal",
            "raipur","jodhpur","udaipur","ajmer","bikaner","kota","alwar",
            "mathura","vrindavan","ayodhya","tirupati","shirdi","nashik",
            "aurangabad","kolhapur","solapur","hubli","mangalore",
            "thiruvananthapuram","kozhikode","thrissur","madurai","trichy","salem",
            "siliguri","asansol","durgapur","howrah","kharagpur",
            "bhopal","gwalior","jabalpur","ujjain","rewa",
            "warangal","rajkot","bhavnagar","anand","surat","valsad"}),
    ("AU", {"sydney","melbourne","brisbane","perth","adelaide","canberra","gold coast",
            "hobart","darwin","cairns","geelong","newcastle","townsville",
            # Australian states & territories
            "new south wales","victoria","queensland","western australia",
            "south australia","tasmania","northern territory","australian capital territory",
            "nsw","vic","qld","wa","sa","tas","nt","act"}),
    ("NZ", {"auckland","wellington","christchurch","hamilton","dunedin"}),
    ("GB", {"london","manchester","birmingham","edinburgh","glasgow","bristol","leeds",
            # UK regions / countries
            "england","scotland","wales","northern ireland",
            "yorkshire","cornwall","devon","kent","essex","surrey",
            "lancashire","oxfordshire","cambridgeshire"}),
    ("US", {"new york","new york city","nyc","ny","los angeles","la",
            "san francisco","sf","chicago","houston","phoenix","seattle",
            "boston","miami","washington","dc","las vegas","dallas",
            "new orleans","denver","atlanta","portland","austin","nashville",
            "minneapolis","detroit","philadelphia",
            # US states
            "california","texas","florida","new york state","illinois","pennsylvania",
            "ohio","georgia","north carolina","michigan","new jersey","virginia",
            "washington state","arizona","massachusetts","tennessee","indiana",
            "missouri","maryland","wisconsin","colorado","minnesota","south carolina",
            "alabama","louisiana","kentucky","oregon","oklahoma","connecticut",
            "utah","iowa","nevada","arkansas","mississippi","kansas","new mexico",
            "nebraska","idaho","west virginia","hawaii","maine","new hampshire",
            "montana","rhode island","delaware","south dakota","north dakota",
            "alaska","vermont","wyoming"}),
    ("CA", {"toronto","vancouver","montreal","calgary","ottawa","edmonton",
            # Canadian provinces & territories
            "ontario","quebec","british columbia","alberta","manitoba",
            "saskatchewan","nova scotia","new brunswick","newfoundland",
            "prince edward island","northwest territories","yukon","nunavut",
            "bc","pei"}),
    ("JP", {"tokyo","osaka","kyoto","yokohama","nagoya","sapporo","fukuoka"}),
    ("EU", {"paris","lyon","marseille","amsterdam","rotterdam","brussels","antwerp",
            "berlin","munich","hamburg","frankfurt","cologne","vienna","zurich","geneva",
            "rome","milan","florence","venice","naples","barcelona","madrid","lisbon",
            "porto","athens","prague","warsaw","budapest","stockholm","oslo","copenhagen",
            "helsinki","dublin","nice","bordeaux","toulouse",
            # EU regions / states
            "bavaria","saxony","bavaria","rhineland","westphalia","baden","württemberg",
            "tuscany","lombardy","sicily","sardinia","veneto","piedmont","calabria",
            "catalonia","andalusia","castile","basque country","galicia",
            "provence","alsace","brittany","normandy","occitanie",
            "flanders","wallonia","andalucia"}),
    ("SG", {"singapore"}),
    ("TH", {"bangkok","phuket","chiang mai","pattaya","krabi"}),
    ("AE", {"dubai","abu dhabi","sharjah"}),
    ("RU", {"moscow","st petersburg","novosibirsk"}),
    ("ZA", {"cape town","johannesburg","durban","pretoria"}),
    ("CN", {"beijing","shanghai","guangzhou","shenzhen","chengdu","hong kong","macau"}),
    ("KR", {"seoul","busan","incheon","jeju"}),
    ("MY", {"kuala lumpur","penang","johor bahru","kota kinabalu"}),
    ("ID", {"jakarta","bali","surabaya","yogyakarta","medan"}),
    ("VN", {"ho chi minh","hanoi","da nang","hoi an"}),
    ("PH", {"manila","cebu","davao","boracay"}),
    ("EG", {"cairo","alexandria","luxor","aswan","hurghada"}),
    ("KE", {"nairobi","mombasa","kisumu"}),
    ("BR", {"sao paulo","rio de janeiro","brasilia","salvador","fortaleza"}),
    ("MX", {"mexico city","cancun","guadalajara","monterrey","playa del carmen"}),
]
for _code, _cities in _CC_GROUPS:
    for _c in _cities:
        _CITY_COUNTRY[_c] = _code


def _resolve_country(city: str) -> str | None:
    key = city.lower().strip()
    if key in _CITY_COUNTRY:
        return _CITY_COUNTRY[key]
    for name, code in _CITY_COUNTRY.items():
        if name.startswith(key) or key.startswith(name):
            return code
    return None


def _transport_hint(origin: str, destination: str) -> tuple[str, int, int]:
    """Return (mode, approx_travel_hours, approx_distance_km) based on common sense rules."""
    oc = _resolve_country(origin)
    dc = _resolve_country(destination)

    # Unknown destination + known origin → assume same country.
    # Both unknown → also assume domestic (user likely testing a domestic route;
    # the web enricher LLM will apply a flight if the actual distance warrants it).
    if dc is None and oc in ("IN", "US", "AU", "CA", "GB", "EU"):
        is_international = False
    elif oc is None and dc is None:
        is_international = False
    else:
        is_international = (oc is None or dc is None or oc != dc)

    if is_international:
        return "flight", 5, 3000
    return "cab", 6, 400


def _needs_enrichment(state: TripState, destination: str) -> bool:
    dest_hotels = [
        h for h in state.get("hotel_candidates", [])
        if h.get("destination") == destination
    ]
    dest_routes = [
        r for r in state.get("route_candidates", [])
        if r.get("destination") == destination
    ]
    return len(dest_hotels) < 2 or len(dest_routes) == 0


def _route_id(origin: str, destination: str) -> str:
    def slug(s): return s.lower().replace(" ", "_")
    return f"{slug(origin)}_{slug(destination)}"


def _structure_with_llm(raw_text: str, origin: str, destination: str,
                        preferred_mode: str | None = None) -> dict:
    """Use Claude to convert raw search snippets into our typed schema."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        rid = _route_id(origin, destination)
        hint_mode, hours, km = _transport_hint(origin, destination)
        # User's explicit choice overrides the hint
        mode = preferred_mode or hint_mode
        schema = _SCHEMA_TEMPLATE.format(
            dest=destination, origin=origin, route_id=rid,
            transport_mode=mode, travel_hours=hours, distance_km=km,
        )

        currency_code, currency_symbol, _ = get_currency(origin)
        mode_instruction = (
            f"- Transport mode MUST be '{mode}' — the user explicitly requested this. "
            f"Do not change it to flight or any other mode.\n"
            if preferred_mode else
            f"- Transport: if {destination} is international or >700 km from {origin}, set mode to 'flight'.\n"
        )
        prompt = (
            f"Travel data for {origin} to {destination}:\n\n"
            f"{raw_text[:3000]}\n\n"
            f"IMPORTANT:\n"
            f"- All prices must be in {currency_code} ({currency_symbol}), the traveller's home currency.\n"
            f"  If local prices are in a different currency, convert to {currency_code} at current rates.\n"
            f"{mode_instruction}"
            f"- transport.cost_per_person = one-way fare per traveller in {currency_code} "
            f"(e.g. economy ticket = actual price per person, NOT total for group).\n"
            f"- hotel.price_per_night = cost per room per night in {currency_code}.\n"
            f"- Use real GPS coordinates: origin_lat/origin_lng for {origin}, dest_lat/dest_lng for {destination}.\n\n"
            f"Return ONLY this JSON:\n{schema}\n\nJSON only."
        )

        response = client.messages.create(
            model=os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text

        # Strip optional markdown fences before parsing
        text = re.sub(r"```(?:json)?", "", text).strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())

    except Exception as e:
        print(f"  ⚠️  Web enricher LLM structuring failed ({type(e).__name__}: {e})")

    return {}


def web_enricher_node(state: TripState) -> dict:
    """
    Search the web for live hotel/activity/transport data when the destination
    is not covered by seed data, then merge results into candidate lists.
    """
    constraints = state.get("extracted_constraints", {})
    destination = constraints.get("destination")
    origin = constraints.get("origin", "Gurugram")

    if not destination:
        print("  ⏭️  Web enricher: no destination set, skipping")
        return {"web_enriched": False, "web_context": {}}

    if not _needs_enrichment(state, destination):
        print(f"  ⏭️  Web enricher: sufficient seed data for {destination}, skipping")
        return {"web_enriched": False, "web_context": {}}

    print(f"  🌐 Web enricher: fetching live data for {destination} from {origin}…")

    preferred_modes = constraints.get("transport_preference") or []
    preferred_mode = preferred_modes[0] if preferred_modes else None
    hint_mode, _, _ = _transport_hint(origin, destination)
    search_mode = preferred_mode or hint_mode

    _MODE_KEYWORD = {
        "flight": "flight airline",
        "train": "train rail Amtrak",
        "bus": "bus coach",
        "cab_with_driver": "cab taxi hire",
        "self_drive": "drive road trip car rental",
    }
    mode_kw = _MODE_KEYWORD.get(search_mode, search_mode)
    transport_query = f"{mode_kw} {origin} to {destination} price duration cost 2025"
    queries = [
        f"best hotels in {destination} price per night 2025 INR",
        f"top tourist attractions things to do {destination} cost entry fee",
        transport_query,
        f"weather {destination} June July events festivals 2025",
    ]

    # Run all searches in parallel to cut latency from ~40s → ~12s
    raw_parts = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        future_to_q = {pool.submit(web_search, q): q for q in queries}
        for future in as_completed(future_to_q):
            q = future_to_q[future]
            snippet = future.result()
            if snippet:
                raw_parts.append(f"=== {q} ===\n{snippet}")

    if not raw_parts:
        print("  ⚠️  Web enricher: all searches returned empty, skipping enrichment")
        return {"web_enriched": False, "web_context": {}}

    enriched = _structure_with_llm("\n\n".join(raw_parts), origin, destination,
                                   preferred_mode=preferred_mode)

    if not enriched:
        return {"web_enriched": False, "web_context": {}}

    # --- Merge into existing candidate lists ---
    existing_routes = list(state.get("route_candidates", []))
    new_route = enriched.get("route")
    if new_route:
        existing_ids = {r.get("route_id") for r in existing_routes}
        if new_route.get("route_id") not in existing_ids:
            existing_routes = [new_route, *existing_routes]

    merged_hotels = list(state.get("hotel_candidates", [])) + enriched.get("hotels", [])
    merged_activities = list(state.get("activity_candidates", [])) + enriched.get("activities", [])
    merged_transport = list(state.get("transport_candidates", [])) + enriched.get("transport", [])

    web_ctx = {
        "destination": destination,
        "weather": enriched.get("weather", ""),
        "events": enriched.get("events", []),
        "source": "live_web_search",
    }

    n_h = len(enriched.get("hotels", []))
    n_a = len(enriched.get("activities", []))
    n_t = len(enriched.get("transport", []))
    print(f"  ✅ Web enricher: +{n_h} hotels, +{n_a} activities, +{n_t} transport options for {destination}")

    return {
        "route_candidates": existing_routes,
        "hotel_candidates": merged_hotels,
        "activity_candidates": merged_activities,
        "transport_candidates": merged_transport,
        "web_enriched": True,
        "web_context": web_ctx,
    }
