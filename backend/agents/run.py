"""
backend/agents/run.py — Bucket 2 output inspection script.

Run the full workflow and replanning workflow with sample input and
print every field of the resulting TripState so you can see what the
system actually produces.

Usage (from project root):
    PYTHONPATH=. python backend/agents/run.py
    PYTHONPATH=. NEO4J_ENABLED=false python backend/agents/run.py
    PYTHONPATH=. LLM_PROVIDER=claude ANTHROPIC_API_KEY=... python backend/agents/run.py
"""
import json
import os

from dotenv import load_dotenv
load_dotenv()

from backend.agents.workflow import run_workflow, run_replan_workflow

# ── Sample input ──────────────────────────────────────────────────────────────

SAMPLE_CHAT = [
    "Hey everyone — let's plan a weekend trip from Gurugram!",
    "Budget: around 12k per person",
    "Mountains only please, not Jaipur again",
    "No overnight driving, we're all tired after work",
    "Must have river rafting and good cafes",
]

SAMPLE_DELAY_EVENT = {
    "type": "transport_delay",
    "description": "Return bus delayed by 4 hours due to landslide on Rishikesh route",
    "affected_segment": "return_journey",
    "delay_hours": 4,
}

SEP = "=" * 60

# ── Helpers ───────────────────────────────────────────────────────────────────

def _serializable(obj):
    """Recursively convert non-JSON-serializable objects (e.g. dataclasses) to str."""
    if isinstance(obj, dict):
        return {k: _serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serializable(i) for i in obj]
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _print_section(title: str, value) -> None:
    print(f"\n── {title} {'─' * max(0, 50 - len(title))}")
    if isinstance(value, (dict, list)):
        print(json.dumps(_serializable(value), indent=2, ensure_ascii=False))
    else:
        print(value)


# ── Run 1: full workflow ──────────────────────────────────────────────────────

print(SEP)
print("Bucket 2 — Output Inspection")
print(f"NEO4J_ENABLED : {os.getenv('NEO4J_ENABLED', 'false')}")
print(f"LLM_PROVIDER  : {os.getenv('LLM_PROVIDER', 'gemini')}")
print(f"LLM_MODEL     : {os.getenv('LLM_MODEL', 'gemini-2.5-flash-lite-preview-06-17')}")
print(SEP)

print("\nInput chat:")
for line in SAMPLE_CHAT:
    print(f"  > {line}")

print(f"\n{SEP}")
print("Running run_workflow() ...")
print(SEP)

state = run_workflow(SAMPLE_CHAT)

_print_section("extracted_constraints",   state.get("extracted_constraints"))
_print_section("missing_fields",          state.get("missing_fields"))
_print_section("assumptions",             state.get("assumptions"))
_print_section("conflict_report",         state.get("conflict_report"))
_print_section("is_ready_to_plan",        state.get("is_ready_to_plan"))
_print_section("route_candidates",        state.get("route_candidates"))
_print_section("hotel_candidates",        state.get("hotel_candidates"))
_print_section("transport_candidates",    state.get("transport_candidates"))
_print_section("activity_candidates",     state.get("activity_candidates"))
_print_section("food_candidates",         state.get("food_candidates"))
_print_section("waypoint_candidates",     state.get("waypoint_candidates"))
_print_section("selected_itinerary",      state.get("selected_itinerary"))
_print_section("alternative_itineraries", state.get("alternative_itineraries"))
_print_section("validation_report",       state.get("validation_report"))
_print_section("score_breakdown",         state.get("score_breakdown"))
_print_section("timeline",                state.get("timeline"))
_print_section("map_points",              state.get("map_points"))
_print_section("cost_breakdown",          state.get("cost_breakdown"))
_print_section("explanation",             state.get("explanation"))
_print_section("trace_id",               state.get("trace_id"))

# ── Run 2: replanning workflow ────────────────────────────────────────────────

print(f"\n{SEP}")
print("Running run_replan_workflow() ...")
print(SEP)
print("\nDelay event:")
print(json.dumps(SAMPLE_DELAY_EVENT, indent=2))

replan_state = run_replan_workflow(state, SAMPLE_DELAY_EVENT)

_print_section("replanned_itinerary",    replan_state.get("replanned_itinerary"))
_print_section("replanning_explanation", replan_state.get("replanning_explanation"))
_print_section("timeline (updated)",     replan_state.get("timeline"))
_print_section("map_points (updated)",   replan_state.get("map_points"))
_print_section("trace_id",              replan_state.get("trace_id"))

print(f"\n{SEP}")
print("Done.")
