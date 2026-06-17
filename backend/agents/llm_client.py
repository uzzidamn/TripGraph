"""
Swappable LLM client factory.

Change LLM_PROVIDER and LLM_MODEL in .env to switch models with no code changes.
Supported providers: gemini, openai, ollama

.env example:
    LLM_PROVIDER=gemini
    LLM_MODEL=gemini-2.0-flash
    GOOGLE_API_KEY=your_key_here
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
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. Supported: gemini, openai, ollama"
        )
