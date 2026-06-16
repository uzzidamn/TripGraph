"""
Tests for MAX_TOOL_CALLS and MAX_ITERATIONS enforcement.
No LLM API key or Neo4j required — LLMClient is mocked.
"""
from unittest.mock import MagicMock, patch
import backend.agents_augmented.workflow as wf


_TOOL_CALL_RESPONSE = {
    "type": "tool_call",
    "tool_call_id": "test-id",
    "tool_name": "get_routes",
    "arguments": {"origin": "Gurugram"},
}

_SAMPLE_CHAT = ["Plan a trip from Gurugram"]


def _make_mock_client(invoke_return):
    client = MagicMock()
    client.invoke.return_value = invoke_return
    return client


# ---------------------------------------------------------------------------
# MAX_TOOL_CALLS
# ---------------------------------------------------------------------------

def test_max_tool_calls_terminates():
    original = wf.MAX_TOOL_CALLS
    wf.MAX_TOOL_CALLS = 3

    mock_client = _make_mock_client(_TOOL_CALL_RESPONSE)

    with patch("backend.agents_augmented.workflow.create_llm_client", return_value=mock_client), \
         patch("backend.agents_augmented.workflow.execute_tool", return_value={"result": []}):
        state = wf.run_workflow(_SAMPLE_CHAT)

    wf.MAX_TOOL_CALLS = original

    assert state["conflict_report"] is not None
    assert state["conflict_report"]["error"] == "execution_limit_exceeded"
    assert mock_client.invoke.call_count == 3


def test_max_tool_calls_is_3_not_4():
    """Verify loop stops exactly at the limit, not one over."""
    original = wf.MAX_TOOL_CALLS
    wf.MAX_TOOL_CALLS = 3

    call_count = 0

    def counting_invoke():
        nonlocal call_count
        call_count += 1
        return _TOOL_CALL_RESPONSE

    mock_client = MagicMock()
    mock_client.invoke.side_effect = counting_invoke

    with patch("backend.agents_augmented.workflow.create_llm_client", return_value=mock_client), \
         patch("backend.agents_augmented.workflow.execute_tool", return_value={"result": []}):
        wf.run_workflow(_SAMPLE_CHAT)

    wf.MAX_TOOL_CALLS = original

    assert call_count == 3


# ---------------------------------------------------------------------------
# MAX_ITERATIONS
# ---------------------------------------------------------------------------

def test_max_iterations_terminates():
    original_tc = wf.MAX_TOOL_CALLS
    original_it = wf.MAX_ITERATIONS
    wf.MAX_TOOL_CALLS = 999  # disable tool cap
    wf.MAX_ITERATIONS = 4

    mock_client = _make_mock_client(_TOOL_CALL_RESPONSE)

    with patch("backend.agents_augmented.workflow.create_llm_client", return_value=mock_client), \
         patch("backend.agents_augmented.workflow.execute_tool", return_value={"result": []}):
        state = wf.run_workflow(_SAMPLE_CHAT)

    wf.MAX_TOOL_CALLS = original_tc
    wf.MAX_ITERATIONS = original_it

    assert state["conflict_report"]["error"] == "execution_limit_exceeded"
    assert mock_client.invoke.call_count == 4


# ---------------------------------------------------------------------------
# Replanning safety limits
# ---------------------------------------------------------------------------

def test_replan_max_tool_calls_terminates():
    original = wf.MAX_TOOL_CALLS
    wf.MAX_TOOL_CALLS = 2

    mock_client = _make_mock_client(_TOOL_CALL_RESPONSE)

    base_state = dict(wf.init_state(_SAMPLE_CHAT))
    base_state["selected_itinerary"] = {"destination": "Rishikesh"}
    base_state["extracted_constraints"] = {"origin": "Gurugram"}

    with patch("backend.agents_augmented.workflow.create_llm_client", return_value=mock_client), \
         patch("backend.agents_augmented.workflow.execute_tool", return_value={"result": {}}):
        result = wf.run_replan_workflow(base_state, {"delay_type": "delay", "delay_minutes": 30})

    wf.MAX_TOOL_CALLS = original

    assert result["conflict_report"]["error"] == "execution_limit_exceeded"
