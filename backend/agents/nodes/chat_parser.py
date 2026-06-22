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

# Defaults applied when LLM does not extract a value.
# Notably no `origin` default — we surface a missing_fields warning instead,
# so the user (or geocoder) decides. Hard-defaulting origin caused the
# "Chandigarh → Manali" bug where it silently became "Gurugram".
_DEFAULTS: Dict[str, Any] = {
    "group_size": 4,
    "hotel_tier": "comfort",
    "risk_tolerance": "medium",
    "avoid_night_driving": False,
    "transport_preference": [],
    "must_include": [],
    "special_requirements": [],
}

# Fields that must be non-null for planning to proceed.
# destination_type is no longer required — the LLM can plan from
# `destination` alone via ORS geocoding + KG-then-API enrichment.
_REQUIRED_FIELDS = ["origin"]


def _parse_llm_json(text: Any) -> Dict[str, Any]:
    """Strip markdown code fences and parse JSON from an LLM response.

    Gemini frequently wraps JSON in ```json ... ``` blocks.
    This handles raw JSON, ```json fenced, and ``` fenced responses.
    """
    if isinstance(text, list):
        parts = []
        for part in text:
            if isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
        text = "".join(parts)
    elif not isinstance(text, str):
        text = str(text)

    # Remove markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Remove any trailing backticks
    text = text.strip("`").strip()
    return json.loads(text)


_MAX_STR = 80          # truncate any string field to this length
_MAX_LIST_ITEMS = 12   # max items per list field
_MAX_BUDGET = 5_000_000  # ₹50 lakh — anything above is almost certainly hostile
_MIN_BUDGET = 500       # below this is meaningless
_INJECTION_PATTERNS = (
    "ignore previous", "ignore above", "system:", "assistant:",
    "you are now", "act as", "<script", "javascript:", "data:text/",
    "```", "<<", ">>",
)


def _strip_injection_patterns(value):
    """Reject strings containing prompt-injection patterns outright."""
    if not isinstance(value, str):
        return value
    lowered = value.lower()
    for pat in _INJECTION_PATTERNS:
        if pat in lowered:
            # Suspicious — discard the value entirely rather than try to clean it
            return None
    # Also discard strings that don't look like a sensible travel field
    # (no letters, just symbols, or contains < > { } which suggest HTML/code)
    if any(c in value for c in "<>{}[]") or not any(c.isalpha() for c in value):
        return None
    return value[:_MAX_STR].strip() or None


def _sanitize_constraints(parsed: dict) -> dict:
    """Defense-in-depth: clamp values and strip prompt-injection patterns
    from anything that came back from the LLM. The LLM is instructed to do
    this in the prompt, but we don't trust it 100%."""
    out = dict(parsed or {})

    # String fields → length-clamp + injection-strip
    for f in ("origin", "destination", "destination_type",
              "trip_duration", "dates", "return_deadline",
              "hotel_tier", "risk_tolerance"):
        if f in out and isinstance(out[f], str):
            out[f] = _strip_injection_patterns(out[f])

    # List fields → cap length + sanitize each item
    for f in ("transport_preference", "must_include", "special_requirements"):
        if isinstance(out.get(f), list):
            cleaned = []
            for item in out[f][:_MAX_LIST_ITEMS]:
                s = _strip_injection_patterns(item) if isinstance(item, str) else None
                if s:
                    cleaned.append(s)
            out[f] = cleaned
        else:
            out[f] = []

    # Numeric clamps
    b = out.get("budget_per_person")
    if isinstance(b, (int, float)):
        b = int(b)
        out["budget_per_person"] = b if _MIN_BUDGET <= b <= _MAX_BUDGET else None
    elif b is not None:
        out["budget_per_person"] = None

    g = out.get("group_size")
    if isinstance(g, (int, float)):
        g = int(g)
        out["group_size"] = g if 1 <= g <= 50 else 4
    elif g is not None:
        out["group_size"] = 4

    return out


def chat_parser_node(state: TripState) -> dict:
    """Extract travel constraints from raw chat messages.

    Calls the LLM with the chat messages and returns structured constraints.
    Retries once on JSON parse failure. Falls back to empty defaults on second failure.
    Applies system defaults for any fields not extracted by the LLM.
    """
    raw_chat = state["raw_chat"]
    formatted = "\n".join(f"{i+1}. {msg}" for i, msg in enumerate(raw_chat))

    llm = get_llm("parser")
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

    # ── Server-side guardrails (defense-in-depth on top of prompt instructions) ──
    parsed = _sanitize_constraints(parsed)

    # Identify fields that are still missing (null after defaults)
    missing = [
        f for f in _REQUIRED_FIELDS
        if parsed.get(f) is None
    ]

    # If the parser detected an off-topic / hostile chat, flag it as a hard miss
    if "OFF_TOPIC" in (parsed.get("special_requirements") or []):
        print("  ⚠️  Chat parser: input flagged as off-topic / prompt-injection attempt")
        missing = list(set(missing + ["origin", "destination"]))

    print(f"  ✅ Chat parser: extracted constraints for origin='{parsed.get('origin')}', "
          f"dest_type='{parsed.get('destination_type')}', budget={parsed.get('budget_per_person')}")

    return {
        "extracted_constraints": parsed,
        "missing_fields": missing,
        "assumptions": {},
    }
