"""
Tests for _parse_final_answer() — no external dependencies.
"""
import json
import pytest
from backend.agents_augmented.state import init_state
from backend.agents_augmented.workflow import _parse_final_answer

SAMPLE_CHAT = ["Let's go to Rishikesh from Gurugram"]


def _base_state() -> dict:
    return dict(init_state(SAMPLE_CHAT))


def test_clean_json_merges_keys():
    state = _base_state()
    payload = json.dumps({
        "selected_itinerary": {"destination": "Rishikesh"},
        "explanation": "Great trip!",
        "is_ready_to_plan": True,
    })
    result = _parse_final_answer(payload, state)
    assert result["selected_itinerary"] == {"destination": "Rishikesh"}
    assert result["explanation"] == "Great trip!"
    assert result["is_ready_to_plan"] is True


def test_json_fence_stripped_and_parsed():
    state = _base_state()
    payload = '```json\n{"explanation": "Fenced JSON"}\n```'
    result = _parse_final_answer(payload, state)
    assert result["explanation"] == "Fenced JSON"


def test_bare_fence_stripped_and_parsed():
    state = _base_state()
    payload = '```\n{"explanation": "Bare fence"}\n```'
    result = _parse_final_answer(payload, state)
    assert result["explanation"] == "Bare fence"


def test_invalid_json_sets_explanation_no_raise():
    state = _base_state()
    payload = "This is not JSON at all."
    result = _parse_final_answer(payload, state)
    assert result["explanation"] == payload
    # Should not raise


def test_partial_json_merges_known_keys_only():
    state = _base_state()
    payload = json.dumps({
        "explanation": "Partial",
        "unknown_key_xyz": "should be ignored",
    })
    result = _parse_final_answer(payload, state)
    assert result["explanation"] == "Partial"
    assert "unknown_key_xyz" not in result


def test_init_defaults_preserved_for_missing_keys():
    state = _base_state()
    payload = json.dumps({"explanation": "Minimal"})
    result = _parse_final_answer(payload, state)
    # Keys not in payload retain init_state defaults
    assert result["raw_chat"] == SAMPLE_CHAT
    assert result["route_candidates"] == []
    assert result["selected_itinerary"] is None
    assert result["is_ready_to_plan"] is False


def test_empty_json_object_no_crash():
    state = _base_state()
    result = _parse_final_answer("{}", state)
    assert result["raw_chat"] == SAMPLE_CHAT  # default preserved
