"""
Bucket 2 Validation Script.
Tests the full agentic pipeline end-to-end.
Run: PYTHONPATH=. python backend/tests/test_bucket_2.py
Requires: GOOGLE_API_KEY in .env for LLM calls (Tests 2 and 5+ are skipped otherwise).
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()

MOCK_MODE = not bool(os.getenv("GOOGLE_API_KEY"))
if MOCK_MODE:
    print("⚠️  GOOGLE_API_KEY not set. LLM tests will be skipped.")

print("=" * 60)
print("Bucket 2 — Agentic Pipeline Validation")
print("=" * 60)

# ── Test 1: TripState schema ─────────────────────────────────────────────────
print("\n📋 Test 1: TripState schema")
try:
    from backend.agents.state import TripState, init_state
    state = init_state(["test"])
    expected_fields = {
        "raw_chat", "extracted_constraints", "missing_fields", "assumptions",
        "conflict_report", "is_ready_to_plan",
        "route_candidates", "hotel_candidates", "transport_candidates",
        "activity_candidates", "food_candidates", "waypoint_candidates",
        "itinerary_candidates", "selected_itinerary", "alternative_itineraries",
        "validation_report", "score_breakdown", "timeline", "map_points", "cost_breakdown",
        "explanation", "trace_id", "delay_event", "replanned_itinerary", "replanning_explanation",
    }
    missing = expected_fields - set(state.keys())
    assert not missing, f"Missing TripState fields: {missing}"
    print(f"  ✅ TripState imported — {len(state)} fields present")
except Exception as e:
    print(f"  ❌ TripState failed: {e}")
    sys.exit(1)

# ── Test 2: LLM client ───────────────────────────────────────────────────────
print("\n🤖 Test 2: LLM client")
try:
    from backend.agents.llm_client import get_llm, get_llm_json, get_provider, get_trace_url
    provider = get_provider()
    print(f"  ✅ LLM client imported — provider: {provider}")
    if not MOCK_MODE:
        llm = get_llm()
        print(f"  ✅ get_llm() returned: {type(llm).__name__}")
    else:
        print("  ⏭️  get_llm() skipped (no API key)")
except Exception as e:
    print(f"  ❌ LLM client failed: {e}")

# ── Test 3: Prompts ──────────────────────────────────────────────────────────
print("\n📝 Test 3: Prompts")
try:
    from backend.agents.prompts import (
        CHAT_PARSER_SYSTEM, CHAT_PARSER_HUMAN,
        EXPLAINER_SYSTEM, EXPLAINER_HUMAN,
        REPLANNER_EXPLAIN_SYSTEM, REPLANNER_EXPLAIN_HUMAN,
    )
    assert len(CHAT_PARSER_SYSTEM) > 50, "CHAT_PARSER_SYSTEM too short"
    assert len(EXPLAINER_SYSTEM) > 50, "EXPLAINER_SYSTEM too short"
    print(f"  ✅ CHAT_PARSER_SYSTEM ({len(CHAT_PARSER_SYSTEM)} chars)")
    print(f"  ✅ EXPLAINER_SYSTEM ({len(EXPLAINER_SYSTEM)} chars)")
    print(f"  ✅ REPLANNER_EXPLAIN_SYSTEM ({len(REPLANNER_EXPLAIN_SYSTEM)} chars)")
except Exception as e:
    print(f"  ❌ Prompts failed: {e}")

# ── Test 4: Workflow imports ─────────────────────────────────────────────────
print("\n🔄 Test 4: Workflow imports")
try:
    from backend.agents.workflow import run_workflow, run_replan_workflow
    print("  ✅ run_workflow and run_replan_workflow imported")
except Exception as e:
    print(f"  ❌ Workflow import failed: {e}")

# ── Test 5: Constraint validator (no API key needed) ────────────────────────
print("\n🔍 Test 5: Constraint validator (pure Python)")
try:
    from backend.agents.nodes.constraint_validator import constraint_validator_node
    from backend.agents.state import init_state

    # Missing origin → should block planning
    s1 = init_state(["test"])
    s1["extracted_constraints"] = {"budget_per_person": 10000, "destination_type": "mountains"}
    r1 = constraint_validator_node(s1)
    assert not r1["is_ready_to_plan"], "Should block when origin missing"
    print("  ✅ Blocks when origin missing")

    # Valid constraints → should allow planning
    s2 = init_state(["test"])
    s2["extracted_constraints"] = {
        "origin": "Gurugram", "budget_per_person": 15000, "destination_type": "mountains"
    }
    r2 = constraint_validator_node(s2)
    assert r2["is_ready_to_plan"], "Should allow planning with valid constraints"
    print("  ✅ Allows planning with valid constraints")

    # Destination/type mismatch → should block
    s3 = init_state(["test"])
    s3["extracted_constraints"] = {
        "origin": "Gurugram", "budget_per_person": 15000,
        "destination": "Jaipur", "destination_type": "mountains",
    }
    r3 = constraint_validator_node(s3)
    assert not r3["is_ready_to_plan"], "Should block on destination mismatch"
    print("  ✅ Blocks on destination/destination_type mismatch")
except Exception as e:
    print(f"  ❌ Constraint validator failed: {e}")
    import traceback; traceback.print_exc()

# ── Test 6: Mock data retriever (no API key needed) ──────────────────────────
print("\n🗃️  Test 6: Data retriever with mock data")
try:
    from backend.agents.nodes.data_retriever import data_retriever_node
    s = init_state(["test"])
    s["extracted_constraints"] = {
        "origin": "Gurugram", "destination_type": "mountains",
        "budget_per_person": 15000, "group_size": 4,
    }
    result = data_retriever_node(s)
    assert result["route_candidates"], "No routes returned"
    assert result["hotel_candidates"], "No hotels returned"
    assert result["activity_candidates"], "No activities returned"
    print(f"  ✅ Routes: {len(result['route_candidates'])}, Hotels: {len(result['hotel_candidates'])}, Activities: {len(result['activity_candidates'])}")
except Exception as e:
    print(f"  ❌ Data retriever failed: {e}")
    import traceback; traceback.print_exc()

# ── Test 7: End-to-end LangGraph workflow ────────────────────────────────────
if not MOCK_MODE:
    print("\n🚀 Test 7: End-to-end LangGraph workflow")
    try:
        os.environ["PIPELINE_MODE"] = "langgraph"
        result = run_workflow([
            "Let's do a weekend trip from Gurugram",
            "Budget under 15k per person",
            "Mountains please, not Jaipur",
            "No night driving",
            "Need rafting and good cafes",
        ])
        print(f"  ✅ Workflow completed")
        print(f"  Origin: {result.get('extracted_constraints', {}).get('origin')}")
        dest = (result.get('selected_itinerary') or {}).get('route', {}).get('destination', 'N/A')
        print(f"  Selected destination: {dest}")
        print(f"  Timeline events: {len(result.get('timeline', []))}")
        print(f"  Map points: {len(result.get('map_points', []))}")
        expl = result.get('explanation', '')
        print(f"  Explanation: {expl[:100]}{'...' if len(expl) > 100 else ''}")
        assert result.get("explanation"), "Explanation is empty"
        assert result.get("timeline"), "Timeline is empty"
        assert result.get("map_points"), "Map points are empty"
    except Exception as e:
        print(f"  ❌ Workflow failed: {e}")
        import traceback; traceback.print_exc()

    # ── Test 8: Replan workflow ──────────────────────────────────────────────
    print("\n🔁 Test 8: Replan workflow")
    try:
        base_result = run_workflow(["Trip from Gurugram to mountains, budget 15000, 4 people"])
        delay = {"delay_type": "traffic_jam", "delay_minutes": 90}
        replanned = run_replan_workflow(base_result, delay)
        assert replanned.get("replanned_itinerary") is not None, "replanned_itinerary is None"
        assert replanned.get("replanning_explanation"), "replanning_explanation is empty"
        print(f"  ✅ Replan completed")
        print(f"  Explanation: {replanned.get('replanning_explanation', '')[:100]}")
    except Exception as e:
        print(f"  ❌ Replan failed: {e}")
        import traceback; traceback.print_exc()

    # ── Test 9: Engine switching ─────────────────────────────────────────────
    print("\n🔀 Test 9: augmented_llm engine switch")
    try:
        os.environ["PIPELINE_MODE"] = "augmented_llm"
        result_aug = run_workflow(["Weekend trip from Gurugram, mountains, 15k budget"])
        print(f"  ✅ augmented_llm engine completed")
        print(f"  Origin: {result_aug.get('extracted_constraints', {}).get('origin')}")
    except Exception as e:
        print(f"  ❌ augmented_llm switch failed: {e}")
    finally:
        os.environ["PIPELINE_MODE"] = "langgraph"
else:
    print("\n⏭️  Tests 7–9 skipped (no API key)")

print("\n" + "=" * 60)
print("Bucket 2 validation complete.")
print("=" * 60)
