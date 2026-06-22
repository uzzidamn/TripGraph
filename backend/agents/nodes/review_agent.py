"""Review agent — the last node in the pipeline.

An LLM "second pair of eyes" that reviews the assembled itinerary for coherence:
  - timing feasibility (can you actually do these events back to back?)
  - geographic sense (is the destination reachable the claimed way?)
  - cost sanity (does the per-person cost look plausible for the tier?)
  - constraint satisfaction (budget, must-include, return deadline, night driving)
  - mode sense (a 2400 km "drive" trip should flag flying)

It returns a structured review with a verdict + notes. It does NOT silently
rewrite the plan — instead it surfaces concrete issues and (where safe) a
recommended fix. The UI renders this under an "AI agent*" disclaimer so the
user knows a model reviewed it.

Output: state['review'] = {
  "verdict": "looks_good" | "minor_issues" | "needs_attention",
  "summary": str,
  "notes": [ {"issue": str, "severity": "low|medium|high", "recommendation": str}, ... ],
  "disclaimer": "Reviewed by an AI agent — verify critical details before booking.",
}
"""
import json

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.llm_client import extract_text_content, get_llm, strip_code_fences
from backend.agents.state import TripState

_SYSTEM = """You are a meticulous travel-plan reviewer for TripGraph AI.

You receive a fully-assembled itinerary (route, transport, hotel, day-by-day
timeline, costs, constraints, and any flight/train advisories). Critically review
it and report issues a careful human planner would catch.

Check for:
- Timing feasibility: are drive durations and event back-to-backs realistic? Flag
  impossible sequences (e.g. arriving 23:00 then a 23:02 check-in is fine, but a
  3-hour activity crammed into a 1-hour slot is not).
- Mode sense: if the trip is very long (>1500 km) and planned as a road drive,
  flag that flying/train is almost certainly better and reference the advisory.
- Cost sanity: does total per-person cost look plausible? Flag suspiciously low
  (e.g. ₹0 transport, ₹0 activities) or missing costs.
- Constraint satisfaction: budget, must-include activities, return deadline,
  avoid-night-driving — are they actually honored?
- Geography: does the destination match the user's intent and region?

OUTPUT RULES:
- Output ONLY one valid JSON object. No markdown.
- verdict ∈ {"looks_good","minor_issues","needs_attention"}.
- notes: 0-5 concrete issues, each with severity low/medium/high and a recommendation.
- Be specific and reference actual numbers/places from the plan.
- If the plan is genuinely fine, return verdict "looks_good" with an empty notes list.

SCHEMA:
{
  "verdict": "...",
  "summary": "one to two sentence overall assessment",
  "notes": [ {"issue": "...", "severity": "low|medium|high", "recommendation": "..."} ]
}
"""

_HUMAN = """Constraints: {constraints}

Selected itinerary (route/transport/hotel/cost): {itinerary}

Day-by-day timeline: {timeline}

Flight advisory: {flights}
Train advisory: {trains}
Total cost per person: ₹{total_cost}
Trip days: {days}

Review this plan. Output only the JSON."""


def _compact_timeline(timeline: list) -> list:
    return [
        {"day": e.get("day"), "start": e.get("start_time"), "end": e.get("end_time"),
         "title": e.get("title"), "type": e.get("type"), "cost": e.get("cost")}
        for e in (timeline or [])
    ]


def review_agent_node(state: TripState) -> dict:
    selected = state.get("selected_itinerary") or {}
    if not selected:
        return {"review": None}

    constraints = state.get("extracted_constraints") or {}
    timeline = state.get("timeline") or []
    cost = (state.get("cost_breakdown") or {}).get("total") or selected.get("total_cost_per_person")
    days = len({e.get("day") for e in timeline}) or 1

    flights = state.get("flights") or {}
    trains = state.get("trains") or {}

    review_itin = {
        "route": selected.get("route"),
        "transport": selected.get("transport"),
        "hotel": {k: (selected.get("hotel") or {}).get(k) for k in ("name", "tier", "price_per_night")},
        "total_cost_per_person": selected.get("total_cost_per_person"),
    }

    fallback = {
        "verdict": "minor_issues",
        "summary": "Automated review could not run; please sanity-check timing and costs yourself.",
        "notes": [],
        "disclaimer": "Reviewed by an AI agent — verify critical details before booking.",
    }

    try:
        llm = get_llm("review")
        resp = llm.invoke([
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=_HUMAN.format(
                constraints=json.dumps(constraints, default=str),
                itinerary=json.dumps(review_itin, default=str),
                timeline=json.dumps(_compact_timeline(timeline), default=str),
                flights=json.dumps(flights.get("advisory") if flights else None, default=str),
                trains=json.dumps(trains.get("advisory") if trains else None, default=str),
                total_cost=cost or 0,
                days=days,
            )),
        ])
        raw = extract_text_content(resp.content).strip()
        raw = strip_code_fences(raw)
        p = json.loads(raw.strip())
        verdict = p.get("verdict") if p.get("verdict") in ("looks_good", "minor_issues", "needs_attention") else "minor_issues"
        notes = []
        for n in (p.get("notes") or [])[:5]:
            notes.append({
                "issue": str(n.get("issue") or ""),
                "severity": n.get("severity") if n.get("severity") in ("low", "medium", "high") else "low",
                "recommendation": str(n.get("recommendation") or ""),
            })
        review = {
            "verdict": verdict,
            "summary": str(p.get("summary") or ""),
            "notes": notes,
            "disclaimer": "Reviewed by an AI agent — verify critical details before booking.",
        }
        print(f"  ✅ Review agent: verdict={verdict}, {len(notes)} note(s)")
        return {"review": review}
    except Exception as e:
        print(f"  ⚠️  Review agent failed ({e})")
        return {"review": fallback}
