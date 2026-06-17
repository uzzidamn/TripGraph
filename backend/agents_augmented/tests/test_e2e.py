"""
End-to-end tests — require a live LLM API and RUN_E2E=true.

These tests make real API calls and consume quota.
They are skipped by default and must be opted into explicitly:

    RUN_E2E=true PYTHONPATH=. pytest backend/agents_augmented/tests/test_e2e.py -v
"""
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

_run_e2e = os.getenv("RUN_E2E", "").lower() in ("1", "true", "yes")

pytestmark = pytest.mark.skipif(
    not _run_e2e,
    reason="Set RUN_E2E=true to run end-to-end tests (they consume real API quota)",
)

from backend.agents_augmented.workflow import run_workflow, run_replan_workflow
from backend.agents_augmented.state import TripState

SAMPLE_CHAT = [
    "Guys let's plan a trip from Gurugram",
    "Maybe Rishikesh? I want to do rafting",
    "Budget around 5000 per person",
    "Weekend trip, 4 of us",
]

SAMPLE_DELAY = {
    "delay_type": "departure_delay",
    "delay_minutes": 90,
}


def test_run_workflow_returns_tripstate():
    state = run_workflow(SAMPLE_CHAT)

    # All 24 keys present
    expected_keys = set(TripState.__annotations__.keys())
    assert expected_keys.issubset(set(state.keys())), (
        f"Missing keys: {expected_keys - set(state.keys())}"
    )


def test_run_workflow_has_selected_itinerary():
    state = run_workflow(SAMPLE_CHAT)
    assert state["selected_itinerary"] is not None, (
        "LLM did not produce a selected_itinerary. "
        f"conflict_report={state.get('conflict_report')}"
    )


def test_run_workflow_has_timeline():
    state = run_workflow(SAMPLE_CHAT)
    assert isinstance(state["timeline"], list)
    assert len(state["timeline"]) > 0


def test_run_workflow_has_validation_report():
    state = run_workflow(SAMPLE_CHAT)
    assert state["validation_report"] is not None


def test_run_workflow_no_langchain():
    """Sanity: workflow module must not import langchain or langgraph."""
    import importlib, sys
    for mod_name in list(sys.modules.keys()):
        assert "langchain" not in mod_name, f"langchain found in sys.modules: {mod_name}"
        assert "langgraph" not in mod_name, f"langgraph found in sys.modules: {mod_name}"


def test_run_replan_workflow_returns_replanned():
    state = run_workflow(SAMPLE_CHAT)

    if not state.get("selected_itinerary"):
        pytest.skip("run_workflow did not produce a selected_itinerary; skipping replan test")

    updated = run_replan_workflow(state, SAMPLE_DELAY)

    assert updated["replanned_itinerary"] is not None, (
        "run_replan_workflow did not produce a replanned_itinerary"
    )
    assert updated["replanning_explanation"] is not None
