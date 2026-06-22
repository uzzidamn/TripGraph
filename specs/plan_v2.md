# Plan: Bucket 2 v2 — Execution Plan

**Spec source:** `specs/bucket2_v2.md`
**Baseline:** Bucket 2 v1 fully implemented and tested.

---

## Implementation Status

### Phase 1 — Core Pipeline (Complete)

| Step | What | Files | Status |
|---|---|---|---|
| 1 | TripState: 32 core fields, `user_id`, `all_route_candidates` | `backend/agents/state.py` | ✅ Done |
| 2 | Memory Store: `get_user_memory()` / `update_user_memory()`, thread-safe | `backend/memory/store.py` | ✅ Done |
| 3 | Prompts: `GUARDRAIL_*`, updated `EXPLAINER_*` | `backend/agents/prompts.py` | ✅ Done |
| 4 | Guardrail node: LLM intent classification + past-trip detection | `backend/agents/nodes/guardrail.py` | ✅ Done |
| 5 | Memory Agent node: load + merge user memory | `backend/agents/nodes/memory_agent.py` | ✅ Done |
| 6 | Memory Updater node: persist completed trip | `backend/agents/nodes/memory_updater.py` | ✅ Done |
| 7 | Route Retriever: fetch + dedup; write `route_candidates` + `all_route_candidates` | `backend/agents/nodes/data_retriever.py` | ✅ Done |
| 8 | 5 domain sub-nodes as real LangGraph graph citizens | `hotel/transport/activity/food/waypoint_retriever.py` | ✅ Done |
| 9 | LangGraph Send fan-out: `_dispatch_retrievers` → 5 sub-nodes | `backend/agents/workflow.py` | ✅ Done |
| 10 | Planner Orchestrator: uses `route_candidates`; falls back to `all_route_candidates` | `backend/agents/nodes/planner_orchestrator.py` | ✅ Done |
| 11 | Explainer: memory influence + dedup sections | `backend/agents/nodes/explainer.py` | ✅ Done |
| 12 | Replanner: 4 event types (traffic, road_closure, flight_delay, hotel_unavailable) | `backend/agents/nodes/replanner_agent.py` | ✅ Done |
| 13 | Workflow rebuild: 13-node graph; `_route_after_guardrail`; `_route_after_retriever` (unsupported-route early-exit + Send fan-out) | `backend/agents/workflow.py` | ✅ Done |
| 14 | run.py: `user_id`, all fields, memory persistence check | `backend/agents/run.py` | ✅ Done |
| 15 | Tests: 57 cases (55 taxonomy + 2 TC041 dedup E2E) | `backend/tests/test_prompt_taxonomy.py` | ✅ Done |
| 16 | Decisions log | `specs/logs/bucket_2_decisions.md` | ✅ Done |

---

### Phase 2 — API, Test Console & Observability (Complete)

| Step | Spec ref | What | Files | Status |
|---|---|---|---|---|
| 17 | G.0 | LangSmith config: `configure_langsmith()` no-op when key absent; `get_runnable_config()` returns `RunnableConfig`; called at workflow import | `backend/config.py`, `backend/agents/workflow.py` | ✅ Done |
| 18 | G.0 | Eval API: `POST /api/eval/run-dataset` streaming NDJSON; 31 cases; filter by category or case IDs; `GET /api/eval/categories` | `backend/api/eval.py`, `backend/main.py` | ✅ Done (partial — 31 cases, no start event; see Phase 5) |
| 19 | G.0 | Frontend: React+Vite scaffold; `EvalPanel.jsx`; `ResultsTable.jsx`; `/eval` tab; `VITE_API_URL` | `frontend/` | ✅ Done (partial — shows 31 cases; see Phase 5) |
| 20a | F.1 | Expand `ParseChatResponse` + `ItineraryResponse` to include all agent output fields | `backend/models/responses.py` | ✅ Done |
| 20b | F.2 | Guardrail banners in test console for `clarify` / `confirm` actions | `backend/api/test_client_html.py` | ✅ Done |
| 20c | F.3 | Pipeline Agent Trace card: per-agent steps with green/amber/red borders | `backend/api/test_client_html.py` | ✅ Done |
| 20d | F.4 | Interactive Clarification Form when `missing_fields` non-empty | `backend/api/test_client_html.py` | ✅ Done |
| 20e | F.5 | CSS: `.trace-step`, `.clarify-grid`, `.suggestion-cards` | `backend/api/test_client_html.py` | ✅ Done |
| 20f | F.6 | No silent assumptions: `_normalize()` is type-only; 5 required fields each checked independently by validator | `backend/agents/nodes/chat_parser.py`, `backend/agents/nodes/constraint_validator.py` | ✅ Done |
| 20g | F.7 | Failure path priority in `generateItinerary()`: unsupported → guardrail → missing → violations | `backend/api/test_client_html.py` | ✅ Done |
| 20h | F.8 | Unsupported route: `unsupported_route` + `suggested_routes` in TripState; Check 1 + Check 2 in route retriever; `_route_after_retriever` exits to END; [Route] Not in Catalog card + suggestion cards | `backend/agents/state.py`, `backend/agents/nodes/data_retriever.py`, `backend/agents/workflow.py`, `backend/models/responses.py`, `backend/api/test_client_html.py` | ✅ Done |
| 20i | F.9 | Response model completeness rule: state.py + api/*.py + responses.py all updated together | Policy enforced | ✅ Done |

---

### Phase 3 — Guardrail Action Cleanup (Complete)

The spec removed `"ignore"` from `guardrail_result.action`. The implementation still uses `"ignore"` in two places that must be updated.

| Step | What | Files | Status |
|---|---|---|---|
| 21 | Remove `"ignore"` from guardrail node output — non-trip and social messages must use `"clarify"` instead. The `action` enum is now `"proceed" \| "clarify" \| "confirm"` only. | `backend/agents/nodes/guardrail.py` | ✅ Done |
| 22 | Update `_route_after_guardrail` in workflow to route on `("clarify", "confirm")` only — remove `"ignore"` from the tuple. | `backend/agents/workflow.py` | ✅ Done |
| 23 | Update any test assertions that check `action == "ignore"` to `action == "clarify"`. | `backend/tests/test_prompt_taxonomy.py`, `backend/api/eval.py` | ✅ Done |

---

### Phase 4 — LangSmith Run ID Capture (Complete)

The spec (G.0) requires the root workflow run ID to be captured and stored in `TripState.langsmith_run_id` via a `RunIdCapture` callback. This enables post-run feedback (eval pass/fail, LLM-judge scores) to be linked to the correct LangSmith trace.

| Step | What | Files | Status |
|---|---|---|---|
| 24 | Add `langsmith_run_id: Optional[str]` to `TripState`; initialise to `None` in `init_state` | `backend/agents/state.py` | ✅ Done |
| 25 | Add `RunIdCapture` callback class to `backend/config.py`; update `get_runnable_config()` to accept an optional `callbacks` list | `backend/config.py` | ✅ Done |
| 26 | Instantiate `RunIdCapture` in `_langgraph_run_workflow()`; pass it in `get_runnable_config(..., callbacks=[capture])`; after `app.invoke()` set `state["langsmith_run_id"] = capture.run_id` | `backend/agents/workflow.py` | ✅ Done |

**`RunIdCapture` implementation (spec G.0):**

```python
class RunIdCapture:
    def __init__(self):
        self.run_id: str | None = None

    def on_chain_start(self, serialized, inputs, *, run_id, **kwargs):
        if self.run_id is None:   # capture only the root run
            self.run_id = str(run_id)
```

Usage in workflow:
```python
capture = RunIdCapture()
config  = get_runnable_config("tripgraph-plan", metadata=run_metadata, callbacks=[capture])
state   = app.invoke(initial, config=config)
state["langsmith_run_id"] = capture.run_id
```

---

### Phase 5 — LLM-as-a-Judge (Complete)

Two test cases (TC014, TC084) require subjective quality evaluation that cannot be captured by a deterministic assertion. The spec defines an `llm_judge()` helper that scores the output 1–5 and posts the result as structured feedback to LangSmith.

| Step | What | Files | Status |
|---|---|---|---|
| 27 | Add `llm_judge(text, rubric, threshold=4, run_id=None) -> int` to `test_prompt_taxonomy.py`; call `langsmith.Client().create_feedback()` when `run_id` and `LANGCHAIN_API_KEY` are set | `backend/tests/test_prompt_taxonomy.py` | ✅ Done |
| 28 | Wire `llm_judge` into TC014 and TC084 assertions; pass `state.get("langsmith_run_id")` as `run_id` | `backend/tests/test_prompt_taxonomy.py` | ✅ Done |

**`llm_judge` implementation (spec G.0):**

```python
def llm_judge(text: str, rubric: str, threshold: int = 4, run_id: str | None = None) -> int:
    # call LLM to score text on rubric 1-5
    score = ...
    if run_id and os.getenv("LANGCHAIN_API_KEY"):
        langsmith.Client().create_feedback(
            run_id  = run_id,
            key     = "llm_judge_score",
            score   = score / 5,
            value   = str(score),
            comment = rubric[:120],
        )
    return score
```

---

### Phase 6 — Eval Dataset Expansion (Complete)

The eval dataset must grow from 31 to 116 cases. The spec defines all 116 in G.2. The current implementation covers only a subset (primarily Guardrail, partial Constraint Extraction, and key dedup cases).

| Step | What | Files | Status |
|---|---|---|---|
| 29 | Add `{"type":"start","total":N}` as the first NDJSON line in `event_stream()`, before any case result. Frontend must handle this as a metadata event (not a result row). | `backend/api/eval.py` | ✅ Done |
| 30 | Add missing cases to `GOLDEN_DATASET`: TC003–TC006, TC008–TC015 (Constraint Extraction); TC017, TC019–TC025 (Missing Information); TC026–TC035 (Contradictions); TC037–TC040, TC044–TC045 (User Memory); TC041b, TC041_filter (Past-Trip Dedup); TC046–TC055 (Destination Retrieval); TC056–TC065 (Activity Matching); TC068–TC069, TC071–TC075 (Budget Validation); TC077–TC078, TC080–TC085 (Replanning); TC087–TC090 (Parallel); TC091–TC095 (Multi-turn); TC097, TC099–TC100 (Edge Cases); MU001–MU003 (Memory Updater) | `backend/api/eval.py` | ✅ Done |
| 31 | `GET /api/eval/categories` total is now 116; all 14 categories returned dynamically | `backend/api/eval.py` | ✅ Done |
| 32 | Update `EvalPanel.jsx`: change hardcoded count (31 → 116); update `CATEGORIES` list to all 14; update streaming reader to handle `{"type":"start","total":N}` first event (sets progress total); show "No matching cases" banner when `total === 0` | `frontend/src/components/eval/EvalPanel.jsx` | ✅ Done |

**14 categories** (spec G.0):
`Guardrail`, `Constraint Extraction`, `Missing Information`, `Contradictions`, `User Memory`, `Past-Trip Dedup`, `Destination Retrieval`, `Activity Matching`, `Budget Validation`, `Replanning`, `Parallel Execution`, `Multi-turn`, `Edge Cases`, `Memory Updater`

---

## Dependency Order

```
Phase 3 (guardrail cleanup)   — independent; do first (fixes action enum before new cases rely on it)
Phase 4 (run ID capture)      — independent; enables Phase 5
Phase 5 (llm_judge)           — depends on Phase 4 (needs run_id from TripState)
Phase 6 (eval expansion)      — depends on Phase 3 (MU cases assert "clarify", not "ignore"); Phase 4 run_id available in cases
```

---

## Architecture Reference

### Node Map (13-node main graph)

```
guardrail
    ↓ (conditional: proceed → chat_parser; clarify/confirm → END)
chat_parser → memory_agent → constraint_validator
                                     ↓ (conditional: is_ready → route_retriever; else → END)
                               route_retriever
                                     ↓ (conditional: unsupported → END; else Send fan-out)
                    ┌────────────────┴───────────────────┐
               hotel_retr  transport_retr  activity_retr  food_retr  waypoint_retr
                    └────────────────┬───────────────────┘
                               (fan-in, implicit)
                               planner_orchestrator
                              ↙                   ↘
                         explainer           memory_updater
                              ↘                   ↙
                                     END
```

### TripState Fields (35 total)

| Group | Fields |
|---|---|
| Input | `raw_chat`, `user_id` |
| Guardrail | `guardrail_result` |
| Memory | `user_profile`, `memory_context`, `memory_updates`, `visited_destinations` |
| Constraints | `extracted_constraints`, `missing_fields`, `assumptions` |
| Validation | `conflict_report`, `is_ready_to_plan` |
| Data Retrieval | `route_candidates`, `all_route_candidates`, `hotel_candidates`, `transport_candidates`, `activity_candidates`, `food_candidates`, `waypoint_candidates` |
| Planning | `itinerary_candidates`, `selected_itinerary`, `alternative_itineraries`, `validation_report`, `score_breakdown`, `timeline`, `map_points`, `cost_breakdown` |
| Explanation | `explanation` |
| Unsupported Route | `unsupported_route`, `suggested_routes` |
| Replanning | `delay_event`, `replanned_itinerary`, `replanning_explanation` |
| Observability | `langsmith_run_id` |

### Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Dedup location | `route_retriever_node` only | Planner never filters; `all_route_candidates` gives sub-nodes + planner fallback access to full data |
| Sub-node input | `all_route_candidates` | Hotel/activity/food data available for fallback routes when all filtered routes are visited (TC041c) |
| Memory scope | `user_id` | Individual user; persists across sessions |
| Parallelism | LangGraph `Send` API | Sub-retrievers are graph citizens; per-node trace spans; implicit fan-in |
| LLM fallback | `guardrail_node` defaults to `proceed` on error | Never blocks planning due to LLM connectivity issues |
| `"luxury"` hotel tier | Mapped to `"expedition"` in `_normalize()` | Prompt schema uses `budget/comfort/expedition`; LLM may return `luxury` |
| Guardrail action enum | `"proceed" \| "clarify" \| "confirm"` (no `"ignore"`) | Social/non-trip messages use `"clarify"` — simpler routing, same semantics |
| Unsupported route early-exit | `_route_after_retriever` returns `END` | Stops pipeline before domain retrievers + planner; avoids silent wrong-destination plan |
| Run ID capture | `RunIdCapture` callback on root `app.invoke()` | Only the root span ID is needed; child span IDs aren't required for eval feedback |
