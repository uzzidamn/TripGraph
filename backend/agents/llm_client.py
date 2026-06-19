"""
Swappable LLM client. Change LLM_PROVIDER and LLM_MODEL in .env to switch models.
Supported providers: gemini, claude, openai, ollama
Tracing: set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY in .env to enable LangSmith.

Gemini SDK note:
  Uses google-genai (new SDK) via langchain-google-genai>=2.0.
  Do NOT install or import google-generativeai (deprecated).
"""
import os
import time
from collections import deque
from threading import Lock

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()

# LangSmith tracing is activated automatically when these env vars are set:
#   LANGCHAIN_TRACING_V2=true
#   LANGCHAIN_API_KEY=...
#   LANGCHAIN_PROJECT=tripgraph-bucket2
# No code changes required in nodes.

# ---------------------------------------------------------------------------
# Rate limiter — module-level sliding-window, shared across all LLM calls
# ---------------------------------------------------------------------------

_rate_limit_rpm: int = int(os.getenv("LLM_RATE_LIMIT_RPM", "15"))
_call_timestamps: deque = deque()
_rate_lock: Lock = Lock()


def _wait_for_rate_limit() -> None:
    """Block until making an LLM call would not exceed LLM_RATE_LIMIT_RPM.
    Uses a sliding 60-second window. Thread-safe.
    """
    with _rate_lock:
        now = time.monotonic()
        while _call_timestamps and now - _call_timestamps[0] >= 60.0:
            _call_timestamps.popleft()

        if len(_call_timestamps) >= _rate_limit_rpm:
            sleep_for = 60.0 - (now - _call_timestamps[0])
            if sleep_for > 0:
                print(f"[RATE LIMIT] Sleeping {sleep_for:.1f}s to stay under {_rate_limit_rpm} RPM")
                time.sleep(sleep_for)
            now = time.monotonic()
            while _call_timestamps and now - _call_timestamps[0] >= 60.0:
                _call_timestamps.popleft()

        _call_timestamps.append(time.monotonic())


# ---------------------------------------------------------------------------
# Public LLM factories — call immediately before .invoke(), not at module load
# ---------------------------------------------------------------------------

def get_llm(run_name: str | None = None) -> BaseChatModel:
    """Return an LLM instance for the configured provider.

    Enforces LLM_RATE_LIMIT_RPM before construction — call this immediately
    before every .invoke() call, not at module import time.
    """
    _wait_for_rate_limit()
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite-preview-06-17")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0"))

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            name=run_name,
        )
    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or "claude-sonnet-4-5",
            temperature=temperature,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            name=run_name,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature, name=run_name)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature, name=run_name)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: gemini, claude, openai, ollama")


def get_llm_json(run_name: str | None = None) -> BaseChatModel:
    """Variant of get_llm() that enforces JSON output at the model level.

    Use in chat_parser_node, explainer_node, replanner_agent_node.
    Rate limit is enforced here — do NOT skip calling this before .invoke().
    """
    _wait_for_rate_limit()
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite-preview-06-17")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0"))

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        # v4: response_mime_type is a direct field (not generation_config)
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            response_mime_type="application/json",
            name=run_name,
        )
    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or "claude-sonnet-4-5",
            temperature=temperature,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            name=run_name,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature, name=run_name)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature, name=run_name)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: gemini, claude, openai, ollama")


def get_provider() -> str:
    """Return the active provider name."""
    return os.getenv("LLM_PROVIDER", "gemini")


def get_trace_url() -> str | None:
    """Return the LangSmith trace URL for the most recent run, or None."""
    if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() != "true":
        return None
    try:
        from langsmith import Client
        client = Client()
        runs = list(client.list_runs(
            project_name=os.getenv("LANGCHAIN_PROJECT", "default"), limit=1
        ))
        if runs:
            return client.get_run_url(run=runs[0])
    except Exception:
        pass
    return None
