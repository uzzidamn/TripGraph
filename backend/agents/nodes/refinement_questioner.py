"""Agent 8: Refinement Questioner — produces 1 round of 4 LLM-generated
counter-questions that sharpen the trip plan before generation.

Used by /api/refinement-questions (between parse-chat and generate-itinerary).
Returns a list of questions in a frozen schema; the frontend renders them as
toggle pills or checkbox grids, the answers are merged back into constraints
before the planner runs.
"""
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.llm_client import extract_text_content, get_llm, strip_code_fences, loads_loose
from backend.agents.prompts import REFINEMENT_QUESTIONER_HUMAN, REFINEMENT_QUESTIONER_SYSTEM
from backend.agents.state import TripState


# Static fallback when the LLM call fails or returns malformed JSON.
# Keeps the UI flow unblocked.
_FALLBACK_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "early_start",
        "prompt": "Leave by 5 AM on Day 1 to beat traffic?",
        "kind": "boolean",
        "options": None,
        "default": True,
        "why_it_matters": "Earlier start = roadside breakfast stop + arrive by lunch.",
    },
    {
        "id": "meal_vibe",
        "prompt": "Pick the dining vibe",
        "kind": "checkbox",
        "options": ["Local dhabas", "One standout meal", "Hotel dining", "Street food crawl"],
        "default": ["One standout meal"],
        "why_it_matters": "Shapes restaurant ranking and food budget.",
    },
    {
        "id": "stay_location",
        "prompt": "Pick stay priority",
        "kind": "checkbox",
        "options": ["Closest to action", "Scenic / quiet", "Best deal", "Family-friendly"],
        "default": ["Closest to action"],
        "why_it_matters": "Drives which hotel cluster we rank first.",
    },
    {
        "id": "pace",
        "prompt": "Prefer a packed itinerary over a chill one?",
        "kind": "boolean",
        "options": None,
        "default": False,
        "why_it_matters": "Controls how many activities we slot per day.",
    },
]


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    return strip_code_fences(text)


def refinement_questioner_node(state: TripState) -> dict:
    """Generate 4 refinement questions tailored to current constraints."""
    constraints = state.get("extracted_constraints") or {}
    assumptions = state.get("assumptions") or {}

    if not constraints:
        return {"refinement_questions": _FALLBACK_QUESTIONS}

    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content=REFINEMENT_QUESTIONER_SYSTEM),
            HumanMessage(content=REFINEMENT_QUESTIONER_HUMAN.format(
                constraints=json.dumps(constraints, indent=2, default=str),
                assumptions=json.dumps(assumptions, default=str),
            )),
        ])
        raw = _strip_code_fences(extract_text_content(response.content))
        parsed = loads_loose(raw)
        questions = parsed.get("questions") or []
        if not isinstance(questions, list) or len(questions) != 4:
            raise ValueError(f"Expected exactly 4 questions, got {len(questions)}")
        # Normalise each question — fill defaults for missing fields rather than failing
        out = []
        for q in questions:
            out.append({
                "id": str(q.get("id") or f"q_{len(out)+1}"),
                "prompt": str(q.get("prompt") or "?"),
                "kind": "boolean" if q.get("kind") == "boolean" else "checkbox",
                "options": q.get("options"),
                "default": q.get("default"),
                "why_it_matters": str(q.get("why_it_matters") or ""),
            })
        return {"refinement_questions": out}
    except Exception as e:
        print(f"  ⚠️  refinement_questioner LLM failed ({e}), using fallback bank")
        return {"refinement_questions": _FALLBACK_QUESTIONS}


def apply_refinement_answers(constraints: dict, answers: dict) -> dict:
    """Merge user answers back into the constraints dict.

    Heuristic mapping for well-known IDs; unknown IDs are stored under
    `refinement_extras` so downstream prompts can still see them.
    """
    if not answers:
        return constraints

    out = dict(constraints)
    extras: dict[str, Any] = {}

    for qid, val in answers.items():
        if qid == "early_start" and isinstance(val, bool):
            out.setdefault("special_requirements", []).append(
                "Depart before sunrise on Day 1" if val else "Avoid early-morning departures"
            )
        elif qid == "meal_vibe" and isinstance(val, list):
            out["meal_vibe"] = val
        elif qid == "stay_location" and isinstance(val, list):
            out["stay_priority"] = val
        elif qid == "pace" and isinstance(val, bool):
            out["pace"] = "packed" if val else "chill"
        else:
            extras[qid] = val

    if extras:
        out["refinement_extras"] = extras
    return out
