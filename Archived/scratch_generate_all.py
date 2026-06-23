import json
from pathlib import Path
import sys

# Add current workspace directory to python path
sys.path.append("/Users/Ujjwal/Documents/Deep learning/Project")

# Load from Part 1
from scratch_generate import activities as act_part1

# Load from Part 2
from scratch_generate_part2 import munnar_activities, leh_activities, mumbai_activities

# Load from Part 3
from scratch_generate_part3 import manali_activities, bangalore_activities, kolkata_activities, shillong_activities

# Load Hotels
from scratch_generate_hotels import hotels

# Load Restaurants
from scratch_generate_restaurants import restaurants

# Load Routes & Transport
from scratch_generate_routes import routes, transports

# Paths
DATA_DIR = Path("/Users/Ujjwal/Documents/Deep learning/Project/backend/data")

# Compile all activities
all_activities = act_part1 + munnar_activities + leh_activities + mumbai_activities + manali_activities + bangalore_activities + kolkata_activities + shillong_activities

# Ensure metadata properties are present on static items
for act in all_activities:
    act.setdefault("verification_status", "llm_generated")
    act.setdefault("data_source", "llm_knowledge")
    act.setdefault("last_verified", "2026-06-22")

# Load all LLM-generated raw files from enriched_raw
ENRICHED_DIR = DATA_DIR / "enriched_raw"
llm_activities = []
llm_hotels = []
llm_restaurants = []

if ENRICHED_DIR.exists():
    for p in ENRICHED_DIR.glob("*_activities.json"):
        with open(p, encoding="utf-8") as f:
            llm_activities.extend(json.load(f))
    for p in ENRICHED_DIR.glob("*_hotels.json"):
        with open(p, encoding="utf-8") as f:
            llm_hotels.extend(json.load(f))
    for p in ENRICHED_DIR.glob("*_restaurants.json"):
        with open(p, encoding="utf-8") as f:
            llm_restaurants.extend(json.load(f))

print(f"Loaded from enriched_raw: {len(llm_activities)} activities, {len(llm_hotels)} hotels, {len(llm_restaurants)} restaurants.")

# Merge static and LLM datasets
compiled_activities = all_activities + llm_activities
compiled_hotels = hotels + llm_hotels
compiled_restaurants = restaurants + llm_restaurants

def save_json(filename, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {filename} with {len(data)} items.")

save_json("seed_activities.json", compiled_activities)
save_json("seed_hotels.json", compiled_hotels)
save_json("seed_restaurants.json", compiled_restaurants)
save_json("seed_routes.json", routes)
save_json("seed_transport.json", transports)
