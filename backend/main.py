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

from backend.api.chat_routes import router as chat_router
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


@app.get("/", tags=["Health"])
async def root() -> dict:
    """Root endpoint — confirms the API is running."""
    return {"message": "TripGraph AI API is running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Health check endpoint used by Docker Compose and monitoring."""
    return {"status": "healthy"}
