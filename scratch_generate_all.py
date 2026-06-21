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

# Compile all activities
all_activities = act_part1 + munnar_activities + leh_activities + mumbai_activities + manali_activities + bangalore_activities + kolkata_activities + shillong_activities

# Ensure metadata properties are present on all compiled items
for act in all_activities:
    act.setdefault("verification_status", "llm_generated")
    act.setdefault("data_source", "llm_knowledge")
    act.setdefault("last_verified", "2026-06-22")

# Paths
DATA_DIR = Path("/Users/Ujjwal/Documents/Deep learning/Project/backend/data")

def save_json(filename, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {filename} with {len(data)} items.")

save_json("seed_activities.json", all_activities)
save_json("seed_hotels.json", hotels)
save_json("seed_restaurants.json", restaurants)
save_json("seed_routes.json", routes)
save_json("seed_transport.json", transports)
