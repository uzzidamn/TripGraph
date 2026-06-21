# KG Seed Data Generation Prompt

Paste this entire prompt into Claude / GPT-4 / Gemini to generate the seed data files.
Split into multiple sessions if needed (by region).

---

## PROMPT START

You are a senior travel data engineer building a curated Knowledge Graph for TripGraph AI, an Indian group travel planner. Generate comprehensive, realistic tourism seed data as JSON files covering **80+ top Indian tourist destinations**.

### DESTINATIONS TO COVER (grouped by region)

**North India (25):**
Jaipur, Udaipur, Jodhpur, Jaisalmer, Pushkar, Mount Abu, Agra, Varanasi, Lucknow, Allahabad (Prayagraj), Amritsar, Chandigarh, Shimla, Manali, Dharamshala/McLeodganj, Rishikesh, Haridwar, Mussoorie, Nainital, Dehradun, Leh-Ladakh, Srinagar, Gulmarg, Kasol/Parvati Valley, Jim Corbett

**South India (20):**
Bangalore, Mysore, Coorg (Madikeri), Hampi, Gokarna, Ooty, Kodaikanal, Munnar, Alleppey (Alappuzha), Kochi, Thiruvananthapuram, Pondicherry, Mahabalipuram, Chennai, Madurai, Rameshwaram, Wayanad, Thekkady, Varkala, Kumarakom

**West India (15):**
Mumbai, Pune, Goa (North + South), Lonavala, Mahabaleshwar, Alibaug, Diu, Dwarka, Somnath, Kutch (Rann), Aurangabad (Ajanta-Ellora), Nashik, Shirdi, Lavasa, Tarkarli

**East India (10):**
Kolkata, Darjeeling, Gangtok, Puri, Konark, Bodh Gaya, Sundarbans, Digha, Kalimpong, Pelling

**Northeast India (8):**
Shillong, Cherrapunji, Kaziranga, Tawang, Majuli, Ziro Valley, Imphal, Kohima

**Central India (5):**
Bhopal, Khajuraho, Orchha, Pachmarhi, Kanha National Park

### OUTPUT FORMAT

Generate **6 separate JSON files**. Each must be a valid JSON array. Output them one at a time, clearly labeled.

---

### FILE 1: `seed_cities.json`

One entry per destination + major origin cities (Delhi, Mumbai, Bangalore, Kolkata, Hyderabad, Chennai, Pune, Ahmedabad, Chandigarh, Gurugram, Kochi).

```json
{
  "name": "Jaipur",
  "type": "mountains" | "beach" | "heritage" | "spiritual" | "hill_station" | "wildlife" | "adventure" | "urban" | "backwater" | "desert" | "origin",
  "lat": 26.9124,
  "lng": 75.7873,
  "state": "Rajasthan",
  "region": "north",
  "description": "1-2 sentence summary of why people visit",
  "best_months": ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
  "tags": ["heritage", "food", "culture", "family", "shopping"],
  "nearest_airport": "Jaipur (JAI)",
  "nearest_railway": "Jaipur Junction (JP)",
  "confidence_pct": 95,
  "verification_status": "llm_generated",
  "data_source": "llm_knowledge",
  "last_verified": "2026-06-22"
}
```

---

### FILE 2: `seed_activities.json`

**15-30 activities per destination** (more for major destinations like Goa, Jaipur, Varanasi). Include a mix of:
- Must-visit landmarks/forts/temples (cultural)
- Adventure activities (rafting, trekking, paragliding)
- Nature/scenic spots (viewpoints, gardens, lakes)
- Markets/shopping
- Unique local experiences (cooking classes, boat rides, village walks)
- Nightlife/entertainment (where relevant)

```json
{
  "activity_id": "amber_fort_jaipur_01",
  "destination": "Jaipur",
  "name": "Amber Fort Tour",
  "category": "cultural" | "adventure" | "nature" | "spiritual" | "food" | "shopping" | "nightlife" | "wellness" | "wildlife" | "water_sport" | "experience",
  "duration_minutes": 150,
  "cost_per_person": 550,
  "available_slots": ["08:00", "09:00", "10:00", "14:00", "15:00"],
  "risk_level": "low" | "medium" | "high",
  "tags": ["heritage", "fort", "history", "photography", "family"],
  "lat": 26.9855,
  "lng": 75.8513,
  "fatigue_score_base": 4,
  "morale_score_base": 8,
  "best_time_of_day": "morning" | "afternoon" | "evening" | "any",
  "best_season": ["Oct-Mar"],
  "accessibility": "easy" | "moderate" | "difficult",
  "editorial_summary": "One sentence on what makes this special — written like a travel writer, not a brochure",
  "opening_hours": ["Monday: 08:00–17:30", "Tuesday: 08:00–17:30", ...],
  "skip_if": "Rain or extreme heat — fort steps are slippery",
  "insider_tip": "Go before 9 AM to avoid tour bus crowds. The mirror palace is best with morning light.",
  "confidence_pct": 92,
  "verification_status": "llm_generated",
  "data_source": "llm_knowledge",
  "last_verified": "2026-06-22"
}
```

**IMPORTANT RULES for activities:**
- `lat`/`lng` MUST be realistic coordinates for the actual place (not the city center). Use your best knowledge. If unsure, use the general area and set `confidence_pct` to 60-70.
- `cost_per_person` in INR. Use 0 for free public places. Include entry fees, guide costs, equipment rental where applicable.
- `duration_minutes` should be realistic visit time, not just the "official" time.
- `fatigue_score_base` (0-10): 0 = sitting at a cafe, 10 = full-day Himalayan trek.
- `morale_score_base` (0-10): how much joy/satisfaction this gives the average tourist.
- `editorial_summary`: Write this like a knowledgeable friend, not a Wikipedia article. "The sunrise view from Tiger Hill is genuinely life-changing — arrive by 4:30 AM for the Kanchenjunga reveal."
- `insider_tip`: Practical advice a local would give. Parking tips, best photo spots, what to skip, cash-only warnings.
- `confidence_pct`: 90-99 for famous landmarks you're certain about. 70-85 for costs/hours you're approximating. 50-69 for lesser-known spots where coords might be off.
- `activity_id` format: `snake_case_name_destination_NN` (e.g., `hawa_mahal_jaipur_01`)

---

### FILE 3: `seed_hotels.json`

**5-8 hotels per destination** spanning budget (₹800-2500), mid-range (₹2500-6000), comfort (₹6000-12000), and luxury (₹12000+).

```json
{
  "hotel_id": "jaipur_budget_01",
  "destination": "Jaipur",
  "name": "Zostel Jaipur",
  "tier": "budget" | "mid" | "comfort" | "luxury",
  "price_per_night": 1200,
  "rooms_required": 2,
  "checkin_time": "14:00",
  "checkout_time": "11:00",
  "comfort_score": 5,
  "lat": 26.9239,
  "lng": 75.8267,
  "amenities": ["wifi", "breakfast", "parking", "pool", "spa", "restaurant", "gym", "room_service", "ac", "bar"],
  "tags": ["backpacker", "central", "social"],
  "editorial_summary": "Clean, social hostel 5 min walk from Hawa Mahal. Rooftop cafe is the real draw.",
  "price_confidence": "high" | "medium" | "low",
  "confidence_pct": 82,
  "verification_status": "llm_generated",
  "data_source": "llm_knowledge",
  "last_verified": "2026-06-22"
}
```

**Rules:**
- Use real or realistic hotel names (Zostel, OYO Townhouse, Taj, ITC, Treebo, FabHotel, RAAS, etc.)
- `price_per_night` is per room in INR (2024-25 era pricing)
- `price_confidence`: "high" for well-known chains, "low" for boutique/seasonal
- `rooms_required`: default 2 (for a group of 4)

---

### FILE 4: `seed_restaurants.json`

**5-8 restaurants per destination** — mix of iconic eateries, local street food, cafes, and fine dining.

```json
{
  "restaurant_id": "lmb_jaipur_01",
  "destination": "Jaipur",
  "route_id": null,
  "name": "LMB (Laxmi Misthan Bhandar)",
  "cuisine": "Rajasthani",
  "meal_types": ["breakfast", "lunch", "dinner"],
  "avg_cost_per_person": 500,
  "avg_duration_minutes": 60,
  "tags": ["vegetarian", "heritage", "famous", "must_visit"],
  "lat": 26.9234,
  "lng": 75.826,
  "signature_dish": "Dal Baati Churma, Ghevar",
  "insider_tip": "Skip the ground floor — go upstairs for the AC section. Try the paneer ghevar.",
  "confidence_pct": 90,
  "verification_status": "llm_generated",
  "data_source": "llm_knowledge",
  "last_verified": "2026-06-22"
}
```

**Rules:**
- Use real restaurant names when confident; use realistic descriptive names when unsure
- `route_id`: set this for highway dhaba stops (e.g., Murthal dhabas on Delhi-Chandigarh route), null for destination restaurants
- Include street food stalls as restaurants (e.g., "Chowpatty Beach Street Food" in Mumbai)

---

### FILE 5: `seed_routes.json`

Routes from **every major origin city** to **every reachable destination**. An origin city can reach a destination if:
- Driving distance < 800 km (road trip viable), OR
- A direct/1-stop flight exists (any distance)

Major origin cities: Delhi/Gurugram, Mumbai, Bangalore, Kolkata, Hyderabad, Chennai, Pune, Ahmedabad, Chandigarh, Kochi.

```json
{
  "route_id": "gurugram_jaipur_2d1n",
  "origin": "Gurugram",
  "destination": "Jaipur",
  "distance_km": 240,
  "base_drive_minutes": 300,
  "risk_level": "low" | "medium" | "high",
  "scenic_score": 5,
  "highway": "NH48",
  "recommended_for": ["heritage", "food", "family", "weekend", "culture"],
  "flight_available": true,
  "flight_duration_minutes": 60,
  "train_available": true,
  "train_duration_minutes": 270,
  "confidence_pct": 95,
  "verification_status": "llm_generated",
  "data_source": "llm_knowledge",
  "last_verified": "2026-06-22"
}
```

**Rules:**
- `route_id` format: `origin_destination_XdYn` (e.g., `delhi_goa_3d2n`)
- `distance_km` and `base_drive_minutes`: driving distance/time. Set to 0 for flight-only routes (distance > 800 km).
- `risk_level`: "high" for mountain roads (Leh, Spiti, NE India), "medium" for long drives, "low" for expressways
- Generate at least 200-300 routes to ensure broad connectivity

---

### FILE 6: `seed_transport.json`

**2-4 transport options per route** (budget/comfort/luxury ground + flight where applicable).

```json
{
  "transport_id": "shared_cab_jaipur_budget",
  "route_id": "gurugram_jaipur_2d1n",
  "mode": "self_drive" | "cab_with_driver" | "shared_cab" | "bus" | "train" | "flight",
  "tier": "budget" | "comfort" | "luxury",
  "cost_total": 2800,
  "capacity": 4,
  "base_duration_minutes": 320,
  "night_driving_allowed": false,
  "comfort_score": 4,
  "fatigue_score": 6,
  "tags": ["shared", "economy"],
  "confidence_pct": 80,
  "verification_status": "llm_generated",
  "data_source": "llm_knowledge",
  "last_verified": "2026-06-22"
}
```

---

### GENERATION INSTRUCTIONS

1. **Output one file at a time.** Start with `seed_cities.json`, then `seed_activities.json` (this will be the largest), etc.
2. **For `seed_activities.json`**: Generate AT LEAST 20 activities for Goa, Jaipur, Varanasi, Mumbai, Manali, Leh, and Kerala (Munnar/Alleppey). Generate 12-18 for other destinations.
3. **Coordinates must be plausible.** Don't use city center for everything — spread activities across their real locations. Amber Fort is NOT at the same coordinates as Hawa Mahal.
4. **Costs in 2024-25 INR.** Entry fees, guide charges, equipment rentals — be realistic.
5. **`confidence_pct` must be honest.** Don't put 95 on everything. Costs and hours are inherently less certain (70-85). Well-known landmarks get 90+. Lesser-known spots get 60-75.
6. **No duplicate `activity_id` or `hotel_id`.** Each must be globally unique.
7. **Target total rows:** ~4,000-5,000 activities, ~500-600 hotels, ~500+ restaurants, ~300+ routes.
8. **Write `editorial_summary` and `insider_tip` like a real travel writer**, not generic marketing copy. These fields are what make the KG better than an API.

### QUALITY BENCHMARKS

Ask yourself for each row:
- Would a territory manager approve this data?
- Is the lat/lng within 500m of the real place?
- Is the cost within 30% of reality?
- Would the insider_tip actually help someone?

If no → lower `confidence_pct` and flag it.

**START WITH `seed_cities.json` (the master destination list), then proceed file by file.**