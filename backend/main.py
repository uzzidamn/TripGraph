"""
TripGraph AI — FastAPI Backend Entry Point

Start server:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

API docs (auto-generated):
    http://localhost:8000/docs

Health check:
    http://localhost:8000/health
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.api.chat_routes import router as chat_router
from backend.api.eval import router as eval_router
from backend.api.itinerary_routes import router as itinerary_router
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

# CORS — allow the React dev server and any other configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route modules
app.include_router(chat_router)
app.include_router(itinerary_router)
app.include_router(replanner_router)
app.include_router(eval_router)

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
    """Root endpoint — serves the interactive Test Console UI."""
    return HTMLResponse(content=HTML_CONTENT)


@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Health check endpoint used by Docker Compose and monitoring."""
    return {"status": "healthy"}


# Serve built React frontend — must be mounted after all API routes
_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_FRONTEND_DIST, "assets")), name="assets")

    @app.get("/app", include_in_schema=False)
    @app.get("/app/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str = "") -> FileResponse:
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))
