"""Insights agent — runs AFTER the main pipeline (data_retriever, planner,
enricher, fatigue) to layer in additional context pulled from DuckDuckGo's
Instant Answer API.

Why: KG + Geoapify + LLM-enricher together give you the structural plan, but
they don't pull arbitrary up-to-date "did you know" context. DDG fills that
gap cheaply (free, no key). Think Wikipedia-style abstract for the destination
+ each top hotel/activity.

Strategy (latency-aware):
  - Look up at most N_QUERIES distinct places per run (destination + top
    hotel + top 2 activities → 4 calls). DDG is fast (~300ms each) but we
    serialize to stay under the FastAPI 60s timeout comfortably.
  - Cache results into backend/data/ddg_cache.json so repeats are instant.
  - Output onto state['insights_per_place'] keyed by a stable place_id so the
    frontend can render them on EventPopover.
"""
import json
from pathlib import Path
from typing import Any

from backend.api_clients.duckduckgo_client import DuckDuckGoClient
from backend.agents.state import TripState

_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "ddg_cache.json"
_MAX_QUERIES_PER_RUN = 4


def _load_cache() -> dict:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        print(f"  ⚠️  Failed to write DDG cache: {e}")


def _build_query(name: str, kind: str, destination: str) -> str:
    """Compose a sensible DDG query string for each place type."""
    name = (name or "").strip()
    destination = (destination or "").strip()
    if not name:
        return ""
    if kind == "destination":
        return name
    if kind == "hotel":
        return f"{name} hotel {destination}".strip()
    if kind == "activity":
        return f"{name} {destination}".strip()
    return name


def insights_agent_node(state: TripState) -> dict:
    """Enrich up to N places with DuckDuckGo abstracts; cache aggressively."""
    selected = state.get("selected_itinerary") or {}
    route = selected.get("route") or {}
    hotel = selected.get("hotel") or {}
    activities = selected.get("activities") or []

    destination = route.get("destination") or ""
    if not destination:
        return {"insights_per_place": {}}

    cache = _load_cache()
    results: dict[str, dict[str, Any]] = {}

    queries: list[tuple[str, str, str]] = []
    # 1. The destination itself
    queries.append((f"destination:{destination}", "destination", destination))
    # 2. Selected hotel (if any)
    if hotel.get("name"):
        hid = hotel.get("hotel_id") or hotel["name"]
        queries.append((f"hotel:{hid}", "hotel", hotel["name"]))
    # 3. Up to 2 top activities (highest morale first)
    sorted_acts = sorted(
        [a for a in activities if a.get("name")],
        key=lambda a: int(a.get("morale_score_base") or 5),
        reverse=True,
    )
    for act in sorted_acts[:2]:
        aid = act.get("activity_id") or act["name"]
        queries.append((f"activity:{aid}", "activity", act["name"]))

    queries = queries[:_MAX_QUERIES_PER_RUN]
    new_lookups = 0

    for place_id, kind, name in queries:
        query = _build_query(name, kind, destination)
        if not query:
            continue
        if query in cache:
            results[place_id] = cache[query]
            continue

        data = DuckDuckGoClient.search(query, max_related=3)
        if data:
            cache[query] = data
            results[place_id] = data
            new_lookups += 1

    if new_lookups:
        _save_cache(cache)

    print(f"  ✅ Insights agent: {len(results)} places enriched "
          f"({new_lookups} new DDG lookups, {len(results) - new_lookups} cached)")

    return {"insights_per_place": results}
