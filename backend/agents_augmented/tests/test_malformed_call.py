"""
Tests for MALFORMED_FUNCTION_CALL recovery in GeminiClient.invoke().

No real API key needed — google.genai is fully mocked via sys.modules injection
before GeminiClient is imported, so the test never touches the real SDK.
"""
import sys
import types
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Response stubs
# ---------------------------------------------------------------------------

def _make_text_response(text="done"):
    """Simulate a normal final-answer response."""
    part = MagicMock()
    part.function_call = None
    content = MagicMock()
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "STOP"
    response = MagicMock()
    response.candidates = [candidate]
    response.text = text
    return response


def _make_tool_call_response(tool_name="get_routes", args=None):
    """Simulate a response where the model called a tool."""
    fc = MagicMock()
    fc.name = tool_name
    fc.args = args or {"origin": "Gurugram"}
    part = MagicMock()
    part.function_call = fc
    content = MagicMock()
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "STOP"
    response = MagicMock()
    response.candidates = [candidate]
    return response


def _make_malformed_finish_response():
    """Simulate a successful call whose finish_reason is MALFORMED_FUNCTION_CALL."""
    candidate = MagicMock()
    candidate.content.parts = []
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "MALFORMED_FUNCTION_CALL"
    response = MagicMock()
    response.candidates = [candidate]
    return response


# ---------------------------------------------------------------------------
# Client factory — bypasses __init__ and injects a models stub
# ---------------------------------------------------------------------------

def _build_client(models_stub):
    """
    Construct a GeminiClient using __new__ (skips __init__) and wire up
    exactly the instance attributes that invoke() needs.
    """
    # Inject minimal google.genai stub so the import inside llm_client works
    google_pkg = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    google_pkg.genai = genai_mod
    sys.modules["google"] = google_pkg
    sys.modules["google.genai"] = genai_mod

    from backend.agents_augmented.llm_client import GeminiClient

    client = GeminiClient.__new__(GeminiClient)

    # Wire up the API client with the controllable models stub
    mock_api_client = MagicMock()
    mock_api_client.models = models_stub
    client._client = mock_api_client

    client._model = "gemini-2.5-flash-lite"
    client._config = MagicMock()
    client._contents = []
    client._genai_types = MagicMock()   # Content/Part calls return MagicMocks — fine for retry tests

    # Base-class rate-limit attributes: set limit high to disable sleeping in tests
    client._call_timestamps = []
    client._rate_limit = 999

    return client


# ---------------------------------------------------------------------------
# Exception-path tests  (generate_content raises ValueError)
# ---------------------------------------------------------------------------

class TestMalformedCallExceptionPath:

    def test_retry_succeeds_with_text_response(self):
        """First call raises MALFORMED; retry #1 returns text — result is final_answer."""
        models = MagicMock()
        models.generate_content.side_effect = [
            ValueError("finish_reason: MALFORMED_FUNCTION_CALL"),
            _make_text_response("Here is your trip"),
        ]
        client = _build_client(models)
        result = client.invoke()

        assert models.generate_content.call_count == 2
        assert result["type"] == "final_answer"
        assert result["content"] == "Here is your trip"

    def test_retry_succeeds_with_tool_call(self):
        """First call raises MALFORMED; retry #1 returns a tool call."""
        models = MagicMock()
        models.generate_content.side_effect = [
            ValueError("finish_reason: MALFORMED_FUNCTION_CALL"),
            _make_tool_call_response("get_routes", {"origin": "Gurugram"}),
        ]
        client = _build_client(models)
        result = client.invoke()

        assert result["type"] == "tool_call"
        assert result["tool_name"] == "get_routes"
        assert result["arguments"]["origin"] == "Gurugram"

    def test_two_retries_then_raise(self):
        """All 3 attempts raise MALFORMED — must re-raise after 2 retries (Decision 20)."""
        models = MagicMock()
        models.generate_content.side_effect = [
            ValueError("finish_reason: MALFORMED_FUNCTION_CALL"),  # initial
            ValueError("finish_reason: MALFORMED_FUNCTION_CALL"),  # retry 1
            ValueError("finish_reason: MALFORMED_FUNCTION_CALL"),  # retry 2 → raise
        ]
        client = _build_client(models)
        with pytest.raises(ValueError, match="MALFORMED_FUNCTION_CALL"):
            client.invoke()
        assert models.generate_content.call_count == 3

    def test_non_malformed_exception_is_reraised_immediately(self):
        """Real API errors (auth, network) must propagate without any retry."""
        models = MagicMock()
        models.generate_content.side_effect = ConnectionError("network error")
        client = _build_client(models)
        with pytest.raises(ConnectionError):
            client.invoke()
        assert models.generate_content.call_count == 1


# ---------------------------------------------------------------------------
# Finish-reason-path tests  (generate_content returns response with MALFORMED finish_reason)
# ---------------------------------------------------------------------------

class TestMalformedCallFinishReasonPath:

    def test_retry_sent_when_finish_reason_malformed(self):
        """Response with MALFORMED finish_reason triggers a retry; recovery succeeds."""
        models = MagicMock()
        models.generate_content.side_effect = [
            _make_malformed_finish_response(),
            _make_text_response("Recovered fine"),
        ]
        client = _build_client(models)
        result = client.invoke()

        assert models.generate_content.call_count == 2
        assert result["type"] == "final_answer"
        assert result["content"] == "Recovered fine"

    def test_two_malformed_finish_reasons_raise(self):
        """2 consecutive MALFORMED finish_reasons exhaust retries and must raise."""
        models = MagicMock()
        models.generate_content.side_effect = [
            _make_malformed_finish_response(),  # retry 1
            _make_malformed_finish_response(),  # retry 2
            _make_malformed_finish_response(),  # hits limit → raise
        ]
        client = _build_client(models)
        with pytest.raises(RuntimeError, match="MALFORMED_FUNCTION_CALL"):
            client.invoke()
