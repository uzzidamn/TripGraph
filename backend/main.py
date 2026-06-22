"""
TripGraph AI — FastAPI Backend Entry Point

Start server:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

API docs (auto-generated):
    http://localhost:8000/docs

Health check:
    http://localhost:8000/health
"""
from dotenv import load_dotenv
# Force-load .env into os.environ at the entry point, overriding any stale/empty
# values inherited from the launching shell. Without override=True, a var that
# was absent when an upstream module first called load_dotenv() could stay unset.
load_dotenv(override=True)

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.chat_routes import router as chat_router
from backend.api.itinerary_routes import router as itinerary_router
from backend.api.refinement_routes import router as refinement_router
from backend.api.replanner_routes import router as replanner_router
from backend.config import settings

app = FastAPI(
    title="TripGraph AI",
    description=(
        "GenAI-Agentic Group Travel Planner API. "
        "Converts WhatsApp-style group chat into structured, constraint-aware itineraries."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow any localhost/127.0.0.1 dev origin on any port.
# Starlette 1.x's allow_origins matching seems to drop the list when the app
# is started under uvicorn in some setups (the list arrives intact via
# `add_middleware` introspection but every preflight returns "Disallowed CORS
# origin"). Using `allow_origin_regex` is more reliable for dev.
#
# allow_credentials is intentionally False — browsers reject "*" / regex
# origins combined with credentials, and the app doesn't use cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Maintenance gate ──────────────────────────────────────────────────────
# When MAINTENANCE_MODE is on, the credit-burning planning endpoints return 503
# so no LLM/API calls fire (protects the owner's keys from public/teammate use).
# The landing page + read-only config endpoints (maptiles, integrations) stay
# live, so the site still looks alive. Owner bypasses by sending the secret
# header X-Tripgraph-Key (set MAINTENANCE_BYPASS_KEY in .env).
_GATED_PATHS = {
    "/api/parse-chat",
    "/api/generate-itinerary",
    "/api/refinement-questions",
    "/api/simulate-delay",
}


def _maintenance_on() -> bool:
    return os.getenv("MAINTENANCE_MODE", "false").strip().lower() in ("1", "true", "yes", "on")


@app.middleware("http")
async def maintenance_gate(request: Request, call_next):
    if (
        _maintenance_on()
        and request.method == "POST"
        and request.url.path in _GATED_PATHS
    ):
        bypass = os.getenv("MAINTENANCE_BYPASS_KEY", "")
        if not bypass or request.headers.get("X-Tripgraph-Key") != bypass:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "TripGraph is in private preview — live planning goes on at the demo.",
                    "maintenance": True,
                },
            )
    return await call_next(request)


# Route modules
app.include_router(chat_router)
app.include_router(itinerary_router)
app.include_router(refinement_router)
app.include_router(replanner_router)

# Config request model
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from backend.api.test_client_html import HTML_CONTENT

class ConfigUpdate(BaseModel):
    pipeline_mode: str

@app.get("/api/config", tags=["Config"])
async def get_config() -> dict:
    """Get the current active pipeline mode."""
    return {"pipeline_mode": settings.PIPELINE_MODE}

@app.post("/api/config", tags=["Config"])
async def set_config(config: ConfigUpdate) -> dict:
    """Set the active pipeline mode dynamically."""
    if config.pipeline_mode not in ("agentic", "augmented"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid pipeline mode. Use 'agentic' or 'augmented'.")
    settings.PIPELINE_MODE = config.pipeline_mode
    return {"pipeline_mode": settings.PIPELINE_MODE}


@app.get("/", tags=["Root"], response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Root endpoint — points the user to the real React UI.

    The old `test_client_html` console is still served at `/console` for
    debugging individual endpoints, but it's intentionally out of the
    happy path now: it was written for an earlier API shape and crashes
    on responses that include the new fields (retrieval_passes,
    fatigue_per_event, etc.).
    """
    return HTMLResponse(content=f"""
<!doctype html>
<html><head><meta charset="utf-8"><title>TripGraph AI — backend</title>
<style>
  body {{ background:#181c24; color:#dde2eb; font-family:-apple-system,Inter,system-ui,sans-serif;
          margin:0; min-height:100vh; display:grid; place-items:center; }}
  .card {{ max-width:520px; padding:36px 32px; border:1px solid rgba(255,255,255,0.16);
           border-radius:16px; background:linear-gradient(180deg,rgba(63,70,81,0.45),rgba(35,40,48,0.65));
           backdrop-filter:blur(20px); box-shadow:0 24px 64px rgba(0,0,0,0.45); }}
  h1 {{ font-size:18px; font-weight:600; margin:0 0 6px; letter-spacing:-0.01em; }}
  p  {{ font-size:13px; color:#b5bcc8; margin:0 0 14px; line-height:1.55; }}
  a.btn {{ display:inline-block; padding:10px 18px; border-radius:999px; text-decoration:none;
           font-size:13px; font-weight:600; color:#181c24;
           background:linear-gradient(180deg,#dde2eb,#b5bcc8); border:1px solid rgba(255,255,255,0.4);
           box-shadow:inset 0 1px 0 rgba(255,255,255,0.5),0 6px 18px rgba(0,0,0,0.35); }}
  a.btn + a.btn {{ margin-left:8px; background:transparent; color:#dde2eb;
                   border:1px solid rgba(255,255,255,0.16); box-shadow:none; font-weight:500; }}
  code {{ color:#dde2eb; background:rgba(255,255,255,0.06); padding:2px 6px; border-radius:4px; font-size:12px; }}
</style></head><body>
  <div class="card">
    <h1>TripGraph backend is running on :8001</h1>
    <p>This is the API server. The user-facing app lives at the React dev server:</p>
    <p><a class="btn" href="http://127.0.0.1:5174">Open TripGraph app</a>
       <a class="btn" href="/docs">API docs</a>
       <a class="btn" href="/console">Legacy console</a></p>
    <p style="margin-top:18px;font-size:11.5px;color:#9aa3b2">
       The legacy console at <code>/console</code> was written for an earlier API shape and
       may crash on new response fields. Use the React app for real use.
    </p>
  </div>
</body></html>
""")


@app.get("/console", tags=["Root"], response_class=HTMLResponse)
async def legacy_console() -> HTMLResponse:
    """Legacy debug console — written for an earlier API shape; may crash on
    new response fields. Kept around for endpoint poking only."""
    return HTMLResponse(content=HTML_CONTENT)


@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Health check endpoint used by Docker Compose and monitoring."""
    return {"status": "healthy"}


@app.get("/api/maptiles-session", tags=["Config"])
async def maptiles_session() -> dict:
    """Create a Google Map Tiles session with a minimal Uber-style grey theme.

    Returns {session, key, tile_url_template} so the frontend can plug Google's
    styled 2D tiles into Leaflet. Returns {available: False} when no key / on error,
    so the frontend can fall back to CartoDB tiles.
    """
    import requests as _rq
    # Read the key from the client module (it runs its own load_dotenv at import,
    # which reliably populates it even when the inline os.getenv path doesn't).
    from backend.api_clients.google_places_client import GOOGLE_MAPS_API_KEY as key

    if not key:
        return {"available": False, "reason": "NO_KEY"}

    # Minimal silver / Uber-like style: hide POIs & transit, desaturate to greys.
    style = [
        {"elementType": "geometry", "stylers": [{"color": "#f5f5f5"}]},
        {"elementType": "labels.icon", "stylers": [{"visibility": "off"}]},
        {"elementType": "labels.text.fill", "stylers": [{"color": "#6b7382"}]},
        {"elementType": "labels.text.stroke", "stylers": [{"color": "#f5f5f7"}]},
        {"featureType": "administrative", "elementType": "geometry", "stylers": [{"visibility": "off"}]},
        {"featureType": "poi", "stylers": [{"visibility": "off"}]},
        {"featureType": "poi.park", "elementType": "geometry", "stylers": [{"color": "#e6e8ec"}]},
        {"featureType": "road", "elementType": "geometry", "stylers": [{"color": "#ffffff"}]},
        {"featureType": "road.arterial", "elementType": "geometry", "stylers": [{"color": "#ececef"}]},
        {"featureType": "road.highway", "elementType": "geometry", "stylers": [{"color": "#dcdee3"}]},
        {"featureType": "road.local", "elementType": "labels", "stylers": [{"visibility": "off"}]},
        {"featureType": "transit", "stylers": [{"visibility": "off"}]},
        {"featureType": "water", "elementType": "geometry", "stylers": [{"color": "#cdd0d6"}]},
    ]
    try:
        r = _rq.post(
            f"https://tile.googleapis.com/v1/createSession?key={key}",
            json={"mapType": "roadmap", "language": "en-US", "region": "IN", "styles": style},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        session = data.get("session")
        if not session:
            return {"available": False, "reason": "NO_SESSION"}
        return {
            "available": True,
            "session": session,
            "key": key,
            "expiry": data.get("expiry"),
            "tile_url_template": f"https://tile.googleapis.com/v1/2dtiles/{{z}}/{{x}}/{{y}}?session={session}&key={key}",
        }
    except Exception as e:
        print(f"  ⚠️  Google Map Tiles session failed: {e}")
        return {"available": False, "reason": f"ERROR:{e}"}


@app.get("/api/integrations", tags=["Config"])
async def integrations_status() -> dict:
    """Report which external API integrations are configured.

    The frontend uses this to show a banner when a key is missing so the user
    understands why a trip outside the seeded routes can't be planned.
    """
    import os as _os
    return {
        "ors":          {"configured": bool(_os.getenv("ORS_API_KEY")),          "purpose": "Geocode any city + draw real road polylines"},
        "geoapify":     {"configured": bool(_os.getenv("GEOAPIFY_API_KEY")),     "purpose": "Discover hotels & activities for cities not seeded in the KG"},
        "openweather":  {"configured": bool(_os.getenv("OPENWEATHERMAP_API_KEY")), "purpose": "3-day weather forecast for the trip + gear suggestions"},
        "flights":      {"configured": bool(_os.getenv("SKYSCANNER_RAPID_API_KEY") or _os.getenv("AMADEUS_API_KEY") or _os.getenv("DUFFEL_API_KEY")), "purpose": "Live flight prices & deal detection"},
        "hotel_deals":  {"configured": bool(_os.getenv("BOOKING_RAPID_API_KEY") or _os.getenv("AGODA_PARTNER_API_KEY") or _os.getenv("HOTELBEDS_API_KEY")), "purpose": "Live hotel pricing + 'good deal' detection"},
        "traffic":      {"configured": bool(_os.getenv("TOMTOM_API_KEY") or _os.getenv("HERE_API_KEY") or _os.getenv("GOOGLE_MAPS_API_KEY")), "purpose": "Current + historical traffic on driving legs"},
    }


@app.on_event("startup")
async def _print_integration_banner():
    """Loud, readable warning at startup when critical keys are missing."""
    import os as _os
    missing = []
    if not _os.getenv("ORS_API_KEY"):          missing.append("ORS_API_KEY (geocoding + driving routes)")
    if not _os.getenv("GEOAPIFY_API_KEY"):     missing.append("GEOAPIFY_API_KEY (hotels + activities discovery)")
    if not _os.getenv("OPENWEATHERMAP_API_KEY"): missing.append("OPENWEATHERMAP_API_KEY (weather forecast)")
    if missing:
        print("")
        print("=" * 72)
        print("  ⚠️  TripGraph: external API keys missing — planner is degraded")
        print("=" * 72)
        for m in missing:
            print(f"     • {m}")
        print("")
        print("  Without ORS, trips outside the 3 seeded routes (Gurugram→")
        print("  Jaipur/Rishikesh/Tirthan) cannot be planned. The planner will")
        print("  fall back to the nearest seeded route.")
        print("")
        print("  Add keys to .env (see .env.example) and restart.")
        print("=" * 72)
        print("")
