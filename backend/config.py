"""
Central configuration loaded from environment variables.
All env var names match .env.example exactly.
Import `settings` from here everywhere — never read os.getenv() directly in route files.
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables at import time."""

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "tripgraph123")

    # LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    PIPELINE_MODE: str = os.getenv("PIPELINE_MODE", "agentic")
    LLM_RATE_LIMIT_RPM: int = int(os.getenv("LLM_RATE_LIMIT_RPM", "5"))

    # API server
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # CORS — comma-separated list in env, split into list here
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")


settings = Settings()
