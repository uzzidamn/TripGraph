"""
Bucket 2 v2 Validation Script.
Tests the agentic pipeline imports, schema, and end-to-end flow.

Run: PYTHONPATH=. python backend/tests/test_bucket_2.py

Tests 1-4 run without any API key.
Tests 5-6 require GOOGLE_API_KEY in .env or environment.
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
print("Bucket 2 v2 — Agentic Pipeline Validation")
print("=" * 60)
if MOCK_MODE:
    print("  ⚠️  GOOGLE_API_KEY not set — LLM tests will be skipped")

# ---------------------------------------------------------------------------
# Test 1: State schema (v2 fields)
# ---------------------------------------------------------------------------
print("\n📋 Test 1: TripState schema")
try:
    from backend.agents.state import TripState, init_state
    check(True, "TripState and init_state imported successfully")

    state = init_state(["test message"], user_id="U_TEST")
    required_keys = [
        # Input
        "raw_chat", "user_id",
        # Guardrail
        "guardrail_result",
        # Memory
        "user_profile", "memory_context", "memory_updates", "visited_destinations",
        # Constraints
        "extracted_constraints", "missing_fields", "assumptions",
        # Validation
        "conflict_report", "is_ready_to_plan",
        # Data retrieval
        "route_candidates", "all_route_candidates",
        "hotel_candidates", "transport_candidates",
        "activity_candidates", "food_candidates", "waypoint_candidates",
        # Planning
        "itinerary_candidates", "selected_itinerary", "alternative_itineraries",
        "validation_report", "score_breakdown", "timeline", "map_points", "cost_breakdown",
        # Explanation
        "explanation",
        # Replanning
        "delay_event", "replanned_itinerary", "replanning_explanation",
    ]
    check(
        all(k in state for k in required_keys),
        f"init_state() has all {len(required_keys)} required fields",
    )
    check(state["raw_chat"] == ["test message"], "raw_chat correctly initialized")
    check(state["user_id"] == "U_TEST", "user_id correctly initialized")
    check(state["is_ready_to_plan"] is False, "is_ready_to_plan defaults to False")
    check(state["selected_itinerary"] is None, "selected_itinerary defaults to None")
    check(state["guardrail_result"] == {}, "guardrail_result defaults to {}")
    check(state["visited_destinations"] == [], "visited_destinations defaults to []")
    check("trace_id" not in state, "trace_id removed in v2")
except Exception as e:
    check(False, f"TripState import/init failed: {e}")

# ---------------------------------------------------------------------------
# Test 2: Memory store
# ---------------------------------------------------------------------------
print("\n🧠 Test 2: Memory store")
try:
    from backend.memory.store import clear_user_memory, get_user_memory, update_user_memory

    check(True, "Memory store imported successfully")
    check(get_user_memory(None) == {}, "get_user_memory(None) returns {}")
    check(get_user_memory("NONEXISTENT") == {}, "get_user_memory for unknown id returns {}")

    update_user_memory("U_STORE_TEST", {"past_trips": [{"destination": "Manali", "status": "completed"}]})
    mem = get_user_memory("U_STORE_TEST")
    check(len(mem.get("past_trips", [])) == 1, "update_user_memory persists past_trips")
    check(mem["past_trips"][0]["destination"] == "Manali", "past_trips entry has correct destination")

    # Null/empty values should not overwrite
    update_user_memory("U_STORE_TEST", {"past_trips": None})
    mem2 = get_user_memory("U_STORE_TEST")
    check(len(mem2.get("past_trips", [])) == 1, "update with None value does not overwrite existing")

    clear_user_memory("U_STORE_TEST")
    check(get_user_memory("U_STORE_TEST") == {}, "clear_user_memory removes all user data")
except Exception as e:
    check(False, f"Memory store test failed: {e}")

# ---------------------------------------------------------------------------
# Test 3: Prompts (v2)
# ---------------------------------------------------------------------------
print("\n📝 Test 3: Prompts")
try:
    from backend.agents.prompts import (
        CHAT_PARSER_HUMAN,
        CHAT_PARSER_SYSTEM,
        EXPLAINER_HUMAN,
        EXPLAINER_SYSTEM,
        GUARDRAIL_HUMAN,
        GUARDRAIL_SYSTEM,
        REPLANNER_EXPLAIN_HUMAN,
        REPLANNER_EXPLAIN_SYSTEM,
    )
    for name, prompt in [
        ("GUARDRAIL_SYSTEM", GUARDRAIL_SYSTEM),
        ("GUARDRAIL_HUMAN", GUARDRAIL_HUMAN),
        ("CHAT_PARSER_SYSTEM", CHAT_PARSER_SYSTEM),
        ("CHAT_PARSER_HUMAN", CHAT_PARSER_HUMAN),
        ("EXPLAINER_SYSTEM", EXPLAINER_SYSTEM),
        ("EXPLAINER_HUMAN", EXPLAINER_HUMAN),
        ("REPLANNER_EXPLAIN_SYSTEM", REPLANNER_EXPLAIN_SYSTEM),
        ("REPLANNER_EXPLAIN_HUMAN", REPLANNER_EXPLAIN_HUMAN),
    ]:
        check(isinstance(prompt, str) and len(prompt) > 50, f"{name} loaded ({len(prompt)} chars)")
    check("{chat_text}" in GUARDRAIL_HUMAN, "GUARDRAIL_HUMAN has {chat_text} placeholder")
    check("{chat_text}" in CHAT_PARSER_HUMAN, "CHAT_PARSER_HUMAN has {chat_text} placeholder")
    check("{memory_context_json}" in EXPLAINER_HUMAN, "EXPLAINER_HUMAN has {memory_context_json} placeholder")
    check("traffic" in REPLANNER_EXPLAIN_SYSTEM, "REPLANNER_EXPLAIN_SYSTEM mentions traffic event type")
    check("road_closure" in REPLANNER_EXPLAIN_SYSTEM, "REPLANNER_EXPLAIN_SYSTEM mentions road_closure")
    check("hotel_unavailable" in REPLANNER_EXPLAIN_SYSTEM, "REPLANNER_EXPLAIN_SYSTEM mentions hotel_unavailable")
except Exception as e:
    check(False, f"Prompts import failed: {e}")

# ---------------------------------------------------------------------------
# Test 4: Workflow imports + node imports
# ---------------------------------------------------------------------------
print("\n🔄 Test 4: Workflow and node imports")
try:
    from backend.agents.workflow import run_replan_workflow, run_workflow
    check(callable(run_workflow), "run_workflow is callable")
    check(callable(run_replan_workflow), "run_replan_workflow is callable")

    import inspect
    sig = inspect.signature(run_workflow)
    check("user_id" in sig.parameters, "run_workflow accepts user_id parameter")

    from backend.agents.nodes.guardrail import guardrail_node
    from backend.agents.nodes.memory_agent import memory_agent_node
    from backend.agents.nodes.memory_updater import memory_updater_node
    check(callable(guardrail_node), "guardrail_node is callable")
    check(callable(memory_agent_node), "memory_agent_node is callable")
    check(callable(memory_updater_node), "memory_updater_node is callable")
except Exception as e:
    check(False, f"Import failed: {e}")

# ---------------------------------------------------------------------------
# Test 5: Memory agent (pure Python — no API key needed)
# ---------------------------------------------------------------------------
print("\n🧩 Test 5: Memory agent (no API key)")
try:
    from backend.agents.nodes.memory_agent import memory_agent_node
    from backend.agents.state import init_state
    from backend.memory.store import clear_user_memory, update_user_memory

    # Seed memory
    update_user_memory("U_MEM_TEST", {
        "preferred_destinations": ["Rishikesh"],
        "preferred_hotel_tier": "comfort",
        "past_trips": [],
    })

    state = init_state(["Let's go somewhere this weekend"], user_id="U_MEM_TEST")
    result = memory_agent_node(state)

    check(result.get("extracted_constraints", {}).get("destination") == "Rishikesh",
          "Memory agent injects Rishikesh from preferred_destinations")
    check(result.get("memory_context", {}).get("source") == "user_memory",
          "memory_context.source == 'user_memory'")
    check(result.get("user_profile", {}).get("preferred_hotel_tier") == "comfort",
          "user_profile populated from memory")
    check(result.get("visited_destinations") == [],
          "visited_destinations is [] when past_trips is empty")

    # Test dedup override
    state2 = init_state(["Let's go back to Rishikesh again"], user_id="U_MEM_TEST")
    state2["visited_destinations"] = ["Rishikesh"]

    # Seed with Rishikesh in past_trips
    update_user_memory("U_MEM_TEST", {"past_trips": [{"destination": "Rishikesh", "status": "completed"}]})
    state3 = init_state(["Let's go back to Rishikesh again"], user_id="U_MEM_TEST")
    result3 = memory_agent_node(state3)
    check(result3.get("memory_context", {}).get("dedup_override") is True,
          "dedup_override=True when 'again' keyword present")

    clear_user_memory("U_MEM_TEST")
except Exception as e:
    check(False, f"Memory agent test failed: {e}")
    import traceback; traceback.print_exc()

# ---------------------------------------------------------------------------
# Test 6: End-to-end workflow (requires API key)
# ---------------------------------------------------------------------------
print("\n🚀 Test 6: End-to-end workflow")
if MOCK_MODE:
    print("  ⏭️  Skipped (no GOOGLE_API_KEY)")
else:
    os.environ["PIPELINE_MODE"] = "langgraph"
    try:
        from backend.agents.workflow import run_replan_workflow, run_workflow
        from backend.memory.store import clear_user_memory, get_user_memory

        clear_user_memory("U_E2E")
        result = run_workflow([
            "Let's do a weekend trip from Gurugram",
            "Budget under 15k per person",
            "Mountains please",
            "No night driving",
            "Need rafting and good cafes",
        ], user_id="U_E2E")

        # Guardrail
        gr = result.get("guardrail_result") or {}
        check(gr.get("action") == "proceed", f"guardrail action=proceed (got {gr.get('action')})")

        # Constraints
        check(bool(result.get("extracted_constraints")), "extracted_constraints populated")
        check(result.get("extracted_constraints", {}).get("origin") == "Gurugram",
              "origin='Gurugram'")
        check(result.get("is_ready_to_plan") is True, "is_ready_to_plan=True")

        # Candidates + planning
        check(bool(result.get("route_candidates")), "route_candidates populated")
        check(result.get("selected_itinerary") is not None, "selected_itinerary is not None")
        check(bool(result.get("timeline")), f"timeline populated ({len(result.get('timeline', []))} events)")
        check(bool(result.get("explanation")), "explanation generated")

        # Memory persistence
        saved = get_user_memory("U_E2E")
        check(len(saved.get("past_trips", [])) >= 1, "memory_updater persisted trip to user memory")

        # Replan
        replan = run_replan_workflow(result, {"type": "traffic", "delay_minutes": 90})
        check(replan.get("replanned_itinerary") is not None, "replanned_itinerary populated")
        check(bool(replan.get("replanning_explanation")), "replanning_explanation generated")

        clear_user_memory("U_E2E")
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
    print("🎉 ALL CHECKS PASSED — Bucket 2 v2 pipeline is valid!")
else:
    print("⚠️  Some checks failed. Review the output above.")
    sys.exit(1)
