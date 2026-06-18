"""
Bucket 2.1 — Tool-Augmented LLM workflow.
Public API: run_workflow(), run_replan_workflow()
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

from backend.agents_augmented.state import TripState, init_state
from backend.agents_augmented.prompts import SYSTEM_PROMPT, REPLAN_CONTEXT_TEMPLATE
from backend.agents_augmented.tool_executor import execute_tool
from backend.agents_augmented.llm_client import create_llm_client

MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", "20"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "25"))

_VALID_KEYS: set[str] = set(TripState.__annotations__.keys())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_user_request(chat_messages: list[str]) -> str:
    chat_text = "\n".join(f"- {msg}" for msg in chat_messages)
    return (
        f"Plan a trip based on these group chat messages:\n\n{chat_text}\n\n"
        "Use the available tools in this order:\n"
        "1. get_routes(origin) to find routes.\n"
        "2. get_hotels(), get_activities(), get_transport_options(), "
        "get_restaurants(), get_waypoints() for each route.\n"
        "3. generate_candidates(constraints, data) — data keys must be: "
        "routes, hotels, transport, activities, food, waypoints.\n"
        "4. score_itinerary() and validate_itinerary() on the best candidate.\n"
        "5. generate_timeline() on the selected itinerary.\n"
        "Then return the complete TripState JSON."
    )


def _strip_fences(content: str) -> str:
    """Strip ```json or ``` markdown fences from LLM response text."""
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]  # drop opening fence line
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _parse_final_answer(content: str, state: dict) -> TripState:
    """
    Parse LLM text as TripState JSON.
    Strips markdown fences, merges known keys into state.
    Never raises — falls back to setting explanation on parse failure.
    """
    text = _strip_fences(content)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                if k in _VALID_KEYS:
                    state[k] = v
    except (json.JSONDecodeError, ValueError):
        state["explanation"] = content

    return TripState(**{k: state.get(k) for k in _VALID_KEYS})


def _react_loop(llm, state: dict) -> dict:
    """Shared ReAct execution loop for both workflow functions."""
    tool_call_count = 0
    iteration_count = 0
    _json_retried = False  # Decision 7: retry invalid JSON once

    while True:
        if tool_call_count >= MAX_TOOL_CALLS or iteration_count >= MAX_ITERATIONS:
            state["conflict_report"] = {"error": "execution_limit_exceeded"}
            return state

        iteration_count += 1
        response = llm.invoke()

        if response["type"] == "tool_call":
            tool_call_count += 1
            result = execute_tool(response["tool_name"], response["arguments"])
            llm.add_tool_result(
                response["tool_call_id"],
                response["tool_name"],
                result,
            )

        elif response["type"] == "final_answer":
            content = response["content"]
            # Decision 7: if response is not valid JSON, retry once with a correction
            try:
                json.loads(_strip_fences(content))
                return _parse_final_answer(content, state)
            except (json.JSONDecodeError, ValueError):
                if not _json_retried:
                    _json_retried = True
                    print("[WORKFLOW] Final answer was not valid JSON — retrying once.")
                    llm.add_user_message(
                        "Your previous response was not valid JSON. "
                        "Return ONLY a raw JSON object for the TripState — "
                        "no markdown fences, no code blocks, no explanation text, just the JSON."
                    )
                    # Loop continues: llm.invoke() will be called again
                else:
                    # Second failure — return partial state with explanation set
                    return _parse_final_answer(content, state)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_workflow(chat_messages: list[str]) -> TripState:
    """
    Run the full planning workflow.
    The LLM autonomously calls tools until it produces a complete TripState.
    """
    state = dict(init_state(chat_messages))
    llm = create_llm_client(SYSTEM_PROMPT)
    llm.add_user_message(_format_user_request(chat_messages))
    return _react_loop(llm, state)


def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    """
    Replan an existing trip after a delay event.
    Uses the same ReAct loop; populates replanned_itinerary and replanning_explanation.
    """
    updated = dict(state)
    updated["delay_event"] = delay_event

    if not state.get("selected_itinerary"):
        updated["replanning_explanation"] = "No itinerary available to replan."
        return TripState(**{k: updated.get(k) for k in _VALID_KEYS})

    context = REPLAN_CONTEXT_TEMPLATE.format(
        existing_trip_state=json.dumps(state, default=str),
        delay_event=json.dumps(delay_event, default=str),
    )

    llm = create_llm_client(SYSTEM_PROMPT)
    llm.add_user_message(context)

    result = _react_loop(llm, updated)

    # Ensure replanning fields are surfaced even if LLM returned full state
    updated["replanned_itinerary"] = result.get("replanned_itinerary")
    updated["replanning_explanation"] = result.get("replanning_explanation")
    return TripState(**{k: updated.get(k) for k in _VALID_KEYS})
