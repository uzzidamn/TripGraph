"""
Agent 0: pipeline gate — classifies message intent and checks for similar past trips.
Runs before Chat Parser. Exits early on non-trip, invalid, or similar-trip-found messages.
"""
import json

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.llm_client import get_llm_json
from backend.agents.prompts import GUARDRAIL_HUMAN, GUARDRAIL_SYSTEM
from backend.agents.state import TripState
from backend.memory.store import get_user_memory


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif hasattr(block, "text"):
                parts.append(block.text)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
        return "".join(parts)
    return str(content)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _classify_intent(chat_text: str) -> tuple[str, float]:
    """Call LLM to classify message intent. Returns (intent, confidence)."""
    try:
        llm = get_llm_json(run_name="guardrail")
        response = llm.invoke([
            SystemMessage(content=GUARDRAIL_SYSTEM),
            HumanMessage(content=GUARDRAIL_HUMAN.format(chat_text=chat_text)),
        ])
        raw = _extract_text(response.content)
        parsed = json.loads(_strip_fences(raw))
        intent = parsed.get("intent", "trip")
        confidence = float(parsed.get("confidence", 1.0))
        return intent, confidence
    except Exception as e:
        print(f"[guardrail] LLM classification failed: {e} — defaulting to proceed")
        return "trip", 1.0


def _find_similar_trip(past_trips: list[dict], chat_text: str) -> dict | None:
    """
    Fuzzy match: checks if any past_trip destination name appears in the chat text
    and has a status field. Returns the matching past_trip or None.
    """
    chat_lower = chat_text.lower()
    for trip in past_trips:
        destination = str(trip.get("destination") or "").strip()
        if not destination:
            continue
        # Simple string match — destination name in chat text
        if destination.lower() in chat_lower:
            return trip
    return None


def guardrail_node(state: TripState) -> dict:
    raw_chat = state.get("raw_chat") or []
    chat_text = "\n".join(f"- {msg}" for msg in raw_chat)

    # --- 1. Intent classification ---
    intent, confidence = _classify_intent(chat_text)

    if intent == "non_trip" or (intent == "trip" and confidence < 0.4):
        return {"guardrail_result": {
            "action": "clarify",
            "reason": "non_trip_message",
            "response": (
                "This is a trip planning assistant. Please send trip-related messages to get started — "
                "for example, share where you'd like to go, your budget, and the number of days."
            ),
            "matched_trip": None,
        }}

    if intent == "invalid":
        return {"guardrail_result": {
            "action": "clarify",
            "reason": "invalid_prompt",
            "response": (
                "Hey! It looks like you're planning a trip. Could you share a few more details — "
                "like where you want to go, your budget, and how many days?"
            ),
            "matched_trip": None,
        }}

    # --- 2. Similar past-trip detection (only when intent == "trip") ---
    user_id = state.get("user_id")
    memory = get_user_memory(user_id)
    past_trips = memory.get("past_trips", [])
    matched = _find_similar_trip(past_trips, chat_text)

    if matched:
        status = str(matched.get("status", "")).lower()
        destination = matched.get("destination", "this destination")
        date = matched.get("date", "")

        if status == "cancelled":
            return {"guardrail_result": {
                "action": "proceed",
                "reason": "similar_trip_cancelled",
                "response": f"Noted — that trip to {destination} was cancelled. Let me put together a new plan.",
                "matched_trip": matched,
            }}

        if status == "completed":
            return {"guardrail_result": {
                "action": "confirm",
                "reason": "similar_trip_found",
                "response": (
                    f"I found a previous trip with similar details to {destination}. "
                    f"Since that trip is completed, should I plan something new, or would you like the same plan again?"
                ),
                "matched_trip": matched,
            }}

        if status == "planned":
            date_str = f" on {date}" if date else ""
            return {"guardrail_result": {
                "action": "confirm",
                "reason": "similar_trip_found",
                "response": (
                    f"I found a similar planned trip to {destination}{date_str}. "
                    f"Is that trip still on, or do you want a fresh plan?"
                ),
                "matched_trip": matched,
            }}

    # --- 3. No match — proceed normally ---
    return {"guardrail_result": {
        "action": "proceed",
        "reason": "no_prior_match",
        "response": None,
        "matched_trip": None,
    }}
