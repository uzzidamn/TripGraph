"""
Provider-agnostic LLM client.
Supports Gemini (default) and Claude via LLM_PROVIDER env var.
Each workflow run creates a new client instance; history is owned internally.
"""
import json
import os
import time
from uuid import uuid4

from backend.agents_augmented.tool_registry import get_gemini_tool_schemas, get_claude_tool_schemas


# ---------------------------------------------------------------------------
# Base class — owns sliding-window rate limiting
# ---------------------------------------------------------------------------

class LLMClient:
    """
    Base class for all LLM provider clients.

    Rate limiting: enforces LLM_RATE_LIMIT_RPM (default 5) calls per 60 seconds
    using a sliding-window timestamp tracker. Subclasses call _rate_limit_wait()
    at the start of their invoke() implementation.
    """

    _call_timestamps: list[float] = []

    def __init__(self) -> None:
        from backend.config import settings
        self._rate_limit: int = settings.LLM_RATE_LIMIT_RPM

    def _rate_limit_wait(self) -> None:
        """Sleep if necessary to stay within LLM_RATE_LIMIT_RPM calls/minute."""
        now = time.time()
        window = 60.0
        # Drop timestamps older than 60 seconds
        LLMClient._call_timestamps = [t for t in LLMClient._call_timestamps if now - t < window]
        if len(LLMClient._call_timestamps) >= self._rate_limit:
            sleep_secs = window - (now - LLMClient._call_timestamps[0])
            if sleep_secs > 0:
                print(f"[RATE LIMIT] Sleeping {sleep_secs:.1f}s (>{self._rate_limit} calls/min)")
                time.sleep(sleep_secs)
        LLMClient._call_timestamps.append(time.time())

    def add_user_message(self, content: str) -> None:
        raise NotImplementedError

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: dict) -> None:
        raise NotImplementedError

    def invoke(self) -> dict:
        """
        Returns one of:
          {"type": "tool_call", "tool_call_id": str, "tool_name": str, "arguments": dict}
          {"type": "final_answer", "content": str}
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Gemini  (google-genai SDK — stateless API, full history per call)
# ---------------------------------------------------------------------------

_MALFORMED_MSG = (
    "Your previous function call had invalid arguments and could not be parsed. "
    "Please retry using only simple values: strings, numbers, and flat lists. "
    "Avoid nested objects."
)
_MAX_MALFORMED_RETRIES = 2


class GeminiClient(LLMClient):
    def __init__(self, system_prompt: str):
        super().__init__()
        from google import genai
        from google.genai import types

        self._genai_types = types
        self._client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self._model = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
        self._config = types.GenerateContentConfig(
            tools=get_gemini_tool_schemas(),
            system_instruction=system_prompt,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
        )
        self._contents: list = []

    def add_user_message(self, content: str) -> None:
        types = self._genai_types
        self._contents.append(
            types.Content(role="user", parts=[types.Part(text=content)])
        )

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: dict) -> None:
        types = self._genai_types
        self._contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=tool_name,
                            response={"result": json.dumps(result, default=str)},
                        )
                    )
                ],
            )
        )

    def invoke(self) -> dict:
        self._rate_limit_wait()
        types = self._genai_types
        _malformed_retries = 0

        while True:
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=self._contents,
                    config=self._config,
                )
            except Exception as e:
                if "MALFORMED_FUNCTION_CALL" in str(e):
                    if _malformed_retries >= _MAX_MALFORMED_RETRIES:
                        print(f"[LLM ERROR] Gemini MALFORMED_FUNCTION_CALL after {_MAX_MALFORMED_RETRIES} retries — raising")
                        raise
                    _malformed_retries += 1
                    print(f"[LLM] MALFORMED_FUNCTION_CALL exception (retry {_malformed_retries}/{_MAX_MALFORMED_RETRIES})")
                    self._contents.append(
                        types.Content(role="user", parts=[types.Part(text=_MALFORMED_MSG)])
                    )
                    continue
                print(f"[LLM ERROR] Gemini: {e}")
                raise

            # Check finish_reason for response-level MALFORMED
            try:
                finish = response.candidates[0].finish_reason
                if "MALFORMED" in getattr(finish, "name", str(finish)):
                    if _malformed_retries >= _MAX_MALFORMED_RETRIES:
                        raise RuntimeError(
                            f"MALFORMED_FUNCTION_CALL after {_MAX_MALFORMED_RETRIES} retries"
                        )
                    _malformed_retries += 1
                    print(f"[LLM] MALFORMED_FUNCTION_CALL finish_reason (retry {_malformed_retries}/{_MAX_MALFORMED_RETRIES})")
                    self._contents.append(
                        types.Content(role="user", parts=[types.Part(text=_MALFORMED_MSG)])
                    )
                    continue
            except (IndexError, AttributeError):
                pass

            # Append model turn to history
            try:
                self._contents.append(response.candidates[0].content)
            except (IndexError, AttributeError):
                pass

            break  # successful response

        # Extract tool call if present
        try:
            for part in response.candidates[0].content.parts:
                fc = getattr(part, "function_call", None)
                if fc and fc.name:
                    return {
                        "type": "tool_call",
                        "tool_call_id": str(uuid4()),
                        "tool_name": fc.name,
                        "arguments": dict(fc.args),
                    }
        except (IndexError, AttributeError):
            pass

        # Final text answer
        try:
            return {"type": "final_answer", "content": response.text}
        except Exception:
            return {"type": "final_answer", "content": str(response)}


# ---------------------------------------------------------------------------
# Claude
# ---------------------------------------------------------------------------

class ClaudeClient(LLMClient):
    def __init__(self, system_prompt: str):
        super().__init__()
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.system_prompt = system_prompt
        self.tools = get_claude_tool_schemas()
        self.model = os.getenv("CLAUDE_MODEL") or os.getenv("LLM_MODEL", "claude-sonnet-4-6")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        self.messages: list[dict] = []

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: dict) -> None:
        self.messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_call_id,
                "content": json.dumps(result, default=str),
            }],
        })

    def invoke(self) -> dict:
        self._rate_limit_wait()
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=self.tools,
                messages=self.messages,
            )
        except Exception as e:
            print(f"[LLM ERROR] Claude: {e}")
            raise

        # Append assistant turn to maintain history
        self.messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            for block in response.content:
                if getattr(block, "type", None) == "tool_use":
                    return {
                        "type": "tool_call",
                        "tool_call_id": block.id,
                        "tool_name": block.name,
                        "arguments": block.input,
                    }

        # Final text answer
        for block in response.content:
            if hasattr(block, "text"):
                return {"type": "final_answer", "content": block.text}

        return {"type": "final_answer", "content": str(response.content)}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_llm_client(system_prompt: str) -> LLMClient:
    """Read LLM_PROVIDER and return the appropriate client."""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        return GeminiClient(system_prompt)
    if provider == "claude":
        return ClaudeClient(system_prompt)
    raise ValueError(f"Unknown LLM_PROVIDER: '{provider}'. Supported: gemini, claude")
