import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents_augmented.workflow import run_workflow

SAMPLE_CHAT = [
    "Guys let's plan a trip from Gurugram",
    "Maybe Rishikesh? I want to do rafting",
    "Budget around 5000 per person",
    "Weekend trip, 4 of us",
]

print("Running workflow...")
result = run_workflow(SAMPLE_CHAT)
print("\n--- Selected Itinerary ---")
print(result.get("selected_itinerary"))
print("\n--- Timeline ---")
print(result.get("timeline"))
print("\n--- Validation Report ---")
print(result.get("validation_report"))
