# Hotels seed data list
hotels = []

# Helper to generate basic hotel template
def add_hotel(destination, name, tier, price, comfort, lat, lng, amenities, tags, summary, confidence=85):
    h_id = f"{destination.lower().replace(' ', '_')}_{tier}_{len([h for h in hotels if h['destination'] == destination]) + 1:02d}"
    hotels.append({
        "hotel_id": h_id,
        "destination": destination,
        "name": name,
        "tier": tier,
        "price_per_night": price,
        "rooms_required": 2,
        "checkin_time": "14:00" if tier in ["comfort", "expedition"] else "12:00",
        "checkout_time": "11:00" if tier in ["comfort", "expedition"] else "10:00",
        "comfort_score": comfort,
        "lat": lat,
        "lng": lng,
        "amenities": amenities,
        "tags": tags,
        "editorial_summary": summary,
        "price_confidence": "high" if "Zostel" in name or "Taj" in name or "ITC" in name else "medium",
        "confidence_pct": confidence,
        "verification_status": "llm_generated",
        "data_source": "llm_knowledge",
        "last_verified": "2026-06-22"
    })

# --- GOA ---
add_hotel("Goa", "Zostel Goa (Morjim)", "budget", 1500, 5, 15.6322, 73.7150, ["wifi", "common_room", "ac", "parking"], ["backpacker", "beach_near", "social"], "Vibrant social hostel just a short walk from Morjim beach. The outdoor garden cafe is perfect for meeting other travelers.")
add_hotel("Goa", "OYO Townhouse Calangute", "budget", 3200, 6, 15.5411, 73.7630, ["wifi", "pool", "ac", "room_service"], ["family", "central", "value"], "Reliable modern rooms near Calangute beach, featuring an outdoor pool and in-house dining options.")
add_hotel("Goa", "Lemon Tree Amarante Beach Resort", "comfort", 7500, 8, 15.5180, 73.7680, ["wifi", "pool", "spa", "restaurant", "bar", "gym"], ["beachside", "resort", "heritage"], "Spanish-style resort in Candolim, offering lush gardens, pool, and close proximity to the beach.")
add_hotel("Goa", "Taj Exotica Resort & Spa (Benaulim)", "expedition", 22000, 10, 15.2490, 73.9230, ["wifi", "pool", "spa", "restaurant", "bar", "golf", "kids_club"], ["luxury", "beachfront", "exclusive"], "Mediterranean-style luxury villa resort in South Goa, featuring a private beach strip, golf course, and world-class spa.")
add_hotel("Goa", "Cidade de Goa - IHCL SeleQtions", "comfort", 11000, 8, 15.4601, 73.8090, ["wifi", "pool", "spa", "beach_access", "restaurant"], ["beachside", "colonial", "family"], "Lively Portuguese-hamlet style resort with views of Zuari River and direct beach access.")

# --- JAIPUR ---
add_hotel("Jaipur", "Zostel Jaipur", "budget", 1200, 5, 26.9239, 75.8267, ["wifi", "rooftop_cafe", "ac", "lockers"], ["backpacker", "central", "social"], "Clean, social hostel 5 min walk from Hawa Mahal. Rooftop cafe is the real draw.")
add_hotel("Jaipur", "OYO Townhouse C-Scheme", "budget", 2800, 6, 26.9110, 75.8010, ["wifi", "ac", "parking", "restaurant"], ["business", "central", "modern"], "Conveniently located in C-Scheme, offering modern rooms and easy transit to city monuments.")
add_hotel("Jaipur", "Alsisar Haveli - Heritage Hotel", "comfort", 8500, 8, 26.9224, 75.8073, ["wifi", "pool", "heritage_architecture", "restaurant", "bar"], ["heritage", "haveli", "central"], "A beautifully restored 19th-century royal haveli in the heart of Jaipur, with a pool and courtyard.")
add_hotel("Jaipur", "Rambagh Palace (Taj)", "expedition", 32000, 10, 26.8982, 75.8115, ["wifi", "pool", "spa", "fine_dining", "gardens", "peacocks"], ["luxury", "palace", "royal"], "The jewel of Jaipur, this authentic former residence of the Maharaja offers absolute luxury and royal treatment.")
add_hotel("Jaipur", "Umaid Bhawan Hotel", "comfort", 4500, 7, 26.9288, 75.7975, ["wifi", "pool", "rooftop_restaurant", "heritage_style"], ["heritage", "value", "rooftop"], "Charming budget heritage hotel featuring detailed carved balconies and a lovely rooftop restaurant.")

# --- VARANASI ---
add_hotel("Varanasi", "Zostel Varanasi", "budget", 1000, 5, 25.3110, 83.0010, ["wifi", "common_area", "ac", "lockers"], ["backpacker", "central", "social"], "A lively backpacker base just a 15-minute walk from the main Dashashwamedh Ghat.")
add_hotel("Varanasi", "Alka Guest House", "budget", 3500, 6, 25.3094, 83.0125, ["wifi", "river_view", "restaurant", "terrace"], ["riverside", "ghat", "value"], "Perched directly on Meer Ghat, offering amazing river views and a quiet garden courtyard.")
add_hotel("Varanasi", "BrijRama Palace - Heritage Hotel", "expedition", 18000, 9, 25.3075, 83.0118, ["wifi", "river_view", "fine_dining", "heritage_architecture", "elevator"], ["luxury", "heritage", "riverside"], "An authentic 18th-century fort palace on Darbhanga Ghat, offering unmatched luxury and traditional music evenings.")
add_hotel("Varanasi", "Ganges View Hotel", "comfort", 7000, 8, 25.2905, 83.0070, ["wifi", "library", "restaurant", "terrace"], ["spiritual", "culture", "peaceful"], "Charming, artsy hotel at Assi Ghat, decorated with local folk paintings and historic books.")
add_hotel("Varanasi", "Taj Ganges Varanasi", "expedition", 14000, 9, 25.3288, 82.9815, ["wifi", "pool", "spa", "gym", "gardens", "restaurant"], ["luxury", "gardens", "business"], "Set in 40 acres of green orchards in Nadesar, offering a quiet refuge from the old city's chaos.")

# --- MUNNAR ---
add_hotel("Munnar", "Zostel Munnar", "budget", 1400, 5, 10.0542, 77.0595, ["wifi", "common_room", "parking", "bonfire"], ["backpacker", "tea_view", "social"], "Lively container hostel set amidst tea plantations, offering panoramic valley views.")
add_hotel("Munnar", "Tea County Hill Station Resort", "comfort", 7500, 8, 10.0889, 77.0595, ["wifi", "restaurant", "bar", "ayurveda_spa", "gym"], ["government", "hill_station", "spacious"], "A spacious KTDC heritage resort nestled between green hills, offering traditional Ayurvedic massages.")
add_hotel("Munnar", "Windermere Estate", "comfort", 11000, 8, 10.0760, 77.0620, ["wifi", "plantation_view", "bonfire", "restaurant"], ["boutique", "nature", "peaceful"], "A quiet, boutique retreat set on a working tea and cardamom plantation, with rustic cottage chalets.")
add_hotel("Munnar", "The Tall Trees Resort", "expedition", 16000, 9, 10.0650, 77.0290, ["wifi", "spa", "restaurant", "forest_cottage", "bonfire"], ["luxury", "forest", "nature"], "Exclusive cottages built under the high canopy of giant trees, offering complete isolation and misty paths.")
add_hotel("Munnar", "OYO Townhouse Munnar", "budget", 3000, 6, 10.0910, 77.0630, ["wifi", "parking", "restaurant"], ["value", "town_near"], "Convenient, modern rooms close to the Munnar main bazaar, ideal for transit travelers.")

# --- LEH ---
add_hotel("Leh", "Zostel Leh", "budget", 1600, 5, 34.1662, 77.5750, ["wifi", "common_area", "bonfire", "views"], ["backpacker", "views", "social"], "India's highest Zostel, featuring stunning views of Leh Palace and the Stok range from the terrace.")
add_hotel("Leh", "Hotel Singge Palace", "comfort", 8000, 8, 34.1595, 77.5810, ["wifi", "restaurant", "heating", "parking", "oxygen_parlour"], ["central", "comfort", "heating"], "A premium hotel in the city center, equipped with room heaters and an oxygen parlor for acclimatization.")
add_hotel("Leh", "The Grand Dragon Ladakh", "expedition", 15000, 9, 34.1512, 77.5850, ["wifi", "heating", "spa", "fine_dining", "gym", "views"], ["luxury", "green", "views"], "Ladakh's premier eco-friendly luxury hotel, combining traditional Ladakhi architecture with modern heating.")
add_hotel("Leh", "Pangong Camp Retreat", "expedition", 4500, 6, 33.7275, 78.4611, ["lake_view", "meals", "campfire"], ["camp", "lakefront", "adventure"], "Luxury tents set directly on the banks of Pangong Tso Lake, offering warm beds and hearty local food.")
add_hotel("Leh", "Hotel Glacier View", "comfort", 4800, 7, 34.1610, 77.5775, ["wifi", "rooftop", "restaurant", "parking"], ["views", "value"], "Quiet rooms in Changspa area, featuring private balconies looking at the snowy Leh peaks.")

# --- MUMBAI ---
add_hotel("Mumbai", "Zostel Mumbai (Andheri)", "budget", 1500, 5, 19.1235, 72.8735, ["wifi", "ac", "cafe", "lockers"], ["backpacker", "transit", "social"], "Clean, social backpacker base in Andheri East, well-connected to Metro and international airport.")
add_hotel("Mumbai", "Hotel Sea Green South Marine Drive", "comfort", 5500, 7, 18.9312, 72.8233, ["wifi", "ac", "sea_view", "parking"], ["sea_view", "marine_drive", "value"], "Heritage hotel directly on Marine Drive, offering simple rooms with balconies looking at the sea.")
add_hotel("Mumbai", "The Taj Mahal Palace", "expedition", 28000, 10, 18.9217, 72.8331, ["wifi", "pool", "spa", "fine_dining", "sea_view", "bar", "heritage"], ["luxury", "heritage", "iconic"], "Mumbai's most famous landmark hotel since 1903, offering unmatched luxury overlooking the Gateway of India.")
add_hotel("Mumbai", "Trident Nariman Point", "comfort", 13000, 8, 18.9268, 72.8205, ["wifi", "pool", "sea_view", "restaurant", "bar", "gym"], ["sea_view", "business", "luxury"], "Sleek high-rise hotel at the tip of Nariman Point, offering sweeping panoramic views of Marine Drive.")
add_hotel("Mumbai", "OYO Townhouse Bandra", "budget", 4000, 6, 19.0550, 72.8380, ["wifi", "ac", "room_service"], ["central", "value", "shopping"], "Modern rooms in Bandra West, placing you in the heart of Mumbai's trendiest shopping and dining lane.")

# --- BANGALORE ---
add_hotel("Bangalore", "Zostel Bangalore (Indiranagar)", "budget", 1300, 5, 12.9695, 77.6405, ["wifi", "ac", "rooftop_cafe", "lockers"], ["backpacker", "cafes", "social"], "Located in Bangalore's pub hub Indiranagar, featuring a cool rooftop space for networking.")
add_hotel("Bangalore", "Treebo Trend Central Indiranagar", "budget", 3000, 6, 12.9730, 77.6410, ["wifi", "ac", "breakfast", "parking"], ["value", "business", "central"], "A comfortable, budget-friendly option situated close to microbreweries and Metro station.")
add_hotel("Bangalore", "ITC Gardenia, a Luxury Collection Hotel", "expedition", 19000, 10, 12.9698, 77.5960, ["wifi", "pool", "spa", "fine_dining", "gym", "green_building"], ["luxury", "eco_friendly", "spa"], "Sleek, eco-friendly luxury hotel near UB City, featuring vertical gardens and award-winning dining.")
add_hotel("Bangalore", "Taj West End", "expedition", 22000, 10, 12.9840, 77.5850, ["wifi", "pool", "gardens", "spa", "heritage_architecture", "fine_dining"], ["luxury", "heritage", "gardens"], "A gorgeous 125-year-old heritage hotel set in 20 acres of tropical gardens, featuring tennis courts.")
add_hotel("Bangalore", "The Paul Bangalore", "comfort", 8500, 8, 12.9610, 77.6390, ["wifi", "pool", "microbrewery", "restaurant", "bar"], ["business", "brewery", "suites"], "All-suite business hotel in Domlur, housing its own popular craft microbrewery 'Murphy's'.")

# --- KOLKATA ---
add_hotel("Kolkata", "Lalaji Backpackers Hostel", "budget", 900, 4, 22.5600, 88.3550, ["wifi", "common_kitchen", "parking"], ["budget", "backpacker", "central"], "Simple, budget backpacker hostel located near Sudder Street, ideal for shoestring travelers.")
add_hotel("Kolkata", "The Broadway Hotel", "budget", 2800, 6, 22.5645, 88.3570, ["wifi", "ac", "bar", "vintage"], ["heritage", "vintage_bar", "value"], "An iconic 1930s hotel preserving old Calcutta charm, featuring a retro bar downstairs.")
add_hotel("Kolkata", "The Oberoi Grand", "expedition", 20000, 10, 22.5602, 88.3515, ["wifi", "pool", "spa", "fine_dining", "bar", "heritage"], ["luxury", "heritage", "central"], "Known as the Grand Dame of Chowringhee, this historic neo-classical palace offers timeless luxury.")
add_hotel("Kolkata", "The Peerless Inn", "comfort", 6500, 8, 22.5615, 88.3522, ["wifi", "restaurant", "gym", "ac", "bar"], ["central", "value", "food"], "Conveniently located near Esplanade, housing the legendary Bengali specialty restaurant 'Aheli'.")
add_hotel("Kolkata", "Astoria Hotel", "comfort", 3200, 6, 22.5568, 88.3535, ["wifi", "ac", "parking", "room_service"], ["central", "value"], "A reliable mid-range hotel near the Indian Museum, popular with tourist groups.")

# --- SHILLONG ---
add_hotel("Shillong", "Pine Cliffe Hostel", "budget", 1200, 5, 25.5683, 91.8845, ["wifi", "parking", "meals", "bonfire"], ["budget", "backpacker", "offbeat"], "Cozy, pine-surrounded backpacker cottage near the city center, offering bonfire nights.")
add_hotel("Shillong", "Hotel Polo Towers", "comfort", 7000, 8, 25.5802, 91.8900, ["wifi", "restaurant", "bar", "spa", "heating"], ["business", "comfort", "central"], "Shillong's primary modern hotel, offering centrally heated rooms and a popular bakery cafe.")
add_hotel("Shillong", "Ri Kynjai - Serenity by the Lake", "expedition", 16000, 10, 25.6450, 91.8980, ["wifi", "spa", "lake_view", "ayurveda", "restaurant"], ["luxury", "lakefront", "cottages"], "Breathtaking luxury resort overlooking Umiam Lake, designed in traditional Khasi thatch-roof style.")
add_hotel("Shillong", "Aerodene Cottage - Heritage Stay", "comfort", 9000, 8, 25.5822, 91.8790, ["wifi", "heritage_architecture", "garden", "library"], ["heritage", "boutique", "peaceful"], "A lovingly restored 60-year-old Assam-style wooden cottage, offering organic meals and green gardens.")
add_hotel("Shillong", "OYO Townhouse Police Bazar", "budget", 3500, 6, 25.5780, 91.8830, ["wifi", "heating", "room_service"], ["central", "value"], "Simple, modern rooms located right next to the Police Bazar shopping circle.")

# --- MANALI ---
add_hotel("Manali", "Zostel Homes Manali (Nasogi)", "budget", 1500, 5, 32.2355, 77.1810, ["wifi", "mountain_view", "cafe", "bonfire"], ["backpacker", "mountain_view", "social"], "Charming wooden home-style hostel in Nasogi village, offering amazing views of the Solang valley.")
add_hotel("Manali", "The Johnson Lodge & Spa", "comfort", 8000, 8, 32.2462, 77.1890, ["wifi", "spa", "restaurant", "bar", "garden"], ["comfort", "wood_cabins", "family"], "Cozy stone-and-wood chalets near Mall Road, featuring a lively garden restaurant and spa.")
add_hotel("Manali", "Span Resort & Spa", "expedition", 20000, 10, 32.1480, 77.1870, ["wifi", "pool", "spa", "river_bank", "fine_dining", "bar"], ["luxury", "riverside", "nature"], "Sprawling luxury resort located on the banks of the Beas River, offering private cottages and pine lawns.")
add_hotel("Manali", "Solang Ski Resort", "comfort", 7500, 8, 32.3160, 77.1610, ["wifi", "ski_access", "heating", "restaurant"], ["skiing", "adventure", "snow"], "Located directly in Solang Valley, offering ski gear rentals and quick access to paragliding slopes.")
add_hotel("Manali", "OYO Townhouse Old Manali", "budget", 3200, 6, 32.2530, 77.1780, ["wifi", "heating", "parking", "restaurant"], ["value", "cafes"], "Modern budget-friendly rooms in Old Manali, placing you within walking distance of music cafes.")

# --- RISHIKESH (Original & Required) ---
add_hotel("Rishikesh", "Ganga View Hostel", "budget", 1600, 4, 30.1087, 78.2983, ["wifi", "common_area", "river_view", "yoga_space"], ["budget", "river_view", "backpacker", "yoga"], "Clean, social hostel close to Ram Jhula, with views of the Ganges and a yoga deck.")
add_hotel("Rishikesh", "Ram Jhula Rest House", "budget", 2000, 5, 30.1156, 78.3045, ["wifi", "hot_water", "parking"], ["budget", "central", "walking_distance"], "Simple guest house near Ram Jhula, offering clean rooms and quick access to ghats.")
add_hotel("Rishikesh", "Riverside Comfort Stay", "comfort", 4200, 8, 30.0869, 78.2676, ["wifi", "parking", "restaurant", "river_view", "balcony"], ["riverside", "central", "comfort", "balcony"], "Comfortable rooms with river balconies and on-site multi-cuisine dining options.")
add_hotel("Rishikesh", "Aloha on the Ganges", "comfort", 5000, 8, 30.0920, 78.2730, ["wifi", "parking", "restaurant", "pool", "river_view", "yoga"], ["riverside", "yoga", "pool", "upscale"], "Stunning resort on the Ganges, offering yoga packages, spa facilities, and a pool.")
add_hotel("Rishikesh", "Camp Crossfire Rishikesh", "expedition", 2500, 6, 30.1200, 78.3200, ["campfire", "river_access", "outdoor_dining", "attached_bath"], ["camp", "riverside", "adventure", "outdoor"], "Luxury tents in Shivpuri, with bonfire pits and direct river rafting access.")
add_hotel("Rishikesh", "Shivpuri Beach Camp", "expedition", 22000, 5, 30.1350, 78.3400, ["campfire", "river_beach", "outdoor_dining"], ["camp", "beach", "adventure", "rafting_nearby"], "Basic riverside beach camp offering outdoor meals and campfires.")

# --- TIRTHAN VALLEY (Original & Required) ---
add_hotel("Tirthan Valley", "Tirthan River Homestay", "budget", 1500, 5, 31.6200, 77.4400, ["home_cooked_meals", "river_view", "hot_water"], ["homestay", "budget", "local_food", "river_view"], "Homestay next to the river, serving home-cooked Himachali meals.")
add_hotel("Tirthan Valley", "Himalayan Nest Guesthouse", "budget", 2000, 5, 31.6350, 77.4520, ["wifi", "home_cooked_meals", "mountain_view"], ["budget", "guesthouse", "mountain_view", "quiet"], "Peaceful guesthouse offering mountain views and home-cooked food.")
add_hotel("Tirthan Valley", "Raju Bharti's Guest House", "comfort", 3800, 7, 31.6381, 77.4511, ["wifi", "home_cooked_meals", "river_view", "bonfire", "fishing_gear"], ["comfort", "river_view", "trout_fishing", "bonfire"], "The legendary homestay in Gushaini, famous for hospitality and fresh trout dinners.")
add_hotel("Tirthan Valley", "WhiteBridge Nature Resort", "comfort", 4200, 8, 31.6420, 77.4560, ["wifi", "restaurant", "river_view", "bonfire", "mountain_view"], ["comfort", "nature_resort", "scenic", "peaceful"], "Scenic resort situated by the river bridge, with modern rooms and a lawn.")
add_hotel("Tirthan Valley", "GHNP Base Camp Tents", "expedition", 2200, 5, 31.7500, 77.5200, ["campfire", "forest_access", "guide_available", "basic_meals"], ["camp", "forest", "trekking_base", "wildlife"], "Basic high-altitude tents at the park entry gate, ideal for morning trekkers.")
add_hotel("Tirthan Valley", "Jalori Pass Shepherd Camp", "expedition", 1800, 4, 31.7200, 77.3900, ["campfire", "basic_meals", "mountain_access"], ["camp", "high_altitude", "stargazing", "remote"], "Remote high-altitude camping near the pass, perfect for stargazing.")
