"""
Agent 5: Explainer
Generates a natural language explanation of why the selected itinerary was chosen.

This is the only node that asks the LLM for prose rather than JSON.
The raw itinerary dict is summarised before passing to the LLM to avoid
non-serializable fields and excessive prompt length.
"""
from backend.agents.llm_client import get_llm
from backend.agents.prompts import EXPLAINER_HUMAN, EXPLAINER_SYSTEM
from backend.agents.state import TripState


def _summarise_itinerary(itinerary: dict) -> dict:
    """Extract key display fields from an itinerary for the LLM prompt."""
    route = itinerary.get("route") or {}
    transport = itinerary.get("transport") or {}
    hotel = itinerary.get("hotel") or {}
    activities = itinerary.get("activities") or []
    cost = itinerary.get("cost_breakdown") or {}
    return {
        "destination": route.get("destination", "Unknown"),
        "transport_mode": transport.get("mode", "unknown"),
        "transport_tier": transport.get("tier", "unknown"),
        "hotel_name": hotel.get("name", "Unknown"),
        "hotel_price": hotel.get("price_per_night", 0),
        "total_cost": cost.get("total", 0),
        "budget_limit": cost.get("budget_limit", 0),
        "activities": ", ".join(a.get("name", "") for a in activities) or "None",
    }


def _summarise_alternatives(alternatives: list[dict]) -> str:
    """Build a brief summary string of alternative itineraries."""
    if not alternatives:
        return "No alternatives generated."
    parts = []
    for alt in alternatives[:3]:
        route = alt.get("route") or {}
        transport = alt.get("transport") or {}
        cost = alt.get("cost_breakdown") or {}
        dest = route.get("destination", "?")
        tier = transport.get("tier", "?")
        total = cost.get("total", 0)
        parts.append(f"{dest} ({tier} tier, ₹{total:,}/person)")
    return "; ".join(parts)


def _summarise_constraints(constraints: dict) -> str:
    """Build a readable one-line summary of user constraints."""
    parts = []
    if constraints.get("destination_type"):
        parts.append(f"wants {constraints['destination_type']}")
    if constraints.get("budget_per_person"):
        parts.append(f"budget ₹{constraints['budget_per_person']:,}/person")
    if constraints.get("avoid_night_driving"):
        parts.append("no night driving")
    if constraints.get("must_include"):
        parts.append(f"must include: {', '.join(constraints['must_include'])}")
    if constraints.get("return_deadline"):
        parts.append(f"return by {constraints['return_deadline']}")
    return "; ".join(parts) if parts else "No specific constraints"


def explainer_node(state: TripState) -> dict:
    """Generate a plain-English explanation of the selected itinerary.

    Summarises the selected itinerary and constraints before sending to the LLM
    to avoid non-serializable fields and reduce token count.
    """
    selected = state.get("selected_itinerary") or {}
    alternatives = state.get("alternative_itineraries") or []
    constraints = state.get("extracted_constraints") or {}
    score = state.get("score_breakdown") or {}
    validation = state.get("validation_report") or {}

    if not selected:
        return {"explanation": "No itinerary was generated."}

    summary = _summarise_itinerary(selected)
    validation_summary = (
        "All constraints satisfied"
        if validation.get("is_valid")
        else f"Violations: {'; '.join(validation.get('hard_constraint_violations', []))}"
    )

    llm = get_llm()
    messages = [
        ("system", EXPLAINER_SYSTEM),
        ("human", EXPLAINER_HUMAN.format(
            destination=summary["destination"],
            transport_mode=summary["transport_mode"],
            transport_tier=summary["transport_tier"],
            hotel_name=summary["hotel_name"],
            hotel_price=summary["hotel_price"],
            total_cost=summary["total_cost"],
            budget_limit=summary["budget_limit"],
            activities=summary["activities"],
            validation_summary=validation_summary,
            final_score=round(score.get("final_score", 0), 1),
            constraints_summary=_summarise_constraints(constraints),
            alternatives_summary=_summarise_alternatives(alternatives),
        )),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            explanation = "".join(parts).strip()
        else:
            explanation = str(content).strip()
    except Exception as e:
        # Degrade gracefully (e.g. Gemini free-tier 429) — build a deterministic
        # explanation so the whole trip doesn't fail on one rate-limited call.
        print(f"  ⚠️  Explainer LLM failed ({e}) — using templated explanation")
        mode = summary["transport_mode"]
        mode_phrase = "flying" if mode == "flight" else f"travelling by {mode.replace('_', ' ')}"
        explanation = (
            f"We selected {summary['destination']} for your trip, {mode_phrase} and staying at "
            f"{summary['hotel_name']}. The plan comes to ₹{summary['total_cost']:,} per person"
            + (f", within your ₹{summary['budget_limit']:,} budget" if summary['budget_limit'] else "")
            + f". Highlights: {summary['activities']}."
        )

    print(f"  ✅ Explainer: {len(explanation)} char explanation")
    return {"explanation": explanation}
