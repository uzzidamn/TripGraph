"""
Agent 6: Replanner Agent
Handles delay simulation by calling the deterministic replanner,
then explains the changes via LLM.
"""
from backend.agents.llm_client import get_llm
from backend.agents.prompts import REPLANNER_EXPLAIN_HUMAN, REPLANNER_EXPLAIN_SYSTEM
from backend.agents.state import TripState
from backend.planner.replanner import replan_itinerary


def replanner_agent_node(state: TripState) -> dict:
    """Replan an existing itinerary around a delay event.

    Step 1: Calls the deterministic replanner to shift/compress/drop events.
    Step 2: Calls the LLM to explain the changes in plain English.
    """
    selected = state.get("selected_itinerary") or {}
    delay_event = state.get("delay_event") or {}
    constraints = state.get("extracted_constraints") or {}

    if not selected or not delay_event:
        return {
            "replanned_itinerary": selected,
            "replanning_explanation": "No delay event provided — itinerary unchanged.",
        }

    # Step 1: Deterministic replanning (no LLM)
    replan_result = replan_itinerary(selected, delay_event, constraints)
    updated_itinerary = replan_result.get("updated_itinerary", selected)
    changes = replan_result.get("changes", [])
    delay_absorbed = replan_result.get("delay_absorbed", 0)
    delay_remaining = replan_result.get("delay_remaining", 0)

    # Step 2: LLM explanation of what changed
    validation = state.get("validation_report") or {}
    constraints_ok = (
        "Return deadline and must-include activities still satisfied"
        if validation.get("is_valid", True)
        else f"Warning: {'; '.join(validation.get('hard_constraint_violations', []))}"
    )

    changes_formatted = "\n".join(f"- {c}" for c in changes) if changes else "- No changes required"

    llm = get_llm()
    messages = [
        ("system", REPLANNER_EXPLAIN_SYSTEM),
        ("human", REPLANNER_EXPLAIN_HUMAN.format(
            delay_type=delay_event.get("delay_type", "departure_delay"),
            delay_minutes=delay_event.get("delay_minutes", 0),
            delay_absorbed=round(delay_absorbed),
            delay_remaining=round(delay_remaining),
            changes_list=changes_formatted,
            constraints_ok=constraints_ok,
        )),
    ]

    try:
        response = llm.invoke(messages)
        explanation = response.content.strip()
    except Exception as e:
        print(f"  ❌ LLM call failed in replanner agent: {e}")
        raise

    print(f"  ✅ Replanner: {len(changes)} changes, "
          f"absorbed={round(delay_absorbed)}min, remaining={round(delay_remaining)}min")

    # Embed changes inside the dict so replanner_routes.py can pop it out
    return {
        "replanned_itinerary": {**updated_itinerary, "changes": changes},
        "replanning_explanation": explanation,
    }
