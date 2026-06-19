"""
Agent 1: extract structured travel constraints from raw group chat messages.
"""
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.agents.llm_client import get_llm_json, get_provider
from backend.agents.prompts import CHAT_PARSER_HUMAN, CHAT_PARSER_SYSTEM
from backend.agents.state import TripState


def _extract_text(content) -> str:
    """Extract plain string from LLM response.content (str or list of blocks)."""
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


def _build_messages(system: str, human: str) -> list:
    msgs = [SystemMessage(content=system), HumanMessage(content=human)]
    if get_provider() == "claude":
        msgs.append(AIMessage(content="{"))
    return msgs


def _normalize(constraints: dict) -> tuple[dict, dict]:
    """Normalize casing and apply defaults. Returns (normalized_constraints, assumptions)."""
    assumptions: dict[str, str] = {}

    # Location names → .title()
    for field in ("origin", "destination"):
        if constraints.get(field):
            constraints[field] = str(constraints[field]).strip().title()

    # Enum fields → lowercase
    for field in ("hotel_tier", "risk_tolerance", "destination_type"):
        if constraints.get(field):
            constraints[field] = str(constraints[field]).strip().lower()

    # List enum fields → lowercase items
    for field in ("transport_preference", "must_include"):
        if constraints.get(field):
            constraints[field] = [str(x).strip().lower() for x in constraints[field] if x]

    # Apply defaults (Decisions 1–5)
    if not constraints.get("group_size"):
        constraints["group_size"] = 4
        assumptions["group_size"] = "defaulted to 4"
    if not constraints.get("hotel_tier"):
        constraints["hotel_tier"] = "comfort"
        assumptions["hotel_tier"] = "defaulted to comfort"
    if not constraints.get("risk_tolerance"):
        constraints["risk_tolerance"] = "medium"
        assumptions["risk_tolerance"] = "defaulted to medium"
    if not constraints.get("origin"):
        constraints["origin"] = "Gurugram"
        assumptions["origin"] = "defaulted to Gurugram"
    if not constraints.get("trip_duration"):
        constraints["trip_duration"] = "2D1N"
        assumptions["trip_duration"] = "defaulted to 2D1N"

    # Ensure list fields are always lists
    for field in ("transport_preference", "must_include", "special_requirements"):
        if not isinstance(constraints.get(field), list):
            constraints[field] = []

    # Ensure avoid_night_driving is a bool
    if not isinstance(constraints.get("avoid_night_driving"), bool):
        constraints["avoid_night_driving"] = False

    return constraints, assumptions


def chat_parser_node(state: TripState) -> dict:
    chat_text = "\n".join(f"- {msg}" for msg in state["raw_chat"])
    messages = _build_messages(
        CHAT_PARSER_SYSTEM,
        CHAT_PARSER_HUMAN.format(chat_text=chat_text),
    )

    try:
        llm = get_llm_json(run_name="chat_parser")
        response = llm.invoke(messages)
        raw = _extract_text(response.content)
        if get_provider() == "claude":
            raw = "{" + raw
        raw = _strip_fences(raw)
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Decision 7: retry once with correction message
        print("[chat_parser] Invalid JSON — retrying once")
        try:
            correction = messages + [
                AIMessage(content=raw if "raw" in dir() else ""),
                HumanMessage(content=(
                    "Your previous response was not valid JSON. "
                    "Return ONLY the raw JSON object — no markdown, no explanation."
                )),
            ]
            llm2 = get_llm_json(run_name="chat_parser_retry")
            response2 = llm2.invoke(correction)
            raw2 = _extract_text(response2.content)
            if get_provider() == "claude":
                raw2 = "{" + raw2
            parsed = json.loads(_strip_fences(raw2))
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            parsed = {}
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        raise

    constraints, assumptions = _normalize(parsed)
    return {
        "extracted_constraints": constraints,
        "assumptions": assumptions,
    }
