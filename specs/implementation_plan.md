# Implementation Plan — Create Bucket 2.1 Spec for Augmented LLM Pipeline

Introduce a new spec file `specs/bucket_2.1_augmented_llm.md` that defines an alternative, simplified "Augmented LLM" implementation of the planning pipeline. This serves as a lightweight baseline comparison to the LangGraph-based agentic workflow.

---

## User Review Required

> [!IMPORTANT]
> **No changes to other specs**: We will achieve this without modifying any other bucket specs (Buckets 1, 3, 4, 5).
> **Integration switch**: We will update the environment variable configuration to support a `PIPELINE_TYPE` toggle (`agentic` vs `augmented`).
> **Dynamic Routing**: The existing `backend/agents/workflow.py` (or its spec) will dynamically route `run_workflow` and `run_replan_workflow` calls to `backend/agents_augmented/workflow.py` when `PIPELINE_TYPE=augmented`. This makes it 100% transparent and compatible with Bucket 3's backend API.

---

## Open Questions

None at this time. The strategy allows complete separation of concerns and lets you test both approaches seamlessly.

---

## Proposed Changes

### [NEW] [bucket_2.1_augmented_llm.md](file:///Users/devbox/Documents/Deep%20learning/Project/specs/bucket_2.1_augmented_llm.md)
Create a new self-contained spec document for the Augmented LLM pipeline following the canonical 7-section structure:
- **Section A**: Context on the baseline Augmented LLM approach.
- **Section B**: Frozen Interface Contracts (copies of `TripState` TypedDict, tool signatures, planner imports).
- **Section C**: Decisions & Defaults specific to the single-turn pipeline (e.g. combined parse & validate prompt, sequential orchestration).
- **Section D**: Build instructions for the `backend/agents_augmented/` package and the `.env` / `backend/agents/workflow.py` integration wrapper.
- **Section E**: File Manifest.
- **Section F**: Runnable verification test script `backend/tests/test_bucket_2_1.py`.
- **Section G**: Decisions Log template.

### [MODIFY] [.env.example](file:///Users/devbox/Documents/Deep%20learning/Project/.env.example)
- Add `PIPELINE_TYPE=agentic` as a configurable option to choose between the pipeline styles.

---

## Verification Plan

### Manual Verification
- Review the newly generated `specs/bucket_2.1_augmented_llm.md` to ensure it is self-contained and accurate.
- Verify that it maps to the exact same `TripState` TypedDict and respects the function signatures of tools and planner functions.
