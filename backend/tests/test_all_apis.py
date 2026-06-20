"""
TripGraph API Test Suite
Tests: Health, Config, parse-chat, generate-itinerary, simulate-delay,
       ORS (geocode + routing), Geoapify (places/hotels), OpenWeatherMap,
       Neo4j (knowledge graph), Gemini LLM
Run: python -m pytest backend/tests/test_all_apis.py -v
Or directly: python backend/tests/test_all_apis.py
"""
import os, sys, json, time, traceback
from pathlib import Path
from datetime import datetime

# ── env & path setup ─────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]   # Project root
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / "backend" / ".env")

import requests

BACKEND_URL = "http://localhost:8001"
TIMEOUT     = 90   # seconds for LLM calls

# ── helpers ───────────────────────────────────────────────────────────────────
PASS  = "✅  PASS"
FAIL  = "❌  FAIL"
SKIP  = "⚠️   SKIP"
SEP   = "─" * 60

results: list[dict] = []
GENERATED_ITINERARY = None


def record(name: str, passed: bool, detail: str = "", skipped: bool = False):
    status = SKIP if skipped else (PASS if passed else FAIL)
    print(f"  {status}  {name}")
    if detail:
        for line in detail.splitlines():
            print(f"           {line}")
    results.append({"name": name, "passed": passed, "skipped": skipped, "detail": detail})

def section(title: str):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

# ══════════════════════════════════════════════════════════════════════════════
# 1. Backend health & config
# ══════════════════════════════════════════════════════════════════════════════
def test_backend_health():
    section("1. Backend Health & Config")
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        ok = r.status_code == 200 and r.json().get("status") == "healthy"
        record("GET /health", ok, f"status={r.status_code}  body={r.text[:120]}")
    except Exception as e:
        record("GET /health", False, str(e))

    try:
        r = requests.get(f"{BACKEND_URL}/api/config", timeout=5)
        ok = r.status_code == 200 and "pipeline_mode" in r.json()
        record("GET /api/config", ok, f"body={r.text[:120]}")
    except Exception as e:
        record("GET /api/config", False, str(e))

    try:
        r = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        ok = r.status_code == 200
        record("GET /docs (Swagger UI)", ok, f"status={r.status_code}")
    except Exception as e:
        record("GET /docs (Swagger UI)", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# 2. parse-chat endpoint
# ══════════════════════════════════════════════════════════════════════════════
def test_parse_chat():
    section("2. POST /api/parse-chat  (LLM — Gemini)")
    payload = {
        "chat_messages": [
            "Guys Rishikesh this weekend? I can do ₹15k max",
            "Yes! But I can't do night driving please",
            "Need rafting for sure, and good cafes",
            "Back by Monday morning sharp"
        ]
    }
    try:
        t0 = time.time()
        r = requests.post(f"{BACKEND_URL}/api/parse-chat", json=payload, timeout=TIMEOUT)
        elapsed = round(time.time() - t0, 2)
        ok = r.status_code == 200
        if ok:
            data = r.json()
            has_constraints = "extracted_constraints" in data
            record("parse-chat — status 200", True, f"elapsed={elapsed}s")
            record("parse-chat — extracted_constraints present", has_constraints,
                   json.dumps(data.get("extracted_constraints", {}), indent=2)[:300])
            record("parse-chat — missing_fields list present", "missing_fields" in data)
            record("parse-chat — conflict_report present", "conflict_report" in data)
        else:
            record("parse-chat — status 200", False,
                   f"status={r.status_code}  body={r.text[:400]}")
    except Exception as e:
        record("parse-chat", False, traceback.format_exc()[-400:])

# ══════════════════════════════════════════════════════════════════════════════
# 3. generate-itinerary endpoint
# ══════════════════════════════════════════════════════════════════════════════
SAMPLE_CONSTRAINTS = {
    "origin": "Gurugram",
    "destination": None,
    "destination_type": "mountains",
    "budget_per_person": 15000,
    "trip_duration": "weekend",
    "transport_preference": ["cab_with_driver"],
    "avoid_night_driving": True,
    "must_include": ["rafting", "cafes"],
    "return_deadline": "Monday morning",
    "hotel_tier": "comfort",
    "group_size": 4,
    "risk_tolerance": "medium",
    "special_requirements": []
}

def test_generate_itinerary():
    section("3. POST /api/generate-itinerary  (LLM + Agentic Pipeline)")
    payload = {"constraints": SAMPLE_CONSTRAINTS}
    try:
        t0 = time.time()
        r = requests.post(f"{BACKEND_URL}/api/generate-itinerary", json=payload, timeout=TIMEOUT)
        elapsed = round(time.time() - t0, 2)
        ok = r.status_code == 200
        if ok:
            data = r.json()
            global GENERATED_ITINERARY
            GENERATED_ITINERARY = data.get("recommended_itinerary")
            record("generate-itinerary — status 200", True, f"elapsed={elapsed}s")
            record("generate-itinerary — recommended_itinerary key",
                   "recommended_itinerary" in data)
            record("generate-itinerary — timeline present",
                   bool(data.get("timeline")),
                   f"events={len(data.get('timeline', []))}")
            record("generate-itinerary — map_points present",
                   bool(data.get("map_points")),
                   f"points={len(data.get('map_points', []))}")
            record("generate-itinerary — cost_breakdown present",
                   bool(data.get("cost_breakdown")))
            record("generate-itinerary — score_breakdown present",
                   bool(data.get("score_breakdown")))
            record("generate-itinerary — alternatives present",
                   "alternatives" in data,
                   f"count={len(data.get('alternatives', []))}")
        else:
            record("generate-itinerary — status 200", False,
                   f"status={r.status_code}  body={r.text[:500]}")
    except Exception as e:
        record("generate-itinerary", False, traceback.format_exc()[-400:])

# ══════════════════════════════════════════════════════════════════════════════
# 4. simulate-delay endpoint
# ══════════════════════════════════════════════════════════════════════════════
def test_simulate_delay():
    section("4. POST /api/simulate-delay  (LLM Replanner)")
    payload = {
        "delay_type": "departure_delay",
        "delay_minutes": 90,
        "constraints": SAMPLE_CONSTRAINTS,
        "selected_itinerary": GENERATED_ITINERARY
    }
    try:
        t0 = time.time()
        r = requests.post(f"{BACKEND_URL}/api/simulate-delay", json=payload, timeout=TIMEOUT)
        elapsed = round(time.time() - t0, 2)
        ok = r.status_code == 200
        if ok:
            data = r.json()
            record("simulate-delay — status 200", True, f"elapsed={elapsed}s")
            record("simulate-delay — changes list present",
                   bool(data.get("changes")),
                   f"count={len(data.get('changes', []))}")
            record("simulate-delay — explanation present",
                   bool(data.get("explanation")))
        else:
            record("simulate-delay — status 200", False,
                   f"status={r.status_code}  body={r.text[:400]}")
    except Exception as e:
        record("simulate-delay", False, traceback.format_exc()[-400:])

# ══════════════════════════════════════════════════════════════════════════════
# 5. ORS (OpenRouteService) — geocode + routing
# ══════════════════════════════════════════════════════════════════════════════
def test_ors():
    section("5. ORS — Geocode + Routing  (api.openrouteservice.org)")
    sys.path.insert(0, str(ROOT))
    try:
        from backend.api_clients.ors_client import ORSClient

        # Geocode
        coords = ORSClient.geocode("Rishikesh")
        ok_geo = coords is not None and "lat" in coords and "lng" in coords
        record("ORS geocode('Rishikesh')", ok_geo,
               f"result={coords}")

        # Routing Gurugram → Rishikesh
        if ok_geo:
            # Gurugram coords
            g_coords = ORSClient.geocode("Gurugram")
            if g_coords:
                route = ORSClient.get_route(
                    origin_lng=g_coords["lng"], origin_lat=g_coords["lat"],
                    dest_lng=coords["lng"],     dest_lat=coords["lat"]
                )
                ok_route = route is not None and "distance_km" in route
                record("ORS route(Gurugram→Rishikesh)", ok_route,
                       f"result={route}")
            else:
                record("ORS route(Gurugram→Rishikesh)", False, "Geocode for Gurugram failed")
        else:
            record("ORS route(Gurugram→Rishikesh)", False, "Skipped — geocode failed")
    except Exception as e:
        record("ORS", False, traceback.format_exc()[-400:])

# ══════════════════════════════════════════════════════════════════════════════
# 6. Geoapify — places / hotels / activities
# ══════════════════════════════════════════════════════════════════════════════
def test_geoapify():
    section("6. Geoapify — Places API  (api.geoapify.com)")
    try:
        from backend.api_clients.geoapify_client import GeoapifyClient

        # Rishikesh lat/lng
        lat, lng = 30.0869, 78.2676

        hotels = GeoapifyClient.get_hotels(lat, lng, limit=3)
        ok_hotels = isinstance(hotels, list)
        record("Geoapify get_hotels(Rishikesh)", ok_hotels,
               f"count={len(hotels)}  first={hotels[0] if hotels else 'none'}")

        activities = GeoapifyClient.get_activities(lat, lng, limit=3)
        ok_act = isinstance(activities, list)
        record("Geoapify get_activities(Rishikesh)", ok_act,
               f"count={len(activities)}  first={activities[0] if activities else 'none'}")
    except Exception as e:
        record("Geoapify", False, traceback.format_exc()[-400:])

# ══════════════════════════════════════════════════════════════════════════════
# 7. OpenWeatherMap — current weather
# ══════════════════════════════════════════════════════════════════════════════
def test_openweathermap():
    section("7. OpenWeatherMap  (api.openweathermap.org)")
    try:
        from backend.api_clients.openweathermap_client import OpenWeatherMapClient

        # Rishikesh
        weather = OpenWeatherMapClient.get_weather(lat=30.0869, lng=78.2676)
        ok = weather is not None and "temp" in weather
        record("OWM get_weather(Rishikesh)", ok,
               f"result={weather}")

        # Gurugram
        weather2 = OpenWeatherMapClient.get_weather(lat=28.4595, lng=77.0266)
        ok2 = weather2 is not None
        record("OWM get_weather(Gurugram)", ok2, f"result={weather2}")
    except Exception as e:
        record("OpenWeatherMap", False, traceback.format_exc()[-400:])

# ══════════════════════════════════════════════════════════════════════════════
# 8. Neo4j Knowledge Graph connectivity
# ══════════════════════════════════════════════════════════════════════════════
def test_neo4j():
    section("8. Neo4j Knowledge Graph  (bolt://localhost:7687)")
    try:
        from backend.knowledge_graph.connection import get_driver, close_driver
        driver = get_driver()
        # Simple query
        with driver.session() as session:
            result = session.run("RETURN 1 AS n")
            val = result.single()["n"]
        ok = val == 1
        record("Neo4j bolt connection", ok, f"RETURN 1 => {val}")
        close_driver()
    except Exception as e:
        err = str(e)
        # Connection refused is expected if Neo4j isn't running
        if "ServiceUnavailable" in err or "Connection refused" in err or "Failed to" in err:
            record("Neo4j bolt connection", False,
                   "⚠ Neo4j not reachable (is Docker running?)\n" + err[:200],
                   skipped=False)
        else:
            record("Neo4j bolt connection", False, err[:300])

# ══════════════════════════════════════════════════════════════════════════════
# 9. Gemini LLM (direct call — NOT via backend route)
# ══════════════════════════════════════════════════════════════════════════════
def test_gemini_llm():
    section("9. Gemini LLM  (direct via LangChain client)")
    try:
        from backend.agents.llm_client import get_llm, extract_text_content
        llm = get_llm()
        from langchain_core.messages import HumanMessage
        t0 = time.time()
        response = llm.invoke([HumanMessage(content="Reply with exactly: TRIPGRAPH_OK")])
        elapsed = round(time.time() - t0, 2)
        text = extract_text_content(response.content)
        ok = "TRIPGRAPH_OK" in text
        record("Gemini LLM invoke", ok, f"elapsed={elapsed}s  response='{text.strip()[:80]}'")
    except Exception as e:
        record("Gemini LLM invoke", False, traceback.format_exc()[-400:])

# ══════════════════════════════════════════════════════════════════════════════
# 10. Pipeline mode switch (agentic ↔ augmented)
# ══════════════════════════════════════════════════════════════════════════════
def test_pipeline_config():
    section("10. Pipeline Config Switching")
    try:
        # Set to augmented
        r = requests.post(f"{BACKEND_URL}/api/config",
                          json={"pipeline_mode": "augmented"}, timeout=5)
        ok1 = r.status_code == 200 and r.json().get("pipeline_mode") == "augmented"
        record("POST /api/config  (set=augmented)", ok1, r.text[:100])

        # Set back to agentic
        r2 = requests.post(f"{BACKEND_URL}/api/config",
                           json={"pipeline_mode": "agentic"}, timeout=5)
        ok2 = r2.status_code == 200 and r2.json().get("pipeline_mode") == "agentic"
        record("POST /api/config  (set=agentic)", ok2, r2.text[:100])

        # Try invalid mode
        r3 = requests.post(f"{BACKEND_URL}/api/config",
                           json={"pipeline_mode": "invalid_mode"}, timeout=5)
        ok3 = r3.status_code == 400
        record("POST /api/config  (invalid → 400)", ok3, f"status={r3.status_code}")
    except Exception as e:
        record("Pipeline Config", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{'═'*60}")
    print(f"  TripGraph AI — Full API Test Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Backend: {BACKEND_URL}")
    print(f"{'═'*60}")

    test_backend_health()
    test_parse_chat()
    test_generate_itinerary()
    test_simulate_delay()
    test_ors()
    test_geoapify()
    test_openweathermap()
    test_neo4j()
    test_gemini_llm()
    test_pipeline_config()

    # ── Summary ──────────────────────────────────────────────────────────────
    total   = len(results)
    passed  = sum(1 for r in results if r["passed"] and not r["skipped"])
    failed  = sum(1 for r in results if not r["passed"] and not r["skipped"])
    skipped = sum(1 for r in results if r["skipped"])

    print(f"\n{'═'*60}")
    print(f"  SUMMARY")
    print(f"{'═'*60}")
    print(f"  Total   : {total}")
    print(f"  Passed  : {passed} ✅")
    print(f"  Failed  : {failed} ❌")
    print(f"  Skipped : {skipped} ⚠️")
    print(f"{'═'*60}")

    if failed:
        print("\n  Failed tests:")
        for r in results:
            if not r["passed"] and not r["skipped"]:
                print(f"    ❌  {r['name']}")
                if r["detail"]:
                    print(f"       {r['detail'].splitlines()[0][:100]}")

    print()
    sys.exit(0 if failed == 0 else 1)
