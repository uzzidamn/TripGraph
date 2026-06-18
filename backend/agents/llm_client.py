"""
Swappable LLM client factory.

Change LLM_PROVIDER and LLM_MODEL in .env to switch models with no code changes.
Supported providers: gemini, openai, ollama, anthropic

.env example:
    LLM_PROVIDER=anthropic
    LLM_MODEL=claude-haiku-4-5-20251001
    ANTHROPIC_API_KEY=your_key_here
    LLM_TEMPERATURE=0
"""
import os

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()


def get_llm() -> BaseChatModel:
    """Create and return an LLM instance based on environment configuration."""
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0"))

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
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

