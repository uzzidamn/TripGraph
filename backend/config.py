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

    # LangSmith observability (optional — tracing is skipped when key is absent)
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "bucket2-golden-dataset")


settings = Settings()


def configure_langsmith() -> None:
    """Enable LangSmith tracing if LANGCHAIN_API_KEY is set. No-op otherwise."""
    if not settings.LANGCHAIN_API_KEY:
        return
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGCHAIN_PROJECT)
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGCHAIN_API_KEY)


from langchain_core.callbacks import BaseCallbackHandler as _BaseCallbackHandler


class RunIdCapture(_BaseCallbackHandler):
    """Callback that captures the root LangGraph run ID from the first on_chain_start event."""

    def __init__(self):
        super().__init__()
        self.run_id: str | None = None

    def on_chain_start(self, serialized, inputs, *, run_id, **kwargs):
        if self.run_id is None:
            self.run_id = str(run_id)


def get_runnable_config(
    run_name: str = "tripgraph",
    metadata: dict | None = None,
    callbacks: list | None = None,
):
    """Return a LangGraph RunnableConfig with optional LangSmith metadata and callbacks."""
    from langchain_core.runnables.config import RunnableConfig
    return RunnableConfig(run_name=run_name, metadata=metadata or {}, callbacks=callbacks or [])
