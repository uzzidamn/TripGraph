#!/usr/bin/env python3
"""
Manual CLI test for Bucket 2.1 Tool-Augmented LLM.

Run from TripGraph project root:
    PYTHONPATH=. python backend/agents_augmented/run.py

Rate limiting is handled automatically inside LLMClient.invoke() via
LLM_RATE_LIMIT_RPM in .env — no manual sleeps needed here.
"""
import json

from dotenv import load_dotenv

load_dotenv()

from backend.agents_augmented.workflow import run_workflow, run_replan_workflow

SAMPLE_CHAT = [
    "Guys let's plan a trip from Gurugram",
    "Maybe Rishikesh? I want to do rafting",
    "Budget around 5000 per person",
    "Weekend trip, 4 of us",
]

SAMPLE_DELAY = {
    "delay_type": "departure_delay",
    "delay_minutes": 90,
}


def main() -> None:
    print("=" * 60)
    print("STEP 1: run_workflow()")
    print("=" * 60)
    state = run_workflow(SAMPLE_CHAT)
    print(json.dumps(state, indent=2, default=str))

    print("\n" + "=" * 60)
    print("STEP 2: run_replan_workflow()")
    print("=" * 60)
    updated = run_replan_workflow(state, SAMPLE_DELAY)
    print("replanned_itinerary:")
    print(json.dumps(updated.get("replanned_itinerary"), indent=2, default=str))
    print("\nreplanning_explanation:")
    print(updated.get("replanning_explanation"))


if __name__ == "__main__":
    main()
