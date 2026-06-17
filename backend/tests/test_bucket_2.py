"""
Bucket 2 Validation Script.
Tests the agentic pipeline end-to-end.

Run: PYTHONPATH=. python backend/tests/test_bucket_2.py

Tests 1-3 run without any API key (import and schema checks only).
Tests 4-5 require GOOGLE_API_KEY in .env or environment.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MOCK_MODE = not bool(GOOGLE_API_KEY)

PASS = 0
FAIL = 0


def check(condition: bool, msg: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {msg}")
    else:
        FAIL += 1
        print(f"  ❌ {msg}")


print("=" * 60)
print("Bucket 2 — Agentic Pipeline Validation")
print("=" * 60)
if MOCK_MODE:
    print("  ⚠️  GOOGLE_API_KEY not set — LLM tests will be skipped")

# ---------------------------------------------------------------------------
# Test 1: State schema
# ---------------------------------------------------------------------------
print("\n📋 Test 1: TripState schema")
try:
    from backend.agents.state import TripState, initialize_state
    check(True, "TripState imported successfully")

    state = initialize_state(["test message"])
    required_keys = [
        "raw_chat", "extracted_constraints", "missing_fields", "assumptions",
        "conflict_report", "is_ready_to_plan",
        "route_candidates", "hotel_candidates", "transport_candidates",
        "activity_candidates", "food_candidates", "waypoint_candidates",
        "itinerary_candidates", "selected_itinerary", "alternative_itineraries",
        "validation_report", "score_breakdown", "timeline", "map_points",
        "cost_breakdown", "explanation", "delay_event", "replanned_itinerary",
        "replanning_explanation",
    ]
    check(
        all(k in state for k in required_keys),
        f"initialize_state() has all {len(required_keys)} required fields",
    )
    check(state["raw_chat"] == ["test message"], "raw_chat correctly initialized")
    check(state["is_ready_to_plan"] is False, "is_ready_to_plan defaults to False")
    check(state["selected_itinerary"] is None, "selected_itinerary defaults to None")
except Exception as e:
    check(False, f"TripState import/init failed: {e}")

# ---------------------------------------------------------------------------
# Test 2: Prompts
# ---------------------------------------------------------------------------
print("\n📝 Test 2: Prompts")
try:
    from backend.agents.prompts import (
        CHAT_PARSER_HUMAN,
        CHAT_PARSER_SYSTEM,
        CONSTRAINT_VALIDATOR_HUMAN,
        CONSTRAINT_VALIDATOR_SYSTEM,
        EXPLAINER_HUMAN,
        EXPLAINER_SYSTEM,
        REPLANNER_EXPLAIN_HUMAN,
        REPLANNER_EXPLAIN_SYSTEM,
    )
    for name, prompt in [
        ("CHAT_PARSER_SYSTEM", CHAT_PARSER_SYSTEM),
        ("CHAT_PARSER_HUMAN", CHAT_PARSER_HUMAN),
        ("CONSTRAINT_VALIDATOR_SYSTEM", CONSTRAINT_VALIDATOR_SYSTEM),
        ("CONSTRAINT_VALIDATOR_HUMAN", CONSTRAINT_VALIDATOR_HUMAN),
        ("EXPLAINER_SYSTEM", EXPLAINER_SYSTEM),
        ("EXPLAINER_HUMAN", EXPLAINER_HUMAN),
        ("REPLANNER_EXPLAIN_SYSTEM", REPLANNER_EXPLAIN_SYSTEM),
        ("REPLANNER_EXPLAIN_HUMAN", REPLANNER_EXPLAIN_HUMAN),
    ]:
        check(isinstance(prompt, str) and len(prompt) > 50, f"{name} loaded ({len(prompt)} chars)")
    check("{chat_messages}" in CHAT_PARSER_HUMAN, "CHAT_PARSER_HUMAN has {chat_messages} placeholder")
    check("{constraints}" in CONSTRAINT_VALIDATOR_HUMAN, "CONSTRAINT_VALIDATOR_HUMAN has {constraints} placeholder")
except Exception as e:
    check(False, f"Prompts import failed: {e}")

# ---------------------------------------------------------------------------
# Test 3: Workflow imports
# ---------------------------------------------------------------------------
print("\n🔄 Test 3: Workflow structure")
try:
    from backend.agents.workflow import run_replan_workflow, run_workflow
    check(True, "run_workflow imported successfully")
    check(True, "run_replan_workflow imported successfully")
    check(callable(run_workflow), "run_workflow is callable")
    check(callable(run_replan_workflow), "run_replan_workflow is callable")
except Exception as e:
    check(False, f"Workflow import failed: {e}")

# ---------------------------------------------------------------------------
# Test 4: LLM client (requires API key)
# ---------------------------------------------------------------------------
print("\n🤖 Test 4: LLM client")
if MOCK_MODE:
    print("  ⏭️  Skipped (no GOOGLE_API_KEY)")
else:
    try:
        from backend.agents.llm_client import get_llm
        llm = get_llm()
        check(True, f"LLM initialized: {type(llm).__name__}")
        # Minimal smoke test
        response = llm.invoke([("human", "Say OK")])
        check("ok" in response.content.lower() or len(response.content) > 0, "LLM responds to a simple prompt")
    except Exception as e:
        check(False, f"LLM init/call failed: {e}")

# ---------------------------------------------------------------------------
# Test 5: End-to-end workflow (requires API key)
# ---------------------------------------------------------------------------
print("\n🚀 Test 5: End-to-end workflow")
if MOCK_MODE:
    print("  ⏭️  Skipped (no GOOGLE_API_KEY)")
else:
    try:
        from backend.agents.workflow import run_workflow
        result = run_workflow([
            "Let's do a weekend trip from Gurugram",
            "Budget under 15k per person",
            "Mountains please, not Jaipur",
            "No night driving",
            "Need rafting and good cafes",
            "We need to return before Monday morning",
        ])

        check(bool(result.get("extracted_constraints")), "extracted_constraints is populated")
        check(
            result.get("extracted_constraints", {}).get("origin") == "Gurugram",
            f"origin correctly extracted as 'Gurugram' (got '{result.get('extracted_constraints', {}).get('origin')}')",
        )
        check(result.get("is_ready_to_plan") is True, "is_ready_to_plan=True")
        check(bool(result.get("route_candidates")), f"route_candidates populated ({len(result.get('route_candidates', []))} routes)")
        check(result.get("selected_itinerary") is not None, "selected_itinerary is not None")
        check(bool(result.get("timeline")), f"timeline populated ({len(result.get('timeline', []))} events)")
        check(bool(result.get("map_points")), f"map_points populated ({len(result.get('map_points', []))} points)")
        check(bool(result.get("explanation")), f"explanation generated ({len(result.get('explanation', ''))} chars)")
        check(bool(result.get("cost_breakdown")), "cost_breakdown populated")

        # Spot-check explanation
        expl = result.get("explanation", "")
        check(len(expl) > 30, f"explanation is non-trivial: '{expl[:80]}...'")

        # Spot-check map point types
        point_types = {p.get("type") for p in result.get("map_points", [])}
        check("origin" in point_types, "map_points contains origin point")
        check("destination" in point_types, "map_points contains destination point")

        # Replan test
        print("\n  Testing replan workflow...")
        replan_result = run_replan_workflow(
            result,
            {"delay_type": "departure_delay", "delay_minutes": 90},
        )
        check(replan_result.get("replanned_itinerary") is not None, "replanned_itinerary populated")
        check(bool(replan_result.get("replanning_explanation")), "replanning_explanation generated")

    except Exception as e:
        check(False, f"End-to-end workflow failed: {e}")
        import traceback
        traceback.print_exc()

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("🎉 ALL CHECKS PASSED — Bucket 2 pipeline is valid!")
else:
    print("⚠️  Some checks failed. Review the output above.")
    sys.exit(1)
