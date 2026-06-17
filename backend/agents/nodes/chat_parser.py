"""
Agent 1: Chat Parser
Extracts structured travel constraints from raw group chat messages via LLM.
"""
import json
import re
from typing import Any, Dict

from backend.agents.llm_client import get_llm
from backend.agents.prompts import CHAT_PARSER_HUMAN, CHAT_PARSER_SYSTEM
from backend.agents.state import TripState

# Defaults applied when LLM does not extract a value
_DEFAULTS: Dict[str, Any] = {
    "origin": "Gurugram",
    "group_size": 4,
    "hotel_tier": "comfort",
    "risk_tolerance": "medium",
    "trip_duration": "2D1N",
    "avoid_night_driving": False,
    "transport_preference": [],
    "must_include": [],
    "special_requirements": [],
}

# Fields that must be non-null for planning to proceed
_REQUIRED_FIELDS = ["origin", "budget_per_person", "destination_type"]


def _parse_llm_json(text: str) -> Dict[str, Any]:
    """Strip markdown code fences and parse JSON from an LLM response.

    Gemini frequently wraps JSON in ```json ... ``` blocks.
    This handles raw JSON, ```json fenced, and ``` fenced responses.
    """
    # Remove markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Remove any trailing backticks
    text = text.strip("`").strip()
    return json.loads(text)


def chat_parser_node(state: TripState) -> dict:
    """Extract travel constraints from raw chat messages.

    Calls the LLM with the chat messages and returns structured constraints.
    Retries once on JSON parse failure. Falls back to empty defaults on second failure.
    Applies system defaults for any fields not extracted by the LLM.
    """
    raw_chat = state["raw_chat"]
    formatted = "\n".join(f"{i+1}. {msg}" for i, msg in enumerate(raw_chat))

    llm = get_llm()
    messages = [
        ("system", CHAT_PARSER_SYSTEM),
        ("human", CHAT_PARSER_HUMAN.format(chat_messages=formatted)),
    ]

    parsed: Dict[str, Any] = {}
    for attempt in range(2):
        try:
            response = llm.invoke(messages)
            parsed = _parse_llm_json(response.content)
            break
        except json.JSONDecodeError as e:
            if attempt == 0:
                print(f"  ⚠️  Chat parser JSON parse failed (attempt 1), retrying: {e}")
            else:
                print(f"  ❌ Chat parser JSON parse failed after retry: {e}")
                parsed = {}
        except Exception as e:
            print(f"  ❌ LLM call failed: {e}")
            raise

    # Apply defaults for missing or null fields
    for field, default in _DEFAULTS.items():
        if parsed.get(field) is None:
            parsed[field] = default

    # Identify fields that are still missing (null after defaults)
    missing = [
        f for f in _REQUIRED_FIELDS
        if parsed.get(f) is None
    ]

    print(f"  ✅ Chat parser: extracted constraints for origin='{parsed.get('origin')}', "
          f"dest_type='{parsed.get('destination_type')}', budget={parsed.get('budget_per_person')}")

    return {
        "extracted_constraints": parsed,
        "missing_fields": missing,
        "assumptions": {},
    }
