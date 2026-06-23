import os
import json
import time
import sys
from pathlib import Path
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# Ensure project root is in path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from backend.agents.llm_client import get_llm

# Target destinations to expand
DESTINATIONS = [
    "Udaipur", "Agra", "Amritsar", "Srinagar", "Dharamshala", 
    "Coorg", "Hampi", "Alleppey", "Gokarna", "Pondicherry", 
    "Ooty", "Pune", "Lonavala", "Mahabaleshwar", "Darjeeling", 
    "Gangtok", "Cherrapunji", "Kaziranga", "Khajuraho"
]

OUT_DIR = ROOT / "backend" / "data" / "enriched_raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Pydantic Schemas matching existing validators
# ---------------------------------------------------------------------------

class ActivityModel(BaseModel):
    activity_id: str = Field(description="Unique snake_case ID, format: name_destination_nn (e.g. city_palace_udaipur_01)")
    destination: str
    name: str
    category: Literal["cultural", "adventure", "nature", "spiritual", "food", "shopping", "nightlife", "wellness", "wildlife", "water_sport", "experience"]
    duration_minutes: int = Field(description="Realistic duration of visit in minutes")
    cost_per_person: int = Field(description="Cost in INR (0 for free public places)")
    available_slots: List[str] = Field(description="Standard starting slots, e.g. ['09:00', '14:00']")
    risk_level: Literal["low", "medium", "high"]
    tags: List[str] = Field(description="Lowercase, no-space tags")
    lat: float = Field(description="Realistic latitude within 500m of the actual location")
    lng: float = Field(description="Realistic longitude within 500m of the actual location")
    fatigue_score_base: int = Field(description="Fatigue rating from 0 (resting) to 10 (extreme physical)")
    morale_score_base: int = Field(description="Joy/morale rating from 0 to 10")
    best_time_of_day: Literal["morning", "afternoon", "evening", "any"]
    best_season: List[str] = Field(description="e.g. ['Oct-Mar'] or ['Jul-Sep']")
    accessibility: Literal["easy", "moderate", "difficult"]
    editorial_summary: str = Field(description="One-sentence description written in an inspiring travel writer style")
    opening_hours: List[str] = Field(description="e.g. ['Monday: 09:00-18:00', 'Tuesday: 09:00-18:00']")
    skip_if: str = Field(description="Condition under which to skip, e.g. 'Heavy rain or fog'")
    insider_tip: str = Field(description="Local expert advice, parking, photo spots, or best times")
    confidence_pct: int = Field(description="Confidence rating of coords/pricing (70-99)")
    verification_status: str = "verified"
    data_source: str = "llm_knowledge"
    last_verified: str = "2026-06-22"

class HotelModel(BaseModel):
    hotel_id: str = Field(description="Unique ID, format: destination_tier_nn (e.g. udaipur_comfort_01)")
    destination: str
    name: str
    tier: Literal["budget", "comfort", "expedition"] = Field(description="Must map to one of: budget, comfort, expedition")
    price_per_night: int = Field(description="Room rate per night in INR")
    rooms_required: int = 2
    checkin_time: str = "14:00"
    checkout_time: str = "11:00"
    comfort_score: int = Field(description="Rating from 1 to 10")
    lat: float
    lng: float
    amenities: List[str] = Field(description="List from: wifi, breakfast, parking, pool, spa, restaurant, gym, room_service, ac, bar")
    tags: List[str]
    editorial_summary: str
    price_confidence: Literal["high", "medium", "low"]
    confidence_pct: int
    verification_status: str = "verified"
    data_source: str = "llm_knowledge"
    last_verified: str = "2026-06-22"

class RestaurantModel(BaseModel):
    restaurant_id: str = Field(description="Unique ID, format: name_destination_nn (e.g. ambrai_udaipur_01)")
    destination: str
    route_id: Optional[str] = None
    name: str
    cuisine: str
    meal_types: List[str] = Field(description="List containing: breakfast, lunch, dinner")
    avg_cost_per_person: int = Field(description="INR average cost")
    avg_duration_minutes: int = 60
    tags: List[str]
    lat: float
    lng: float
    signature_dish: str
    insider_tip: str
    confidence_pct: int
    verification_status: str = "verified"
    data_source: str = "llm_knowledge"
    last_verified: str = "2026-06-22"

# Containers for LLM Structured Output
class ActivityList(BaseModel):
    items: List[ActivityModel]

class HotelList(BaseModel):
    items: List[HotelModel]

class RestaurantList(BaseModel):
    items: List[RestaurantModel]

# ---------------------------------------------------------------------------
# Generator Core Loop
# ---------------------------------------------------------------------------

def main():
    llm = get_llm()
    
    # Bind structured outputs
    activities_llm = llm.with_structured_output(ActivityList)
    hotels_llm = llm.with_structured_output(HotelList)
    restaurants_llm = llm.with_structured_output(RestaurantList)

    for city in DESTINATIONS:
        print(f"\n========================================\nProcessing City: {city}\n========================================")
        
        # 1. Activities
        act_file = OUT_DIR / f"{city.lower().replace(' ', '_')}_activities.json"
        if not act_file.exists():
            print(f"Generating 20 activities for {city}...")
            prompt = f"""
            You are a professional travel writer and data engineer.
            Generate exactly 20 diverse, highly-rated activities for the tourist destination '{city}', India.
            Ensure activities include:
            - Must-visit heritage sites and museums (cultural)
            - Trekking, boating, safari, or adventure sports if applicable (adventure/wildlife/water_sport)
            - Scenic viewpoints, lakes, gardens (nature)
            - Historic local markets/shopping spots (shopping)
            - Iconic eateries or street food experiences (food)
            - Authentic local workshops or yoga/wellness classes (experience/wellness)
            
            Strictly locate them at their actual latitude/longitude (lat/lng) coordinates. 
            Write short, evocative editorial summaries and highly practical insider tips.
            Generate unique `activity_id` values starting with the activity name, ending with _01, _02, etc.
            """
            try:
                result = activities_llm.invoke(prompt)
                with open(act_file, "w", encoding="utf-8") as f:
                    json.dump([item.dict() for item in result.items], f, indent=2)
                print(f"Saved {len(result.items)} activities for {city} to {act_file.name}")
                time.sleep(6) # Rate limit cooling
            except Exception as e:
                print(f"ERROR generating activities for {city}: {e}")
        else:
            print(f"Activities for {city} already exist. Skipping.")

        # 2. Hotels
        hotel_file = OUT_DIR / f"{city.lower().replace(' ', '_')}_hotels.json"
        if not hotel_file.exists():
            print(f"Generating 8 hotels for {city}...")
            prompt = f"""
            Generate exactly 8 realistic hotels for the tourist destination '{city}', India.
            Cover a range of budgets (budget, comfort, expedition):
            - at least 2 budget hostels or homestays (₹800 - ₹2000 per night)
            - at least 3 mid-range and comfort hotels/resorts (₹2000 - ₹8000 per night)
            - at least 3 premium/luxury hotels/heritage stays (₹8000+ per night), ensuring their tier is set to 'expedition'
            
            Specify realistic names, room pricing in INR, coordinates, comfort scores (1 to 10), and amenities.
            """
            try:
                result = hotels_llm.invoke(prompt)
                with open(hotel_file, "w", encoding="utf-8") as f:
                    json.dump([item.dict() for item in result.items], f, indent=2)
                print(f"Saved {len(result.items)} hotels for {city} to {hotel_file.name}")
                time.sleep(6) # Rate limit cooling
            except Exception as e:
                print(f"ERROR generating hotels for {city}: {e}")
        else:
            print(f"Hotels for {city} already exist. Skipping.")

        # 3. Restaurants
        rest_file = OUT_DIR / f"{city.lower().replace(' ', '_')}_restaurants.json"
        if not rest_file.exists():
            print(f"Generating 8 restaurants for {city}...")
            prompt = f"""
            Generate exactly 8 realistic, well-known, or highly typical restaurants/cafes/street food spots in and around '{city}', India.
            Include:
            - Famous local traditional eateries (e.g. serving regional thali or signature local dishes)
            - Popular cafes with views or good breakfast setups
            - Famous street food stalls
            - Fine dining or romantic spots
            
            Specify coordinates, cuisine, average cost per person, signature dish, and local insider tips.
            """
            try:
                result = restaurants_llm.invoke(prompt)
                with open(rest_file, "w", encoding="utf-8") as f:
                    json.dump([item.dict() for item in result.items], f, indent=2)
                print(f"Saved {len(result.items)} restaurants for {city} to {rest_file.name}")
                time.sleep(6) # Rate limit cooling
            except Exception as e:
                print(f"ERROR generating restaurants for {city}: {e}")
        else:
            print(f"Restaurants for {city} already exist. Skipping.")

    print("\n🎉 Generative Seeding Run Completed!")

if __name__ == "__main__":
    main()
