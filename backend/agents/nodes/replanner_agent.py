"""
Agent 6: handle delay events — call replan_itinerary() then explain changes.
"""
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.agents.llm_client import get_llm_json, get_provider
from backend.agents.prompts import REPLANNER_EXPLAIN_HUMAN, REPLANNER_EXPLAIN_SYSTEM
from backend.agents.state import TripState
from backend.planner.replanner import replan_itinerary


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


def _build_messages(system: str, human: str) -> list:
    msgs = [SystemMessage(content=system), HumanMessage(content=human)]
    if get_provider() == "claude":
        msgs.append(AIMessage(content="{"))
    return msgs


def _safe_json(obj) -> str:
    if isinstance(obj, dict):
        obj = {k: v for k, v in obj.items() if k != "trip_graph"}
    return json.dumps(obj, default=str, ensure_ascii=False)


def replanner_agent_node(state: TripState) -> dict:
    itinerary = state.get("selected_itinerary") or {}
    delay_event = state.get("delay_event") or {}
    constraints = state.get("extracted_constraints") or {}

    # Call the Python replanner
    replan_result = replan_itinerary(itinerary, delay_event, constraints)
    updated_itinerary = replan_result.get("updated_itinerary") or itinerary
    changes = replan_result.get("changes") or []

    human_prompt = REPLANNER_EXPLAIN_HUMAN.format(
        constraints_json=_safe_json(constraints),
        original_itinerary_json=_safe_json(itinerary),
        updated_itinerary_json=_safe_json(updated_itinerary),
        changes_json=json.dumps(changes, default=str),
        delay_event_json=json.dumps(delay_event, default=str),
    )
    messages = _build_messages(REPLANNER_EXPLAIN_SYSTEM, human_prompt)

    try:
        llm = get_llm_json(run_name="replanner_agent")
        response = llm.invoke(messages)
        raw = _extract_text(response.content)
        if get_provider() == "claude":
            raw = "{" + raw
        parsed = json.loads(_strip_fences(raw))
        replanning_explanation = parsed.get("replanning_explanation", "")
    except json.JSONDecodeError:
        print("[replanner_agent] Invalid JSON — retrying once")
        try:
            correction = messages + [
                HumanMessage(content=(
                    "Your previous response was not valid JSON. "
                    'Return ONLY {"replanning_explanation": "..."} — no markdown, no extra text.'
                )),
            ]
            llm2 = get_llm_json(run_name="replanner_agent_retry")
            response2 = llm2.invoke(correction)
            raw2 = _extract_text(response2.content)
            if get_provider() == "claude":
                raw2 = "{" + raw2
            parsed2 = json.loads(_strip_fences(raw2))
            replanning_explanation = parsed2.get("replanning_explanation", "")
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            replanning_explanation = ""
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        raise

    return {
        "replanned_itinerary": updated_itinerary,
        "replanning_explanation": replanning_explanation,
    }
