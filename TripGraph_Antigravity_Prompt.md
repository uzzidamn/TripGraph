# TripGraph AI — Antigravity IDE Prompt
### Execution Pivot: Distributed Compute via Spec-Driven Parallel Build

---

## 1. Context & What Has Been Done

You are working on **TripGraph AI** — a GenAI-agentic group travel planner that converts messy WhatsApp-style group chat into structured, constraint-aware itineraries. It is a **planning engine with a chat interface**, not a chatbot.

The full specification exists in this repository under `specs/`. The following documents are your single source of truth:

- `specs/MASTER_SPEC.md` — Full architecture, Neo4j schema, agent design, API contracts, data models
- `specs/implementation_plan.md` — Decisions finalized, bucket structure, interface contracts
- `specs/project_context.md` — Project summary and current status
- `specs/bucket_1_dummy_data.md` — Spec for Bucket 1 (Dummy Data & Seed)
- `specs/bucket_2_agentic_pipeline.md` — Spec for Bucket 2 (LangGraph Agents)
- `specs/bucket_3_backend_api.md` — Spec for Bucket 3 (FastAPI Backend)
- `specs/bucket_4_frontend_ui.md` — Spec for Bucket 4 (React Frontend)
- `specs/bucket_5_neo4j_planner.md` — Spec for Bucket 5 (Neo4j + Planning Engine)

**Current state:** Bucket 5 (Neo4j Knowledge Graph + Graph Planning Engine) has been developed. The `backend/knowledge_graph/`, `backend/tools/`, and `backend/planner/` directories have been implemented. All other buckets are **spec-only — no implementation code exists yet**.

---

## 2. Strategic Pivot — What Is Changing

The project is now being executed **solo with distributed compute**. There are no active human collaborators making decisions. Instead, each bucket spec file will be fed independently into a separate Claude Pro session (running in parallel, likely on a teammate's machine). Those sessions will generate code and push to the GitHub repository.

**This changes the execution model entirely:**

| Old Model | New Model |
|---|---|
| Teammates read specs and ask clarifying questions | LLM sessions receive a spec and build without asking any questions |
| Coordination happens in real-time conversation | Coordination happens through frozen interface contracts embedded in spec files |
| Waiting on others for integration | Async — each session builds to frozen contracts and pushes to GitHub |
| Human-level UI effort | LLM-generated — UI should be pushed to its maximum quality ceiling |

The goal is to use their Claude Pro compute and AI credits to produce high-quality, heavy, production-grade code in a single pass — code that you (the mainframe) can then integrate and refine.

---

## 3. Your Task — Rewrite All Bucket Specs for LLM-Ready Execution

You must rewrite **Bucket 1, Bucket 2, Bucket 3, and Bucket 4** spec files so that any Claude instance, given only that spec file, can build the entire bucket **without asking a single question, making any assumption, or waiting on any external input.**

Bucket 5 is yours (mainframe) and does not need to be rewritten unless integration requires it.

### The Core Rule

> **Every spec must be 100% self-contained. No question should be answerable by "check with another bucket" or "assume reasonable defaults." Every default is written explicitly in the spec.**

---

## 4. Mandatory Sections in Every Rewritten Spec

Each rewritten bucket spec must contain the following sections **in this order**:

---

### Section A — Project Context (Brief)
A 10-line summary of what TripGraph AI is and what this bucket's role is within the whole. This is for the LLM's orientation only.

---

### Section B — 🔒 Frozen Interface Contracts

This is the most critical section. It must contain, **verbatim and copy-pasted from the Master Spec**, every piece of external data this bucket depends on or produces. The LLM running this spec must never derive these values — they are frozen.

For each bucket:

**Bucket 1 must include:**
- Complete Neo4j node schema: every node label with every property name and its Python type (e.g., `price_per_night: float`, NOT just "price"). This comes from `MASTER_SPEC.md` Section 6.2.
- All relationship types and their properties.
- The schema constraints and index creation Cypher — copy exactly from `MASTER_SPEC.md` Section 6.5.
- One complete JSON example per seed file (cities, routes, hotels, activities, restaurants, transport, waypoints) showing every field with a realistic value. These examples are the ground truth that the seeding LLM will follow.

**Bucket 2 must include:**
- The complete `TripState` TypedDict — copy exactly from `MASTER_SPEC.md` Section 7.4.
- All 6 tool function signatures with full parameter types AND their exact return TypedDict shapes. Each return type must be a fully-specified `TypedDict` (e.g., `HotelDict`, `RouteDict`), not just `list[dict]`.
- All 5 planner function signatures with full parameter and return types.
- Exact import paths: `from backend.tools.route_tool import get_routes`, etc.
- Mock data blocks: for each tool function, a hardcoded Python dict that matches the return TypedDict exactly. These are used while Bucket 5 integration is pending.

**Bucket 3 must include:**
- Complete `TripState` TypedDict — copy exactly.
- Exact import path: `from backend.agents.workflow import run_workflow, run_replan_workflow`.
- All Pydantic request and response model definitions written out in full Python code — not described, fully written. Field names, types, Optional/required, default values, and example values via `Field(example=...)`.
- Full JSON response examples for all 3 endpoints, matching Pydantic model field names exactly.

**Bucket 4 must include:**
- All 3 endpoint URL paths, HTTP methods, and full JSON request/response shapes — written as TypeScript interfaces or as commented mock objects the frontend can import.
- A `MOCK_DATA.js` block (ready to import) that contains realistic hardcoded responses for all 3 endpoints, so the frontend can build and run without the backend being live.
- The exact field names the frontend must read from API responses (e.g., `response.recommended_itinerary.timeline[0].event_name`).
- Leaflet.js map coordinate format: `{ lat: float, lng: float, label: string, type: 'origin'|'waypoint'|'hotel'|'activity'|'destination' }`.

---

### Section C — Decisions & Defaults (Pre-Made)

List every decision the LLM would normally ask about. Make the decision explicitly. No decision should be left open.

Examples of what to pre-decide:
- What port does the FastAPI server run on? → `8000`
- What is the CORS origin allowed? → `http://localhost:5173`
- What happens if Neo4j is unreachable on startup? → Log error, raise RuntimeError, do not silently continue
- What font does the UI use? → Provide the CDN link
- What color scheme? → Specify hex values or the design tokens
- What does an empty `must_include` array mean? → No activity constraints; accept all activities
- What is the default group size if not specified? → `4`

There should be a minimum of 15 pre-made decisions per bucket.

---

### Section D — Step-by-Step Build Instructions

Ordered, numbered steps the LLM must follow to build the bucket. Each step has:
- The file to create or modify
- The exact imports to use
- The exact function/class signatures to implement
- Pseudocode or logic description for non-trivial functions
- Integration points explicitly called out (e.g., "This function is called by Bucket 2's `data_retriever.py` — the return shape must match `HotelDict` exactly")

For **Bucket 4 (Frontend)** specifically:
- The UI quality bar is **maximum**. This is not a prototype. It must be a polished, modern, dark-themed SPA with smooth transitions, micro-interactions, and production-grade visual design.
- Specify: Tailwind CSS with custom config, Framer Motion for animations, Lucide React for icons, shadcn/ui components as a base, a specific Google Font, specific color palette hex values.
- Each component must have its full prop interface defined.
- Include responsive breakpoints explicitly (mobile: 375px, tablet: 768px, desktop: 1280px).
- Include a section titled **"UI Excellence Requirements"** — 10+ specific UI/UX behaviors that must be implemented (e.g., skeleton loaders on every data fetch, animated number counters in cost breakdown, smooth polyline drawing on Leaflet map, toast notifications for errors, hover card effects, timeline item entrance animations).

---

### Section E — File Manifest

A complete list of every file the LLM must produce for this bucket. Format:

```
backend/agents/workflow.py          — LangGraph StateGraph definition, exports run_workflow()
backend/agents/state.py             — TripState TypedDict
backend/agents/llm_client.py        — LLM factory, reads LLM_PROVIDER from env
...
```

No file should be ambiguous. If a file is shared with another bucket (e.g., `seed.py` is owned by Bucket 1 but calls Bucket 5's `connection.py`), state the exact import path.

---

### Section F — Integration Verification Checklist

A checklist the LLM must run mentally before finishing, confirming:
- [ ] All frozen field names match exactly what's in the contract (no renaming)
- [ ] No `TODO` or `pass` in any function that is part of an interface contract
- [ ] Import paths are correct relative to the `backend/` or `frontend/src/` root
- [ ] Mock data is present and operational for all external dependencies
- [ ] The bucket can run independently (e.g., `uvicorn main:app` starts without the other buckets being present)

---

### Section G — 📋 Assumptions & Decisions Log (Output File)

**This section defines a file the LLM must CREATE and COMMIT as part of its bucket output.**

At the end of building this bucket, the LLM must produce a file:

```
specs/logs/bucket_N_decisions.md
```

This file must be structured as follows:

```markdown
# Bucket N — Decisions & Assumptions Log
Generated by: Claude [model] on [date]

## Pre-Specified Decisions Applied
[List every decision from Section C that was applied, with the actual value used]

## Unspecified Decisions Made During Build
[List every decision the spec did not cover, what the LLM decided, and why]
Example:
- DECISION: Used `asyncio.sleep(0)` between candidate generation iterations to yield control
  REASON: Candidate generation is CPU-bound; yielding prevents event loop blocking
  IMPACT: Bucket 2 (agents) will see slightly higher latency per planning call (~5ms)

## Deviations from Spec
[Any case where the spec said X but the LLM built Y, with justification]
Example:
- SPEC SAID: Use List[dict] for tool returns
  BUILT: TypedDict subclasses (HotelDict, RouteDict, etc.)
  REASON: Type safety for agents; no functional change for callers

## External Assumptions
[Anything assumed about the environment, other buckets, or runtime]
Example:
- ASSUMED: Neo4j is running at bolt://localhost:7687 when Bucket 2 is tested
- ASSUMED: Bucket 5's tool functions are importable before integration testing

## User Changes (If Any)
[This section is filled by the human user if they modify the generated code before pushing]
Example:
- CHANGED: MapView default zoom from 8 to 10
  REASON: 10 gives better detail for the 3 routes in scope
```

This log file is the primary communication channel between the distributed LLM sessions and the mainframe (you). You will read these logs from the GitHub repository to understand what each session built, what it assumed, and what changed.

---

## 5. GitHub Push Protocol

Each rewritten spec must end with a **Git Commit Protocol** section telling the LLM exactly what to commit when done:

```
Git Commit Protocol:
1. Stage all files listed in the File Manifest (Section E)
2. Stage specs/logs/bucket_N_decisions.md
3. Commit message format: "Bucket N: [one-line description] — [date]"
   Example: "Bucket 4: React frontend with full UI, mock API — 2026-06-13"
4. Branch: bucket-N/implementation
5. Push to origin
6. Do NOT merge to main — push to the feature branch only
```

---

## 6. Quality Bar — Non-Negotiable

These apply to all rewritten specs:

**Backend (Buckets 1, 2, 3):**
- All Python code must be typed (no bare `dict`, use TypedDict or Pydantic)
- All functions must have docstrings with parameter and return descriptions
- Error handling: every external call (Neo4j, LLM API) must have try/except with meaningful log output
- `requirements.txt` must be included with pinned versions

**Frontend (Bucket 4):**
- The UI is the face of this project. It must be excellent.
- Dark theme by default. Modern, clean, high contrast.
- Every loading state has a skeleton. No blank screens.
- Every error state has a human-readable message with a retry action.
- The Leaflet map must animate the route polyline drawing on load.
- The timeline must have smooth entrance animations per item.
- The cost breakdown must animate numbers counting up.
- Mobile-responsive. All 8 components work at 375px width.
- No `console.log` left in production code.

**All Buckets:**
- No hardcoded secrets. All config from `.env`.
- The bucket must be runnable in isolation using mock/stub data before integration.
- The decisions log (`specs/logs/bucket_N_decisions.md`) is mandatory. A bucket without this file is incomplete.

---

## 7. Do This Now

Rewrite the following specs in order:

1. `specs/bucket_1_dummy_data.md` — incorporating all Frozen Contracts for Neo4j schema and seed JSON examples
2. `specs/bucket_2_agentic_pipeline.md` — incorporating all TypedDict return shapes and mock data blocks
3. `specs/bucket_3_backend_api.md` — incorporating full Pydantic models and import paths
4. `specs/bucket_4_frontend_ui.md` — incorporating mock API data, full component prop interfaces, and UI excellence requirements

For each file:
- Read the existing spec first
- Read the relevant sections of `MASTER_SPEC.md` and `implementation_plan.md`
- Produce the rewritten spec following the 7-section structure above
- Save it back to the same path (overwrite the existing spec)

Do not ask for clarification. All information needed is in the spec files already present in this repository. Any gap you encounter should be resolved by making a reasonable decision and logging it in Section G.

---

*This prompt was written for Antigravity IDE — Claude model. The mainframe (Bucket 5 + integration) is operated separately. All outputs from this session will be reviewed by the mainframe before merging to `main`.*
