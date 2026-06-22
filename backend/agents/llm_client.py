"""
Swappable, per-role LLM client factory.

Two big ideas live here:

1. PER-ROLE ROUTING — every agent calls `get_llm("<role>")`. You can pin any
   single agent to a different provider/model via env overrides, with ZERO code
   changes. The architect can stay on a strong Claude model while cheap
   extraction agents run on Haiku, for example.

       Global default (used when no role override is set):
           LLM_PROVIDER=anthropic
           LLM_MODEL=claude-haiku-4-5-20251001

       Per-role override (UPPERCASE the role):
           LLM_PROVIDER_ARCHITECT=anthropic
           LLM_MODEL_ARCHITECT=claude-sonnet-4-6
           LLM_PROVIDER_ENRICHER=gemini
           LLM_MODEL_ENRICHER=gemini-2.0-flash

2. GOOGLE-GROUNDED GEMINI — `get_grounded_llm()` returns a Gemini client with
   native Google Search grounding enabled. This is the "agents that fetch live
   data from Google" capability: the model issues real Google Search queries
   mid-generation and grounds its answer in the results (current prices, "is it
   still open", seasonal closures) instead of its training-cutoff memory. Claude
   has no equivalent built-in, which is exactly why a two-provider setup is worth
   having: route reasoning to Claude, route fresh-fact lookups to Gemini.

Supported providers: gemini, openai, ollama, anthropic
"""
import os

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()


def _resolve(role: str | None, key: str, default: str) -> str:
    """Resolve a config value with an optional per-role override.

    For role="architect" and key="LLM_PROVIDER", looks up
    LLM_PROVIDER_ARCHITECT first, then LLM_PROVIDER, then `default`.
    """
    if role:
        role_val = os.getenv(f"{key}_{role.upper()}")
        if role_val:
            return role_val
    return os.getenv(key, default)


def get_llm(role: str | None = None) -> BaseChatModel:
    """Create an LLM instance, optionally routed per agent role.

    Pass the calling agent's role (e.g. "architect", "enricher", "parser") to
    allow env-level per-role overrides. Omit it to use the global default.
    """
    provider = _resolve(role, "LLM_PROVIDER", "gemini")
    model = _resolve(role, "LLM_MODEL", "gemini-2.0-flash")
    temperature = float(_resolve(role, "LLM_TEMPERATURE", "0"))

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        # max_retries gives automatic exponential backoff on 429 (free-tier
        # rate limits) — important since the pipeline makes ~7 LLM calls per trip.
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            max_retries=4,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_retries=3,
            timeout=60,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. Supported: gemini, openai, ollama, anthropic"
        )


def get_grounded_llm(model: str | None = None):
    """Return a Gemini client with native Google Search grounding enabled.

    The returned model answers using live Google Search results. Use it for
    agents whose value is freshness (enricher, deals, fact-checking) rather than
    structured reasoning. Returns None if Gemini / the Google key is unavailable,
    so callers can gracefully fall back to a normal `get_llm()`.

    Grounding tool name differs by model generation:
      - Gemini 2.x  → {"google_search": {}}
      - Gemini 1.5  → {"google_search_retrieval": {}}
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    model = model or os.getenv("GROUNDED_LLM_MODEL", "gemini-2.0-flash")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        client = ChatGoogleGenerativeAI(
            model=model,
            temperature=0,
            google_api_key=api_key,
            max_retries=4,
        )
        tool = {"google_search": {}} if "1.5" not in model else {"google_search_retrieval": {}}
        return client.bind_tools([tool])
    except Exception as e:
        print(f"  ⚠️  Grounded Gemini unavailable ({e}) — caller should fall back")
        return None


def extract_text_content(content: any) -> str:
    """Helper to convert LangChain message content (which could be a string, a list of dicts/strings, or other types) into a plain string."""
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)
    elif not isinstance(content, str):
        return str(content) if content is not None else ""
    return content
