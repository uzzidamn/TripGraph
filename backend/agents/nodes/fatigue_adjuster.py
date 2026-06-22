"""Agent 9: Fatigue Adjuster — hybrid per-event fatigue & morale model.

Step 1 (deterministic): pull base scores from the activity/transport catalog.
Step 2 (LLM): contextually adjust each event for cumulative km, prior intensity,
              weather, and time-of-day — and stamp a skippability rating.

If the LLM call fails, we fall back to base scores + a simple heuristic for
skippability so the UI always has something to render.
"""
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.llm_client import extract_text_content, get_llm, strip_code_fences, loads_loose
from backend.agents.prompts import FATIGUE_ADJUSTER_HUMAN, FATIGUE_ADJUSTER_SYSTEM
from backend.agents.state import TripState


def _strip_code_fences(text: str) -> str:
    return strip_code_fences(text)


def _base_scores_for_event(event: dict, lookups: dict) -> tuple[int, int]:
    """Resolve base fatigue + morale from the activity/transport catalogs."""
    eid = event.get("id") or event.get("event_id") or ""
    etype = (event.get("type") or "").lower()

    if etype in ("activity", "experience"):
        a = lookups["activities_by_id"].get(eid) or lookups["activities_by_name"].get((event.get("title") or "").lower())
        if a:
            return int(a.get("fatigue_score_base", 4)), int(a.get("morale_score_base", 6))
    if etype in ("travel", "drive", "transport"):
        t = lookups["transport_by_id"].get(eid)
        if t:
            return int(t.get("fatigue_score", 5)), 5
        # Default for driving legs
        return 6, 4
    if etype in ("meal", "food", "restaurant"):
        return 2, 6
    if etype in ("hotel", "checkin", "checkout"):
        return 1, 5
    return 4, 5


def _skippability_default(adjusted_fatigue: int, adjusted_morale: int, is_signature: bool) -> str:
    if is_signature:
        return "must"
    if adjusted_fatigue >= 8 and adjusted_morale <= 5:
        return "optional"
    if adjusted_morale >= 8:
        return "must"
    return "recommend"


def fatigue_adjuster_node(state: TripState) -> dict:
    """Emit state['fatigue_per_event'] = { event_id: {base, adjusted, skippability, note} }."""
    timeline = state.get("timeline") or []
    if not timeline:
        return {"fatigue_per_event": {}}

    activities = state.get("activity_candidates") or []
    transport = state.get("transport_candidates") or []
    lookups = {
        "activities_by_id": {a.get("activity_id"): a for a in activities if a.get("activity_id")},
        "activities_by_name": {(a.get("name") or "").lower(): a for a in activities if a.get("name")},
        "transport_by_id": {t.get("transport_id"): t for t in transport if t.get("transport_id")},
    }

    # Cumulative km per day from timeline (best-effort)
    km_per_day: dict[int, float] = {}
    for ev in timeline:
        day = ev.get("day") or 1
        km_per_day[day] = km_per_day.get(day, 0.0) + float(ev.get("distance_km") or 0)

    # Weather per day (whatever we already have on state)
    weather_per_day: dict[int, str] = {}
    forecast = state.get("weather_forecast") or {}
    for day, entry in forecast.items() if isinstance(forecast, dict) else []:
        if isinstance(entry, dict):
            weather_per_day[day] = entry.get("summary") or entry.get("description") or "unknown"

    # Compute base scores up front. We REQUIRE a stable `id` on every event
    # (set by timeline_generator) so the frontend can look up fatigue_per_event[ev.id]
    # without re-deriving keys.
    base: dict[str, dict[str, Any]] = {}
    for idx, ev in enumerate(timeline):
        eid = str(ev.get("id") or f"ev_{idx}")
        ev["id"] = eid  # make sure it sticks even if missing
        # Event may carry its own fatigue_score_base (from point_ref), prefer that
        bf_seed = ev.get("fatigue_score_base")
        bm_seed = ev.get("morale_score_base")
        if bf_seed is not None and bm_seed is not None:
            bf, bm = int(bf_seed), int(bm_seed)
        else:
            bf, bm = _base_scores_for_event(ev, lookups)
        base[eid] = {
            "id": eid,
            "title": ev.get("title"),
            "day": ev.get("day") or 1,
            "start_time": ev.get("start_time"),
            "base_fatigue": bf,
            "base_morale": bm,
            "tags": ev.get("tags") or [],
        }

    # Try LLM adjustment
    adjusted: dict[str, Any] = {}
    try:
        llm = get_llm("fatigue")
        response = llm.invoke([
            SystemMessage(content=FATIGUE_ADJUSTER_SYSTEM),
            HumanMessage(content=FATIGUE_ADJUSTER_HUMAN.format(
                days=max(km_per_day.keys()) if km_per_day else 1,
                km_per_day=json.dumps(km_per_day),
                weather_per_day=json.dumps(weather_per_day),
                events_json=json.dumps(list(base.values()), default=str),
            )),
        ])
        raw = _strip_code_fences(extract_text_content(response.content))
        parsed = loads_loose(raw)
        ev_map = parsed.get("events") or {}
        # Build the merged result
        # Pick the highest-morale activity as the trip's "signature"
        signature_id = max(base.values(), key=lambda b: b["base_morale"])["id"] if base else None
        for eid, b in base.items():
            patch = ev_map.get(eid) or {}
            adj_f = int(patch.get("adjusted_fatigue", b["base_fatigue"]))
            adj_m = int(patch.get("adjusted_morale", b["base_morale"]))
            skip = patch.get("skippability") or _skippability_default(adj_f, adj_m, eid == signature_id)
            adjusted[eid] = {
                "base_fatigue": b["base_fatigue"],
                "base_morale": b["base_morale"],
                "adjusted_fatigue": max(0, min(10, adj_f)),
                "adjusted_morale": max(0, min(10, adj_m)),
                "skippability": skip if skip in ("must", "recommend", "optional") else "recommend",
                "note": patch.get("note", ""),
            }
    except Exception as e:
        print(f"  ⚠️  fatigue_adjuster LLM failed ({e}), using base-only fallback")
        signature_id = max(base.values(), key=lambda b: b["base_morale"])["id"] if base else None
        for eid, b in base.items():
            adjusted[eid] = {
                "base_fatigue": b["base_fatigue"],
                "base_morale": b["base_morale"],
                "adjusted_fatigue": b["base_fatigue"],
                "adjusted_morale": b["base_morale"],
                "skippability": _skippability_default(b["base_fatigue"], b["base_morale"], eid == signature_id),
                "note": "",
            }

    return {"fatigue_per_event": adjusted}
