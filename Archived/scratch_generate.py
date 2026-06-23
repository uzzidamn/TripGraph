import json
import os
from pathlib import Path

activities = []

# --- GOA (20 Activities) ---
goa_activities = [
    {
        "activity_id": "baga_beach_goa_01", "destination": "Goa", "name": "Baga Beach Relaxation & Water Sports",
        "category": "water_sport", "duration_minutes": 180, "cost_per_person": 1500,
        "available_slots": ["09:00", "11:00", "14:00", "16:00"], "risk_level": "medium",
        "tags": ["beach", "parasailing", "jet_ski", "nightlife"], "lat": 15.5553, "lng": 73.7517,
        "fatigue_score_base": 5, "morale_score_base": 8, "best_time_of_day": "afternoon",
        "best_season": ["Nov-Feb"], "accessibility": "easy",
        "editorial_summary": "Goa's most vibrant and crowded beach, offering high-octane water sports and endless beach shacks.",
        "opening_hours": ["Monday-Sunday: 06:00-23:00"], "skip_if": "Heavy rains or monsoons make water sports unsafe.",
        "insider_tip": "Book water sports package directly with registered local operators at the beach to save 30% over hotel bookings.",
        "confidence_pct": 95
    },
    {
        "activity_id": "fontainhas_walk_goa_02", "destination": "Goa", "name": "Fontainhas Latin Quarter Walking Tour",
        "category": "cultural", "duration_minutes": 120, "cost_per_person": 800,
        "available_slots": ["08:30", "16:30"], "risk_level": "low",
        "tags": ["heritage", "portuguese", "architecture", "photography"], "lat": 15.4925, "lng": 73.8322,
        "fatigue_score_base": 3, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Oct-May"], "accessibility": "easy",
        "editorial_summary": "Walk through narrow winding streets lined with colorful 18th-century Portuguese houses.",
        "opening_hours": ["Monday-Sunday: 00:00-23:59"], "skip_if": "Midday heat can make walking uncomfortable.",
        "insider_tip": "Visit the Confeitaria 31 De Janeiro bakery for authentic Goan bebinca and coconut cookies.",
        "confidence_pct": 96
    },
    {
        "activity_id": "bom_jesus_goa_03", "destination": "Goa", "name": "Basilica of Bom Jesus Heritage Tour",
        "category": "cultural", "duration_minutes": 90, "cost_per_person": 0,
        "available_slots": ["09:00", "11:00", "14:30", "16:00"], "risk_level": "low",
        "tags": ["heritage", "church", "baroque", "history", "spiritual"], "lat": 15.5009, "lng": 73.9116,
        "fatigue_score_base": 2, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-May"], "accessibility": "easy",
        "editorial_summary": "A UNESCO World Heritage Site holding the mortal remains of St. Francis Xavier.",
        "opening_hours": ["Monday-Saturday: 09:00-18:30", "Sunday: 10:30-18:30"], "skip_if": "Dress code violation (should cover shoulders and knees).",
        "insider_tip": "Look for the detailed wooden carvings and the silver casket created by Florentine artists.",
        "confidence_pct": 98
    },
    {
        "activity_id": "dudhsagar_falls_goa_04", "destination": "Goa", "name": "Dudhsagar Waterfalls Jeep Trek",
        "category": "adventure", "duration_minutes": 360, "cost_per_person": 1200,
        "available_slots": ["07:30", "09:00"], "risk_level": "medium",
        "tags": ["nature", "waterfall", "trekking", "wildlife"], "lat": 15.3175, "lng": 74.3142,
        "fatigue_score_base": 7, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Oct-May"], "accessibility": "moderate",
        "editorial_summary": "A four-tiered waterfall cascading down the Mandovi River, surrounded by deciduous forests.",
        "opening_hours": ["Monday-Sunday: 09:00-17:00"], "skip_if": "Monsoons sometimes close the jeep track due to high waters.",
        "insider_tip": "Wear sturdy shoes with good grip and carry swimwear; you can bathe in the natural pool under the fall.",
        "confidence_pct": 92
    },
    {
        "activity_id": "anjuna_flea_goa_05", "destination": "Goa", "name": "Anjuna Wednesday Flea Market Shopping",
        "category": "shopping", "duration_minutes": 150, "cost_per_person": 0,
        "available_slots": ["10:00", "14:00", "16:00"], "risk_level": "low",
        "tags": ["shopping", "flea_market", "hippie", "crafts"], "lat": 15.5786, "lng": 73.7431,
        "fatigue_score_base": 4, "morale_score_base": 7, "best_time_of_day": "evening",
        "best_season": ["Nov-Apr"], "accessibility": "easy",
        "editorial_summary": "The original hippie flea market offering silver jewelry, beachwear, spices, and handmade crafts.",
        "opening_hours": ["Wednesday: 09:00-18:00"], "skip_if": "Any day other than Wednesday; market does not run.",
        "insider_tip": "Bargaining is essential here. Start counter-offers at 40-50% of the vendor's initial price.",
        "confidence_pct": 94
    },
    {
        "activity_id": "aguada_fort_goa_06", "destination": "Goa", "name": "Fort Aguada & Lighthouse Visit",
        "category": "cultural", "duration_minutes": 90, "cost_per_person": 50,
        "available_slots": ["09:00", "10:30", "15:00", "16:30"], "risk_level": "low",
        "tags": ["heritage", "fort", "viewpoint", "history"], "lat": 15.4922, "lng": 73.7739,
        "fatigue_score_base": 3, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-May"], "accessibility": "easy",
        "editorial_summary": "A 17th-century Portuguese fort standing on Sinquerim Beach, featuring a prominent lighthouse.",
        "opening_hours": ["Monday-Sunday: 09:00-18:00"], "skip_if": "Heavy afternoon heat can make walking the ramparts exhausting.",
        "insider_tip": "Head to the lower fort walls near the Taj hotel road for an unobstructed and quiet sunset view.",
        "confidence_pct": 98
    },
    {
        "activity_id": "spice_plantation_goa_07", "destination": "Goa", "name": "Sahakari Spice Farm Tour & lunch",
        "category": "experience", "duration_minutes": 180, "cost_per_person": 500,
        "available_slots": ["11:00", "12:30"], "risk_level": "low",
        "tags": ["experience", "food", "spices", "nature", "family"], "lat": 15.4342, "lng": 74.0253,
        "fatigue_score_base": 3, "morale_score_base": 8, "best_time_of_day": "afternoon",
        "best_season": ["Oct-May"], "accessibility": "easy",
        "editorial_summary": "Walk through tropical spice gardens followed by a traditional Goan buffet served on banana leaves.",
        "opening_hours": ["Monday-Sunday: 09:00-16:30"], "skip_if": "Extreme heavy rain, though monsoons make the farm look very lush.",
        "insider_tip": "The tour includes a warm welcome drink and herbal tea. Try the fresh local cashew feni if offered.",
        "confidence_pct": 93
    },
    {
        "activity_id": "scuba_diving_goa_08", "destination": "Goa", "name": "Scuba Diving at Grande Island",
        "category": "water_sport", "duration_minutes": 300, "cost_per_person": 3000,
        "available_slots": ["07:30"], "risk_level": "high",
        "tags": ["diving", "ocean", "adventure", "marine_life"], "lat": 15.3512, "lng": 73.7667,
        "fatigue_score_base": 6, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Nov-Apr"], "accessibility": "difficult",
        "editorial_summary": "A full-day boat excursion to Grande Island offering shallow coral diving and snorkeling.",
        "opening_hours": ["Monday-Sunday: 07:00-15:00"], "skip_if": "Poor water visibility (common in monsoon/heavy winds).",
        "insider_tip": "Don't expect red sea corals, but you will see groupers, triggerfish, and sometimes dolphins en route.",
        "confidence_pct": 88
    },
    {
        "activity_id": "silent_noise_goa_09", "destination": "Goa", "name": "Silent Noise Headphone Club Night",
        "category": "nightlife", "duration_minutes": 240, "cost_per_person": 1000,
        "available_slots": ["21:00", "22:00"], "risk_level": "low",
        "tags": ["nightlife", "party", "beach", "music"], "lat": 14.9858, "lng": 74.0286,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "night",
        "best_season": ["Nov-Apr"], "accessibility": "easy",
        "editorial_summary": "Dance on the beach to multiple DJs playing simultaneously over wireless headphones.",
        "opening_hours": ["Saturday: 21:00-04:00"], "skip_if": "Any weekday, as the main silent disco events occur on weekends.",
        "insider_tip": "Get there by 10 PM to secure the best headphones. Switch channels to match the crowd dynamics.",
        "confidence_pct": 91
    },
    {
        "activity_id": "casino_royale_goa_10", "destination": "Goa", "name": "Deltin Royale Floating Casino Experience",
        "category": "nightlife", "duration_minutes": 240, "cost_per_person": 3500,
        "available_slots": ["20:00", "22:00"], "risk_level": "low",
        "tags": ["nightlife", "gaming", "river", "dinner"], "lat": 15.5003, "lng": 73.8294,
        "fatigue_score_base": 3, "morale_score_base": 7, "best_time_of_day": "night",
        "best_season": ["Oct-May"], "accessibility": "easy",
        "editorial_summary": "Asia's largest offshore floating casino, offering gaming tables, live music, and unlimited buffet.",
        "opening_hours": ["Monday-Sunday: 24 Hours"], "skip_if": "Smart casual dress code not met (no shorts, slippers, or sleeveless shirts).",
        "insider_tip": "The entry ticket includes playing chips and buffet. Go on weekdays for a less chaotic ferry transit.",
        "confidence_pct": 95
    },
    {
        "activity_id": "arambol_drum_goa_11", "destination": "Goa", "name": "Arambol Sunset Drum Circle & Hippie Market",
        "category": "experience", "duration_minutes": 120, "cost_per_person": 0,
        "available_slots": ["17:00"], "risk_level": "low",
        "tags": ["experience", "hippie", "music", "sunset", "beach"], "lat": 15.6881, "lng": 73.7042,
        "fatigue_score_base": 2, "morale_score_base": 9, "best_time_of_day": "evening",
        "best_season": ["Nov-Mar"], "accessibility": "easy",
        "editorial_summary": "Gather with travelers, musicians, and artists on Arambol beach for a sunset drumming session.",
        "opening_hours": ["Monday-Sunday: 16:30-19:00"], "skip_if": "Rainy or heavily cloudy evenings.",
        "insider_tip": "Sit slightly back on the sand, enjoy the vibe, and buy handmade jewelry from local travelers.",
        "confidence_pct": 90
    },
    {
        "activity_id": "vagator_sunset_goa_12", "destination": "Goa", "name": "Vagator Beach & Chapora Fort Sunset View",
        "category": "nature", "duration_minutes": 90, "cost_per_person": 0,
        "available_slots": ["16:30", "17:00"], "risk_level": "low",
        "tags": ["sunset", "viewpoint", "fort", "scenic"], "lat": 15.6061, "lng": 73.7336,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-May"], "accessibility": "moderate",
        "editorial_summary": "Walk up to the red cliffs of Chapora Fort, made famous by the movie 'Dil Chahta Hai'.",
        "opening_hours": ["Monday-Sunday: 08:00-18:30"], "skip_if": "Steep rocky trail is slippery during heavy downpours.",
        "insider_tip": "The climb is quick (15 mins) but steep. Wear good sneakers and carry a bottle of water.",
        "confidence_pct": 97
    },
    {
        "activity_id": "mandovi_cruise_goa_13", "destination": "Goa", "name": "Mandovi River Sunset Cruise",
        "category": "experience", "duration_minutes": 60, "cost_per_person": 500,
        "available_slots": ["17:00", "18:00"], "risk_level": "low",
        "tags": ["experience", "cruise", "boat", "dance", "sunset"], "lat": 15.4988, "lng": 73.8311,
        "fatigue_score_base": 2, "morale_score_base": 6, "best_time_of_day": "evening",
        "best_season": ["Oct-May"], "accessibility": "easy",
        "editorial_summary": "A relaxing river boat ride featuring live Goan dekni and fugdi folk dance performances.",
        "opening_hours": ["Monday-Sunday: 17:00-20:00"], "skip_if": "Heavy river swells or stormy monsoon weather.",
        "insider_tip": "Arrive 30 minutes early at the Santa Monica Jetty to get top deck corner seats.",
        "confidence_pct": 95
    },
    {
        "activity_id": "palolem_kayak_goa_14", "destination": "Goa", "name": "Palolem Beach Kayaking to Monkey Island",
        "category": "water_sport", "duration_minutes": 90, "cost_per_person": 400,
        "available_slots": ["07:30", "09:00", "15:30", "16:30"], "risk_level": "medium",
        "tags": ["kayak", "beach", "adventure", "island"], "lat": 15.0101, "lng": 74.0232,
        "fatigue_score_base": 5, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Nov-Apr"], "accessibility": "easy",
        "editorial_summary": "Paddle through the calm crescent waters of Palolem Beach towards the nearby rocky island.",
        "opening_hours": ["Monday-Sunday: 07:00-18:00"], "skip_if": "High waves or windy afternoons make paddling hard work.",
        "insider_tip": "Kayaking during high tide in the morning gives you the smoothest ride and clearest water.",
        "confidence_pct": 93
    },
    {
        "activity_id": "shack_dining_goa_15", "destination": "Goa", "name": "Beach Shack Dining at Curlies Anjuna",
        "category": "food", "duration_minutes": 120, "cost_per_person": 800,
        "available_slots": ["13:00", "18:00", "20:00"], "risk_level": "low",
        "tags": ["food", "shack", "seafood", "beach_view"], "lat": 15.5714, "lng": 73.7428,
        "fatigue_score_base": 1, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Nov-Apr"], "accessibility": "easy",
        "editorial_summary": "Dine with your toes in the sand at a historic Goan shack, enjoying tandoori red snapper.",
        "opening_hours": ["Monday-Sunday: 08:30-03:00"], "skip_if": "Monsoons, when shacks are disassembled and closed.",
        "insider_tip": "Try the Goan fish curry rice and vindaloo. The upper deck has the best sunset breeze.",
        "confidence_pct": 94
    },
    {
        "activity_id": "curlies_beach_goa_16", "destination": "Goa", "name": "Arambol Sweet Water Lake Walk",
        "category": "nature", "duration_minutes": 120, "cost_per_person": 0,
        "available_slots": ["08:00", "15:00", "16:30"], "risk_level": "low",
        "tags": ["nature", "lake", "swimming", "scenic"], "lat": 15.6983, "lng": 73.7025,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "afternoon",
        "best_season": ["Oct-May"], "accessibility": "moderate",
        "editorial_summary": "Walk along the coastline past Arambol cliffs to a fresh water lake bordered by jungle hills.",
        "opening_hours": ["Monday-Sunday: 06:00-18:30"], "skip_if": "High tide cut-off along the rocky walk path.",
        "insider_tip": "Go past the lake into the jungle (10 min walk) to find the famous giant Banyan tree.",
        "confidence_pct": 91
    },
    {
        "activity_id": "titos_party_goa_17", "destination": "Goa", "name": "Clubbing at Tito's Lane Baga",
        "category": "nightlife", "duration_minutes": 180, "cost_per_person": 1500,
        "available_slots": ["21:00", "22:30"], "risk_level": "low",
        "tags": ["nightlife", "party", "clubbing", "music"], "lat": 15.5562, "lng": 73.7533,
        "fatigue_score_base": 4, "morale_score_base": 7, "best_time_of_day": "night",
        "best_season": ["Nov-Apr"], "accessibility": "easy",
        "editorial_summary": "Experience the classic Goa party street, lined with bars, neon lights, and loud DJs.",
        "opening_hours": ["Monday-Sunday: 18:00-04:00"], "skip_if": "If you are highly uncomfortable in packed tourist environments.",
        "insider_tip": "Couple entry packages are much cheaper and often include unlimited drinks.",
        "confidence_pct": 96
    },
    {
        "activity_id": "butterfly_beach_goa_18", "destination": "Goa", "name": "Butterfly Beach Boat Trip & Dolphin Sighting",
        "category": "nature", "duration_minutes": 120, "cost_per_person": 1200,
        "available_slots": ["08:00", "10:00", "15:00"], "risk_level": "low",
        "tags": ["beach", "boat", "nature", "scenic"], "lat": 15.0183, "lng": 74.0042,
        "fatigue_score_base": 3, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Nov-Apr"], "accessibility": "moderate",
        "editorial_summary": "A hidden cove shaped like a butterfly, reachable mostly via boat, offering pristine waters.",
        "opening_hours": ["Monday-Sunday: 07:00-17:30"], "skip_if": "Rough sea conditions prevent small boat landings.",
        "insider_tip": "Hire a private boat from Agonda or Palolem beach. Morning trips increase dolphin sighting chances.",
        "confidence_pct": 90
    },
    {
        "activity_id": "reis_magos_goa_19", "destination": "Goa", "name": "Reis Magos Fort History Museum",
        "category": "cultural", "duration_minutes": 90, "cost_per_person": 100,
        "available_slots": ["09:30", "11:00", "14:30", "16:00"], "risk_level": "low",
        "tags": ["heritage", "fort", "museum", "history"], "lat": 15.4981, "lng": 73.8093,
        "fatigue_score_base": 2, "morale_score_base": 7, "best_time_of_day": "morning",
        "best_season": ["Oct-May"], "accessibility": "easy",
        "editorial_summary": "A restored 16th-century fortress, showing history exhibitions and Mario Miranda cartoon art.",
        "opening_hours": ["Tuesday-Sunday: 09:30-17:30"], "skip_if": "Mondays, when the fort is closed to visitors.",
        "insider_tip": "The battlements offer great, quiet photography spots looking over the Mandovi river mouth.",
        "confidence_pct": 97
    },
    {
        "activity_id": "divar_island_goa_20", "destination": "Goa", "name": "Divar Island Heritage Ferry Exploration",
        "category": "experience", "duration_minutes": 180, "cost_per_person": 100,
        "available_slots": ["09:00", "14:30"], "risk_level": "low",
        "tags": ["experience", "island", "ferry", "offbeat", "cycling"], "lat": 15.5211, "lng": 73.8833,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-May"], "accessibility": "moderate",
        "editorial_summary": "Take a local river ferry to a serene, sleepy island featuring old Portuguese villas and temples.",
        "opening_hours": ["Monday-Sunday: 24 Hours (ferry runs 06:00-00:00)"], "skip_if": "Floods during peak monsoon.",
        "insider_tip": "Rent a scooter or bicycle before boarding the ferry from Ribandar; there is no local transport on the island.",
        "confidence_pct": 91
    }
]
activities.extend(goa_activities)

# --- JAIPUR (20 Activities) ---
jaipur_activities = [
    {
        "activity_id": "amber_fort_jaipur_01", "destination": "Jaipur", "name": "Amber Fort Heritage Tour",
        "category": "cultural", "duration_minutes": 150, "cost_per_person": 550,
        "available_slots": ["08:00", "09:30", "11:00", "14:00", "15:30"], "risk_level": "low",
        "tags": ["heritage", "fort", "history", "architecture", "family"], "lat": 26.9855, "lng": 75.8513,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A majestic red sandstone and marble fortress overlooking Maota Lake, famous for its mirror palace (Sheesh Mahal).",
        "opening_hours": ["Monday-Sunday: 08:00-17:30"], "skip_if": "Rain or extreme summer heat (fort floors get slippery and hot).",
        "insider_tip": "Arrive by 8:30 AM to beat the tour buses. Hire a licensed guide at the ticket counter to explain the hidden passages.",
        "confidence_pct": 99
    },
    {
        "activity_id": "hawa_mahal_jaipur_02", "destination": "Jaipur", "name": "Hawa Mahal & Wind Palace Tour",
        "category": "cultural", "duration_minutes": 60, "cost_per_person": 200,
        "available_slots": ["09:00", "10:30", "12:00", "14:30", "16:00"], "risk_level": "low",
        "tags": ["heritage", "palace", "architecture", "photography"], "lat": 26.9239, "lng": 75.8267,
        "fatigue_score_base": 3, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "An iconic five-story palace facade with 953 small casements, designed for royal ladies to observe streets.",
        "opening_hours": ["Monday-Sunday: 09:00-17:00"], "skip_if": "Claustrophobia (the inner passages and stairs are very narrow).",
        "insider_tip": "Cross the street to the Wind View Cafe rooftop for the ultimate postcard photo of the facade.",
        "confidence_pct": 99
    },
    {
        "activity_id": "city_palace_jaipur_03", "destination": "Jaipur", "name": "City Palace & Royal Residence Tour",
        "category": "cultural", "duration_minutes": 120, "cost_per_person": 700,
        "available_slots": ["09:30", "11:30", "14:00", "16:00"], "risk_level": "low",
        "tags": ["heritage", "palace", "royalty", "museum"], "lat": 26.9258, "lng": 75.8236,
        "fatigue_score_base": 3, "morale_score_base": 9, "best_time_of_day": "afternoon",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A majestic complex of courtyards, gardens, and buildings combining Rajasthani and Mughal styles.",
        "opening_hours": ["Monday-Sunday: 09:30-17:00"], "skip_if": "Budget travel (tickets are relatively expensive compared to other monuments).",
        "insider_tip": "Visit the Pritam Niwas Chowk inside to see the four famous decorated gates representing the seasons.",
        "confidence_pct": 98
    },
    {
        "activity_id": "jantar_mantar_jaipur_04", "destination": "Jaipur", "name": "Jantar Mantar Astronomical Observatory",
        "category": "cultural", "duration_minutes": 90, "cost_per_person": 200,
        "available_slots": ["09:00", "11:00", "13:00", "15:00"], "risk_level": "low",
        "tags": ["heritage", "science", "astronomy", "unesco"], "lat": 26.9248, "lng": 75.8245,
        "fatigue_score_base": 3, "morale_score_base": 7, "best_time_of_day": "noon",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A collection of nineteen architectural astronomical instruments built by King Sawai Jai Singh II.",
        "opening_hours": ["Monday-Sunday: 09:00-16:30"], "skip_if": "Rainy or cloudy weather, as the sun dial instruments require sunlight to work.",
        "insider_tip": "Hire an on-site guide or use the audio guide; otherwise, the instruments look like abstract concrete blocks.",
        "confidence_pct": 98
    },
    {
        "activity_id": "nahargarh_sunset_jaipur_05", "destination": "Jaipur", "name": "Nahargarh Fort Sunset View",
        "category": "nature", "duration_minutes": 120, "cost_per_person": 200,
        "available_slots": ["16:30", "17:00"], "risk_level": "low",
        "tags": ["sunset", "fort", "viewpoint", "panoramic"], "lat": 26.9374, "lng": 75.8156,
        "fatigue_score_base": 3, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "Perched on the edge of the Aravalli Hills, offering a sweeping bird's-eye view of the entire city.",
        "opening_hours": ["Monday-Sunday: 10:00-17:30"], "skip_if": "Heavily overcast or smoggy evenings.",
        "insider_tip": "Walk to Padao Restaurant inside the fort for a drink while watching the city lights come on.",
        "confidence_pct": 97
    },
    {
        "activity_id": "jaigarh_fort_jaipur_06", "destination": "Jaipur", "name": "Jaigarh Fort & Jaivana Cannon Tour",
        "category": "cultural", "duration_minutes": 90, "cost_per_person": 150,
        "available_slots": ["09:00", "11:00", "14:00", "16:00"], "risk_level": "low",
        "tags": ["heritage", "fort", "military", "history"], "lat": 26.9850, "lng": 75.8450,
        "fatigue_score_base": 4, "morale_score_base": 7, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "Known as the Fort of Victory, it houses Jaivana, which was once the world's largest cannon on wheels.",
        "opening_hours": ["Monday-Sunday: 09:00-16:45"], "skip_if": "Extremely hot summer afternoons.",
        "insider_tip": "Check out the subterranean water tank system, which is an engineering marvel of the 18th century.",
        "confidence_pct": 98
    },
    {
        "activity_id": "albert_hall_jaipur_07", "destination": "Jaipur", "name": "Albert Hall Museum & Night Visit",
        "category": "cultural", "duration_minutes": 90, "cost_per_person": 300,
        "available_slots": ["10:00", "14:00", "19:00"], "risk_level": "low",
        "tags": ["museum", "heritage", "history", "arts"], "lat": 26.9116, "lng": 75.8194,
        "fatigue_score_base": 2, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "The state museum of Rajasthan, housed in a stunning Indo-Saracenic building, glowing at night.",
        "opening_hours": ["Monday-Sunday: 09:00-17:00, 19:00-22:00"], "skip_if": "If you don't enjoy historical artifacts and pottery collections.",
        "insider_tip": "Visit during the night slot (7 PM onwards) when the entire building is spectacularly illuminated.",
        "confidence_pct": 98
    },
    {
        "activity_id": "birla_mandir_jaipur_08", "destination": "Jaipur", "name": "Birla Mandir White Marble Temple",
        "category": "spiritual", "duration_minutes": 60, "cost_per_person": 0,
        "available_slots": ["08:00", "17:00", "18:30"], "risk_level": "low",
        "tags": ["spiritual", "temple", "marble", "peaceful"], "lat": 26.8920, "lng": 75.8153,
        "fatigue_score_base": 2, "morale_score_base": 7, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A modern Hindu temple built entirely of high-quality white marble, glowing softly in the evening.",
        "opening_hours": ["Monday-Sunday: 08:00-12:00, 16:00-20:00"], "skip_if": "Dress code rules apply (modest clothing required).",
        "insider_tip": "Watch the detailed relief carvings of historical figures and philosophers on the temple pillars.",
        "confidence_pct": 97
    },
    {
        "activity_id": "chokhi_dhani_jaipur_09", "destination": "Jaipur", "name": "Chokhi Dhani Ethnic Village Experience",
        "category": "experience", "duration_minutes": 240, "cost_per_person": 900,
        "available_slots": ["18:00", "19:30"], "risk_level": "low",
        "tags": ["experience", "food", "culture", "family", "performance"], "lat": 26.7910, "lng": 75.7573,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A recreated traditional Rajasthani village mock-up, offering folk dances, camel rides, and local thalis.",
        "opening_hours": ["Monday-Sunday: 17:00-23:00"], "skip_if": "If you are short on time (it's located 20km from the city center).",
        "insider_tip": "Opt for the traditional sit-down floor dining layout rather than the buffet dining for a better experience.",
        "confidence_pct": 95
    },
    {
        "activity_id": "johari_bazaar_jaipur_10", "destination": "Jaipur", "name": "Johari Bazaar Gemstone Shopping",
        "category": "shopping", "duration_minutes": 120, "cost_per_person": 0,
        "available_slots": ["11:00", "15:00", "17:00"], "risk_level": "low",
        "tags": ["shopping", "bazaar", "jewelry", "textiles"], "lat": 26.9200, "lng": 75.8280,
        "fatigue_score_base": 3, "morale_score_base": 7, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "The oldest market in Jaipur, famous for traditional block-print sarees, silver jewelry, and gems.",
        "opening_hours": ["Monday-Sunday: 10:00-20:00 (Sundays partially closed)"], "skip_if": "If you cannot tolerate heavy crowds and traffic.",
        "insider_tip": "Always bargain. Do not buy expensive gems here unless you are a certified expert.",
        "confidence_pct": 95
    },
    {
        "activity_id": "bapu_bazaar_jaipur_11", "destination": "Jaipur", "name": "Bapu Bazaar Mojri & Handicrafts Shopping",
        "category": "shopping", "duration_minutes": 120, "cost_per_person": 0,
        "available_slots": ["11:00", "14:00", "17:00"], "risk_level": "low",
        "tags": ["shopping", "bazaar", "crafts", "family"], "lat": 26.9160, "lng": 75.8210,
        "fatigue_score_base": 3, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "Famous for leather mojris (traditional shoes), block prints, and lacquer bangles.",
        "opening_hours": ["Monday-Sunday: 11:00-21:00"], "skip_if": "Any day during peak summer afternoons.",
        "insider_tip": "Go inside the lanes for the best lacquer bangles directly from the artisans who make them.",
        "confidence_pct": 96
    },
    {
        "activity_id": "govind_dev_jaipur_12", "destination": "Jaipur", "name": "Govind Dev Ji Temple Aarti",
        "category": "spiritual", "duration_minutes": 60, "cost_per_person": 0,
        "available_slots": ["08:30", "17:30", "19:00"], "risk_level": "low",
        "tags": ["spiritual", "temple", "culture", "local"], "lat": 26.9288, "lng": 75.8248,
        "fatigue_score_base": 2, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A lively temple in the City Palace complex, featuring massive crowds chanting during Govind Dev ji's aarti.",
        "opening_hours": ["Monday-Sunday: 04:30-12:30, 17:30-21:00"], "skip_if": "Crowd-shy travelers (temple gets extremely packed during aarti).",
        "insider_tip": "Check the exact daily aarti timings online, as they change slightly based on the Hindu calendar.",
        "confidence_pct": 95
    },
    {
        "activity_id": "patrika_gate_jaipur_13", "destination": "Jaipur", "name": "Patrika Gate Instagram Photography",
        "category": "experience", "duration_minutes": 45, "cost_per_person": 0,
        "available_slots": ["07:30", "09:00", "16:00"], "risk_level": "low",
        "tags": ["photography", "architecture", "scenic", "instagram"], "lat": 26.8288, "lng": 75.7958,
        "fatigue_score_base": 1, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A colorful hand-painted archway entrance to Jawahar Circle Garden, illustrating Jaipur history.",
        "opening_hours": ["Monday-Sunday: 24 Hours"], "skip_if": "Clouds or low light, as the gate is best shot under bright sun.",
        "insider_tip": "Go before 8 AM if you want a clean shot without other photographers in your background.",
        "confidence_pct": 97
    },
    {
        "activity_id": "galtaji_temple_jaipur_14", "destination": "Jaipur", "name": "Galtaji Monkey Temple Exploration",
        "category": "spiritual", "duration_minutes": 120, "cost_per_person": 50,
        "available_slots": ["08:30", "15:00", "16:30"], "risk_level": "low",
        "tags": ["spiritual", "temple", "nature", "monkeys", "offbeat"], "lat": 26.9167, "lng": 75.8593,
        "fatigue_score_base": 5, "morale_score_base": 7, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "moderate",
        "editorial_summary": "A sacred Hindu pilgrimage site nestled between cliffs, famous for natural springs and large monkey populations.",
        "opening_hours": ["Monday-Sunday: 05:00-21:00"], "skip_if": "If you are afraid of monkeys (they can get aggressive if they see food).",
        "insider_tip": "Keep all food inside your bag and do not feed the monkeys directly unless with local guide supervision.",
        "confidence_pct": 94
    },
    {
        "activity_id": "panna_meena_jaipur_15", "destination": "Jaipur", "name": "Panna Meena Ka Kund Stepwell",
        "category": "cultural", "duration_minutes": 45, "cost_per_person": 0,
        "available_slots": ["08:30", "10:30", "15:00"], "risk_level": "low",
        "tags": ["heritage", "stepwell", "architecture", "photography"], "lat": 26.9901, "lng": 75.8493,
        "fatigue_score_base": 2, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "An ancient geometric stepwell with interlocking steps and octagonal pavilions, near Amber Fort.",
        "opening_hours": ["Monday-Sunday: 07:00-18:00"], "skip_if": "Stepwell entry: guards no longer allow tourists to walk down the steps.",
        "insider_tip": "Combine this with Amber Fort. Stand at the corners for the best symmetrical perspective photos.",
        "confidence_pct": 98
    },
    {
        "activity_id": "jal_mahal_view_jaipur_16", "destination": "Jaipur", "name": "Jal Mahal Lakeside Viewpoint",
        "category": "nature", "duration_minutes": 45, "cost_per_person": 0,
        "available_slots": ["08:00", "17:00", "18:00"], "risk_level": "low",
        "tags": ["lake", "palace", "scenic", "photography"], "lat": 26.9535, "lng": 75.8465,
        "fatigue_score_base": 2, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A gorgeous palace that appears to float in the middle of Man Sagar Lake; observed from the promenade.",
        "opening_hours": ["Monday-Sunday: 24 Hours"], "skip_if": "Heavily polluted fog mornings.",
        "insider_tip": "Access inside the palace is closed to the public. The promenade is beautiful around sunset with street vendors.",
        "confidence_pct": 98
    },
    {
        "activity_id": "masala_chowk_jaipur_17", "destination": "Jaipur", "name": "Masala Chowk Food Court Tasting",
        "category": "food", "duration_minutes": 90, "cost_per_person": 300,
        "available_slots": ["18:00", "19:30", "21:00"], "risk_level": "low",
        "tags": ["food", "street_food", "local", "family"], "lat": 26.9099, "lng": 75.8190,
        "fatigue_score_base": 2, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "An open-air food court gathering Jaipur's most famous street food stalls in one clean location.",
        "opening_hours": ["Monday-Sunday: 13:00-22:00"], "skip_if": "If you are strictly looking for upscale fine-dining spaces.",
        "insider_tip": "Try the dal baati churma from Gopal Singh's stall, and the spicy pyaz kachori from Rawat Mishthan Bhandar.",
        "confidence_pct": 95
    },
    {
        "activity_id": "jhalana_safari_jaipur_18", "destination": "Jaipur", "name": "Jhalana Leopard Safari Jeep Tour",
        "category": "wildlife", "duration_minutes": 180, "cost_per_person": 1500,
        "available_slots": ["06:45", "15:00"], "risk_level": "medium",
        "tags": ["wildlife", "safari", "leopard", "jeep", "nature"], "lat": 26.8653, "lng": 75.8340,
        "fatigue_score_base": 4, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Nov-Jun"], "accessibility": "easy",
        "editorial_summary": "India's first dedicated leopard reserve, located right on the edge of Jaipur city limits.",
        "opening_hours": ["Monday-Sunday: 06:45-09:30, 15:00-18:00"], "skip_if": "Monsoons, when safari tracks are closed (July to September).",
        "insider_tip": "Book slots at least a month in advance via the Rajasthan Forest Department portal as tickets sell out.",
        "confidence_pct": 91
    },
    {
        "activity_id": "kathputli_show_jaipur_19", "destination": "Jaipur", "name": "Kathputli Puppet Show & Crafts Walk",
        "category": "experience", "duration_minutes": 90, "cost_per_person": 250,
        "available_slots": ["16:00", "18:00"], "risk_level": "low",
        "tags": ["experience", "culture", "family", "performance"], "lat": 26.9205, "lng": 75.8115,
        "fatigue_score_base": 2, "morale_score_base": 7, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A traditional Rajasthani puppet play, illustrating folklore and music in a heritage setting.",
        "opening_hours": ["Monday-Sunday: 10:00-19:00"], "skip_if": "If you are looking for modern theatrical productions.",
        "insider_tip": "You can purchase beautiful handmade puppets directly from the artists after the performance.",
        "confidence_pct": 93
    },
    {
        "activity_id": "patrikagate_walk_jaipur_20", "destination": "Jaipur", "name": "Sisodia Rani Ka Bagh Garden Walk",
        "category": "nature", "duration_minutes": 90, "cost_per_person": 50,
        "available_slots": ["09:00", "15:00", "16:30"], "risk_level": "low",
        "tags": ["nature", "garden", "scenic", "fountains", "peaceful"], "lat": 26.8833, "lng": 75.8753,
        "fatigue_score_base": 3, "morale_score_base": 6, "best_time_of_day": "afternoon",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A tiered royal garden decorated with painted murals showing the life of Lord Krishna.",
        "opening_hours": ["Monday-Sunday: 08:00-18:00"], "skip_if": "Peak summer days (fountains might not be running).",
        "insider_tip": "This is a quiet, offbeat spot compared to Jaipur's major palaces. Ideal for couples and sketch artists.",
        "confidence_pct": 92
    }
]
activities.extend(jaipur_activities)

# --- VARANASI (20 Activities) ---
varanasi_activities = [
    {
        "activity_id": "kashi_temple_varanasi_01", "destination": "Varanasi", "name": "Kashi Vishwanath Golden Temple Tour",
        "category": "spiritual", "duration_minutes": 120, "cost_per_person": 0,
        "available_slots": ["05:30", "09:00", "14:30", "17:30"], "risk_level": "low",
        "tags": ["spiritual", "temple", "hinduism", "culture"], "lat": 25.3109, "lng": 83.0104,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "moderate",
        "editorial_summary": "The sacred temple of Lord Shiva, featuring its famous gold-plated spire and new temple corridor.",
        "opening_hours": ["Monday-Sunday: 03:00-23:00"], "skip_if": "If you don't carry physical ID cards (security is very strict).",
        "insider_tip": "Phones, smartwatches, and leather goods are strictly banned. Leave them in lockers at your hotel or shop entry.",
        "confidence_pct": 98
    },
    {
        "activity_id": "ganga_aarti_varanasi_02", "destination": "Varanasi", "name": "Dashashwamedh Ghat Evening Ganga Aarti",
        "category": "spiritual", "duration_minutes": 90, "cost_per_person": 0,
        "available_slots": ["18:00"], "risk_level": "low",
        "tags": ["spiritual", "aarti", "river", "evening", "culture"], "lat": 25.3072, "lng": 83.0105,
        "fatigue_score_base": 3, "morale_score_base": 9, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A grand, synchronized evening prayer ritual performed with brass lamps at the edge of the Ganges.",
        "opening_hours": ["Monday-Sunday: 18:30-20:00"], "skip_if": "Floods during peak monsoon cover the ghat steps.",
        "insider_tip": "Rent a seat on a shared boat parked in front of the ghat to watch the ritual from the water.",
        "confidence_pct": 99
    },
    {
        "activity_id": "assi_ghat_varanasi_03", "destination": "Varanasi", "name": "Subah-e-Banaras Assi Ghat Sunrise Experience",
        "category": "spiritual", "duration_minutes": 120, "cost_per_person": 0,
        "available_slots": ["05:00"], "risk_level": "low",
        "tags": ["spiritual", "sunrise", "yoga", "performance", "river"], "lat": 25.2900, "lng": 83.0069,
        "fatigue_score_base": 3, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "Enjoy a serene start to the day with Vedic chanting, classical music, and yoga sessions by the Ganges.",
        "opening_hours": ["Monday-Sunday: 05:00-08:00"], "skip_if": "If you cannot wake up by 4:30 AM.",
        "insider_tip": "Stick around after the chants to try hot piping kachoris from Chachi Ki Dukan near Assi Ghat.",
        "confidence_pct": 97
    },
    {
        "activity_id": "sunrise_boat_varanasi_04", "destination": "Varanasi", "name": "Sunrise Ganges Boat Cruise",
        "category": "experience", "duration_minutes": 90, "cost_per_person": 300,
        "available_slots": ["05:30"], "risk_level": "low",
        "tags": ["experience", "boat", "river", "sunrise", "scenic"], "lat": 25.3000, "lng": 83.0120,
        "fatigue_score_base": 2, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "Float down the Ganges at dawn, observing bathers, rituals, and the orange glow hitting the ghats.",
        "opening_hours": ["Monday-Sunday: 05:00-08:00"], "skip_if": "Monsoons, when boat operations are banned due to heavy currents.",
        "insider_tip": "Ask your boatman to row from Assi Ghat all the way to Manikarnika Ghat to see the full stretch.",
        "confidence_pct": 96
    },
    {
        "activity_id": "sarnath_tour_varanasi_05", "destination": "Varanasi", "name": "Sarnath Buddhist Pilgrimage Tour",
        "category": "cultural", "duration_minutes": 180, "cost_per_person": 50,
        "available_slots": ["09:00", "14:00"], "risk_level": "low",
        "tags": ["heritage", "buddhism", "archaeology", "history"], "lat": 25.3762, "lng": 83.0227,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "The historical park where Lord Buddha gave his first sermon; features massive stupas and museums.",
        "opening_hours": ["Monday-Sunday: 06:00-18:00"], "skip_if": "Mondays (Sarnath museum is closed on Mondays).",
        "insider_tip": "Check out the famous Lion Capital of Ashoka inside the air-conditioned museum building.",
        "confidence_pct": 98
    },
    {
        "activity_id": "bhu_tour_varanasi_06", "destination": "Varanasi", "name": "Banaras Hindu University (BHU) Campus Tour",
        "category": "cultural", "duration_minutes": 120, "cost_per_person": 0,
        "available_slots": ["10:00", "15:00"], "risk_level": "low",
        "tags": ["campus", "architecture", "temple", "peaceful"], "lat": 25.2677, "lng": 82.9912,
        "fatigue_score_base": 3, "morale_score_base": 7, "best_time_of_day": "afternoon",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A clean, green university campus housing the grand New Vishwanath Temple (VT) in red sandstone.",
        "opening_hours": ["Monday-Sunday: 08:00-19:00"], "skip_if": "During exams or holidays, when some campus sites are limited.",
        "insider_tip": "Visit the VT temple grounds and enjoy the cold, sweet lassi and sandesh at the campus dairy stalls.",
        "confidence_pct": 95
    },
    {
        "activity_id": "street_food_varanasi_07", "destination": "Varanasi", "name": "Banaras Street Food Tasting Tour",
        "category": "food", "duration_minutes": 120, "cost_per_person": 300,
        "available_slots": ["08:30", "17:00", "19:00"], "risk_level": "low",
        "tags": ["food", "street_food", "local", "spicy"], "lat": 25.3085, "lng": 83.0088,
        "fatigue_score_base": 3, "morale_score_base": 9, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "Taste authentic Banarasi treats including tamatar chaat, malaiyo, and wood-churned lassi.",
        "opening_hours": ["Monday-Sunday: 08:00-22:00"], "skip_if": "If you have a very sensitive stomach; eat only at clean, highly-rated stalls.",
        "insider_tip": "Head to Kashi Chat Bhandar for Tamatar Chaat and try Malaiyo (winter sweet foam) at Chowk.",
        "confidence_pct": 94
    },
    {
        "activity_id": "saree_weaving_varanasi_08", "destination": "Varanasi", "name": "Banarasi Saree Weaving Workshop Tour",
        "category": "experience", "duration_minutes": 90, "cost_per_person": 0,
        "available_slots": ["10:30", "14:30", "16:00"], "risk_level": "low",
        "tags": ["experience", "crafts", "weaving", "textiles"], "lat": 25.3200, "lng": 82.9980,
        "fatigue_score_base": 2, "morale_score_base": 7, "best_time_of_day": "afternoon",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "Observe Muslim silk weavers hand-crafting beautiful sarees using silver and gold threads on wooden looms.",
        "opening_hours": ["Monday-Saturday: 10:00-18:00"], "skip_if": "Sundays, when most weaving workshops are closed.",
        "insider_tip": "Avoid auto-rickshaw drivers who offer to take you to 'cheap Govt factories' — they charge heavy markups.",
        "confidence_pct": 91
    },
    {
        "activity_id": "blue_lassi_varanasi_09", "destination": "Varanasi", "name": "Blue Lassi Shop Tasting",
        "category": "food", "duration_minutes": 60, "cost_per_person": 150,
        "available_slots": ["11:00", "14:00", "17:00", "19:00"], "risk_level": "low",
        "tags": ["food", "lassi", "famous", "must_visit"], "lat": 25.3115, "lng": 83.0118,
        "fatigue_score_base": 2, "morale_score_base": 8, "best_time_of_day": "afternoon",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A tiny 100-year-old shop serving hand-churned fruit lassis in clay cups, decorated with traveler photos.",
        "opening_hours": ["Monday-Sunday: 09:00-22:00"], "skip_if": "If you are uncomfortable sitting near burning cremation processions passing by.",
        "insider_tip": "Try the Pomegranate-Chocolate Lassi. It is located near Manikarnika Ghat entry path.",
        "confidence_pct": 95
    },
    {
        "activity_id": "ramnagar_fort_varanasi_10", "destination": "Varanasi", "name": "Ramnagar Fort & Museum Visit",
        "category": "cultural", "duration_minutes": 120, "cost_per_person": 150,
        "available_slots": ["10:00", "14:00", "15:30"], "risk_level": "low",
        "tags": ["heritage", "fort", "museum", "river_view"], "lat": 25.2678, "lng": 83.0232,
        "fatigue_score_base": 3, "morale_score_base": 6, "best_time_of_day": "afternoon",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A crumbling 18th-century sandstone fortress on the eastern bank, housing an odd vintage car collection.",
        "opening_hours": ["Monday-Sunday: 10:00-17:00"], "skip_if": "Photography is banned inside the museum room.",
        "insider_tip": "Check out the royal collection of vintage weapons, ivory palanquins, and antique clocks.",
        "confidence_pct": 95
    },
    {
        "activity_id": "manikarnika_view_varanasi_11", "destination": "Varanasi", "name": "Manikarnika Ghat Cremation Ghat Walk",
        "category": "spiritual", "duration_minutes": 60, "cost_per_person": 0,
        "available_slots": ["17:00", "18:30"], "risk_level": "low",
        "tags": ["spiritual", "ritual", "history", "culture"], "lat": 25.3106, "lng": 83.0135,
        "fatigue_score_base": 3, "morale_score_base": 7, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "moderate",
        "editorial_summary": "Varanasi's primary cremation ghat, where funeral pyres burn constantly along the Ganges.",
        "opening_hours": ["Monday-Sunday: 24 Hours"], "skip_if": "Photography is strictly forbidden and highly disrespectful.",
        "insider_tip": "Observe from a distance on the ghat steps or a boat. Ignore local scammers claiming to need 'cremation wood donations'.",
        "confidence_pct": 96
    },
    {
        "activity_id": "sankat_mochan_varanasi_12", "destination": "Varanasi", "name": "Sankat Mochan Hanuman Temple Tour",
        "category": "spiritual", "duration_minutes": 60, "cost_per_person": 0,
        "available_slots": ["06:00", "17:00", "19:00"], "risk_level": "low",
        "tags": ["spiritual", "temple", "monkeys", "hinduism"], "lat": 25.2818, "lng": 82.9989,
        "fatigue_score_base": 2, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A peaceful Lord Hanuman temple founded by poet-saint Tulsidas, full of resident monkeys.",
        "opening_hours": ["Monday-Sunday: 05:00-12:00, 15:00-22:00"], "skip_if": "Security checks: electronics, phones, and bags are not allowed inside.",
        "insider_tip": "Try the famous besan ladoos sold inside the temple counters; they are incredibly fresh.",
        "confidence_pct": 96
    },
    {
        "activity_id": "tulsi_manas_varanasi_13", "destination": "Varanasi", "name": "Tulsi Manas Mandir Marble Temple",
        "category": "spiritual", "duration_minutes": 60, "cost_per_person": 0,
        "available_slots": ["09:00", "15:30", "18:00"], "risk_level": "low",
        "tags": ["spiritual", "temple", "marble", "history"], "lat": 25.2842, "lng": 82.9998,
        "fatigue_score_base": 2, "morale_score_base": 7, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A white marble temple where the Hindu epic Ramcharitmanas was written; walls show carved verses.",
        "opening_hours": ["Monday-Sunday: 05:30-12:00, 15:30-21:00"], "skip_if": "If you expect ancient historical architecture.",
        "insider_tip": "Visit the second floor to see the moving mechanical puppet scenes depicting Hindu mythology.",
        "confidence_pct": 95
    },
    {
        "activity_id": "durga_kund_varanasi_14", "destination": "Varanasi", "name": "Durga Kund Red Temple Visit",
        "category": "spiritual", "duration_minutes": 60, "cost_per_person": 0,
        "available_slots": ["08:30", "17:00", "19:00"], "risk_level": "low",
        "tags": ["spiritual", "temple", "culture", "history"], "lat": 25.2855, "lng": 82.9995,
        "fatigue_score_base": 2, "morale_score_base": 7, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "An 18th-century temple built in Nagara style, painted bright red, featuring a sacred water tank.",
        "opening_hours": ["Monday-Sunday: 05:00-22:00"], "skip_if": "If you are trying to avoid crowded temple queues.",
        "insider_tip": "Tuesdays and Saturdays are particularly busy. Combine with a visit to Tulsi Manas temple next door.",
        "confidence_pct": 96
    },
    {
        "activity_id": "galis_walk_varanasi_15", "destination": "Varanasi", "name": "Varanasi Old City Alleyways Walk",
        "category": "cultural", "duration_minutes": 120, "cost_per_person": 0,
        "available_slots": ["09:00", "15:00", "16:30"], "risk_level": "low",
        "tags": ["heritage", "walking", "alleyways", "local"], "lat": 25.3110, "lng": 83.0110,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "moderate",
        "editorial_summary": "Navigate the labyrinth of narrow, ancient alleys containing small shrines, cow stalls, and hidden shops.",
        "opening_hours": ["Monday-Sunday: 24 Hours"], "skip_if": "If you have walking difficulties or struggle with intense sensory inputs.",
        "insider_tip": "Keep your map app open, but don't hesitate to ask locals for directions to the nearest 'ghat' if lost.",
        "confidence_pct": 94
    },
    {
        "activity_id": "alaknanda_cruise_varanasi_16", "destination": "Varanasi", "name": "Alaknanda Luxury River Cruise",
        "category": "experience", "duration_minutes": 90, "cost_per_person": 900,
        "available_slots": ["16:30"], "risk_level": "low",
        "tags": ["experience", "cruise", "boat", "luxury", "sunset"], "lat": 25.3050, "lng": 83.0150,
        "fatigue_score_base": 1, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "An air-conditioned double-decker luxury cruise boat sailing past Varanasi's historic ghats.",
        "opening_hours": ["Monday-Sunday: 16:30-18:00"], "skip_if": "Monsoons, when high waters halt all cruise ships.",
        "insider_tip": "Book at least 2 weeks in advance online, as tickets for the sunset slot are highly sought after.",
        "confidence_pct": 95
    },
    {
        "activity_id": "chunar_fort_varanasi_17", "destination": "Varanasi", "name": "Chunar Fort Heritage Day Trip",
        "category": "cultural", "duration_minutes": 240, "cost_per_person": 200,
        "available_slots": ["09:00"], "risk_level": "low",
        "tags": ["heritage", "fort", "history", "scenic"], "lat": 25.1233, "lng": 82.8833,
        "fatigue_score_base": 5, "morale_score_base": 7, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "moderate",
        "editorial_summary": "A historic fort situated on the banks of the Ganges, featuring links to king Vikramaditya and Sher Shah Suri.",
        "opening_hours": ["Monday-Sunday: 09:00-17:00"], "skip_if": "If you are on a tight schedule (it takes 1.5 hours to reach from Varanasi).",
        "insider_tip": "Explore the sundial and the prison cells inside the fort complex. Carry your own lunch/water.",
        "confidence_pct": 90
    },
    {
        "activity_id": "dhamek_stupa_varanasi_18", "destination": "Varanasi", "name": "Dhamek Stupa Pilgrimage Site",
        "category": "spiritual", "duration_minutes": 60, "cost_per_person": 25,
        "available_slots": ["08:00", "11:00", "15:00"], "risk_level": "low",
        "tags": ["spiritual", "stupa", "buddhism", "heritage"], "lat": 25.3800, "lng": 83.0240,
        "fatigue_score_base": 2, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "A massive, cylindrical stone stupa built by Emperor Ashoka to mark where Buddha preached his first sermon.",
        "opening_hours": ["Monday-Sunday: 06:00-18:00"], "skip_if": "Low light, as the intricate floral carvings on stone look best in sunshine.",
        "insider_tip": "Walk clockwise around the stupa following Buddhist custom for meditation.",
        "confidence_pct": 98
    },
    {
        "activity_id": "museum_sarnath_varanasi_19", "destination": "Varanasi", "name": "Sarnath Archaeological Museum",
        "category": "cultural", "duration_minutes": 90, "cost_per_person": 5,
        "available_slots": ["09:00", "11:00", "14:00", "15:30"], "risk_level": "low",
        "tags": ["museum", "archaeology", "history", "buddhism"], "lat": 25.3755, "lng": 83.0215,
        "fatigue_score_base": 2, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "The oldest site museum of the Archaeological Survey of India, housing stunning Buddhist sculptures.",
        "opening_hours": ["Saturday-Thursday: 09:00-17:00"], "skip_if": "Fridays, when the museum is closed.",
        "insider_tip": "Do not miss the 3rd-century BC Ashoka pillar capital, which is the national emblem of India.",
        "confidence_pct": 98
    },
    {
        "activity_id": "bharat_mata_varanasi_20", "destination": "Varanasi", "name": "Bharat Mata Temple Map Visit",
        "category": "cultural", "duration_minutes": 45, "cost_per_person": 20,
        "available_slots": ["09:30", "12:00", "15:00", "16:30"], "risk_level": "low",
        "tags": ["heritage", "map", "history", "patriotic"], "lat": 25.3168, "lng": 82.9890,
        "fatigue_score_base": 2, "morale_score_base": 6, "best_time_of_day": "morning",
        "best_season": ["Oct-Mar"], "accessibility": "easy",
        "editorial_summary": "An unusual temple dedicated to Mother India, featuring a relief map of the country carved in marble.",
        "opening_hours": ["Monday-Sunday: 09:30-20:00"], "skip_if": "If you expect traditional idols, as there are no statues of gods here.",
        "insider_tip": "Check the high detail of mountain ranges and major rivers carved dynamically in white marble.",
        "confidence_pct": 97
    }
]
activities.extend(varanasi_activities)

# --- RISHIKESH (5 Activities) ---
rishikesh_activities = [
    {
        "activity_id": "rafting_rishikesh_01", "destination": "Rishikesh", "name": "White Water Rafting (16 km)",
        "category": "adventure", "duration_minutes": 180, "cost_per_person": 1800,
        "available_slots": ["09:00", "12:00", "14:00"], "risk_level": "medium",
        "tags": ["adventure", "rafting", "water", "outdoor", "friends"], "lat": 30.1159, "lng": 78.3127,
        "fatigue_score_base": 8, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Sep-Jun"], "accessibility": "moderate",
        "editorial_summary": "Raft down the roaring rapids of the holy Ganges with experienced guides.",
        "opening_hours": ["Monday-Sunday: 08:00-16:00"], "skip_if": "Monsoons, when river is flooded and rafting is banned.",
        "insider_tip": "Wear quick-dry clothes and strap your sandals securely; the rapids can be powerful.",
        "confidence_pct": 95
    },
    {
        "activity_id": "ganga_aarti_rishikesh_01", "destination": "Rishikesh", "name": "Parmarth Niketan Ganga Aarti",
        "category": "spiritual", "duration_minutes": 60, "cost_per_person": 0,
        "available_slots": ["18:30", "19:00"], "risk_level": "low",
        "tags": ["spiritual", "aarti", "ganga", "evening", "culture"], "lat": 30.1354, "lng": 78.3207,
        "fatigue_score_base": 3, "morale_score_base": 8, "best_time_of_day": "evening",
        "best_season": ["Sep-Jun"], "accessibility": "easy",
        "editorial_summary": "A peaceful sunset devotional ceremony with prayers and lamps on the river bank.",
        "opening_hours": ["Monday-Sunday: 18:00-19:30"], "skip_if": "None; a quiet and sacred experience.",
        "insider_tip": "Sit on the steps near the huge Shiva statue for the best views.",
        "confidence_pct": 98
    },
    {
        "activity_id": "beatles_ashram_rishikesh_01", "destination": "Rishikesh", "name": "Beatles Ashram (Chaurasi Kutia)",
        "category": "cultural", "duration_minutes": 90, "cost_per_person": 150,
        "available_slots": ["09:00", "10:00", "14:00", "15:00"], "risk_level": "low",
        "tags": ["heritage", "ashram", "art", "photography", "history"], "lat": 30.1249, "lng": 78.3215,
        "fatigue_score_base": 4, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Sep-Jun"], "accessibility": "moderate",
        "editorial_summary": "The ruins of Maharishi Mahesh Yogi's ashram, where the Beatles stayed in 1968.",
        "opening_hours": ["Monday-Sunday: 09:00-16:30"], "skip_if": "Rainy weather.",
        "insider_tip": "Check out the colorful murals painted inside the meditation hall.",
        "confidence_pct": 97
    },
    {
        "activity_id": "bungee_rishikesh_01", "destination": "Rishikesh", "name": "Bungee Jumping (83m)",
        "category": "adventure", "duration_minutes": 60, "cost_per_person": 3550,
        "available_slots": ["09:30", "11:00", "13:00", "15:00"], "risk_level": "high",
        "tags": ["adventure", "bungee", "extreme", "outdoor", "thrill"], "lat": 30.0986, "lng": 78.3947,
        "fatigue_score_base": 8, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Sep-Jun"], "accessibility": "moderate",
        "editorial_summary": "Jump from a fixed platform over a rocky river tributary, India's highest jump point.",
        "opening_hours": ["Wednesday-Monday: 09:00-16:00"], "skip_if": "High wind, rain, or if you have heart conditions.",
        "insider_tip": "Book online in advance as slots are limited to 100 jumpers per day.",
        "confidence_pct": 99
    },
    {
        "activity_id": "cafe_hopping_rishikesh_01", "destination": "Rishikesh", "name": "Lakshman Jhula Cafe Hopping",
        "category": "food", "duration_minutes": 90, "cost_per_person": 500,
        "available_slots": ["10:00", "11:00", "15:00", "16:00", "17:00"], "risk_level": "low",
        "tags": ["cafes", "food", "river_view", "relaxed", "instagram"], "lat": 30.1256, "lng": 78.3152,
        "fatigue_score_base": 2, "morale_score_base": 6, "best_time_of_day": "afternoon",
        "best_season": ["Sep-Jun"], "accessibility": "easy",
        "editorial_summary": "Relax in multi-cuisine cafes overlooking the Ganges next to the historic suspension bridge.",
        "opening_hours": ["Monday-Sunday: 09:00-22:00"], "skip_if": "None; great spot for lazy afternoons.",
        "insider_tip": "Order ginger-lemon tea and chocolate pancakes at Freedom Cafe.",
        "confidence_pct": 96
    }
]
activities.extend(rishikesh_activities)

# --- TIRTHAN VALLEY (5 Activities) ---
tirthan_activities = [
    {
        "activity_id": "ghnp_trek_tirthan_01", "destination": "Tirthan Valley", "name": "Great Himalayan NP Day Trek",
        "category": "adventure", "duration_minutes": 360, "cost_per_person": 1200,
        "available_slots": ["06:00", "07:00"], "risk_level": "medium",
        "tags": ["trekking", "wildlife", "forest", "nature", "himalaya"], "lat": 31.75, "lng": 77.52,
        "fatigue_score_base": 8, "morale_score_base": 9, "best_time_of_day": "morning",
        "best_season": ["Mar-Jun", "Oct-Nov"], "accessibility": "difficult",
        "editorial_summary": "A guided trek through alpine meadows and pristine rivers in a UNESCO-protected park.",
        "opening_hours": ["Monday-Sunday: 06:00-18:00"], "skip_if": "Heavy snow in winter or monsoons.",
        "insider_tip": "Obtain entry permits at the Sai Ropa office before starting.",
        "confidence_pct": 98
    },
    {
        "activity_id": "trout_fishing_tirthan_01", "destination": "Tirthan Valley", "name": "Trout Fishing in Tirthan River",
        "category": "nature", "duration_minutes": 180, "cost_per_person": 800,
        "available_slots": ["07:00", "08:00", "14:00"], "risk_level": "low",
        "tags": ["fishing", "river", "nature", "peaceful", "local_experience"], "lat": 31.6381, "lng": 77.4511,
        "fatigue_score_base": 6, "morale_score_base": 4, "best_time_of_day": "morning",
        "best_season": ["Mar-Oct"], "accessibility": "easy",
        "editorial_summary": "Cast a line in the crystal-clear Tirthan River, famous for brown and rainbow trout.",
        "opening_hours": ["Monday-Sunday: 07:00-18:00"], "skip_if": "None; highly relaxing.",
        "insider_tip": "A fishing permit from the local fisheries department is required.",
        "confidence_pct": 97
    },
    {
        "activity_id": "waterfall_hike_tirthan_01", "destination": "Tirthan Valley", "name": "Chhoie Waterfall Hike",
        "category": "nature", "duration_minutes": 240, "cost_per_person": 0,
        "available_slots": ["08:00", "09:00", "10:00"], "risk_level": "low",
        "tags": ["waterfall", "hiking", "nature", "scenic", "photography"], "lat": 31.59, "lng": 77.42,
        "fatigue_score_base": 8, "morale_score_base": 8, "best_time_of_day": "morning",
        "best_season": ["Oct-Jun"], "accessibility": "moderate",
        "editorial_summary": "A short, steep hike from Gushaini village to a hidden, sacred waterfall.",
        "opening_hours": ["Monday-Sunday: 06:00-18:00"], "skip_if": "Heavy rainfall makes path muddy.",
        "insider_tip": "The water is freezing but crystal clear; carry dry clothes if you plan to wade in.",
        "confidence_pct": 98
    },
    {
        "activity_id": "village_walk_tirthan_01", "destination": "Tirthan Valley", "name": "Gushaini Village Cultural Walk",
        "category": "cultural", "duration_minutes": 90, "cost_per_person": 0,
        "available_slots": ["09:00", "10:00", "15:00", "16:00"], "risk_level": "low",
        "tags": ["culture", "village", "local_life", "photography", "himachali"], "lat": 31.61, "lng": 77.43,
        "fatigue_score_base": 4, "morale_score_base": 4, "best_time_of_day": "morning",
        "best_season": ["Oct-Jun"], "accessibility": "easy",
        "editorial_summary": "Walk through quiet apple orchards and traditional wooden houses in a quiet village.",
        "opening_hours": ["Monday-Sunday: 24 Hours"], "skip_if": "None; highly pleasant.",
        "insider_tip": "Talk to locals; they are extremely friendly and often offer tea.",
        "confidence_pct": 98
    },
    {
        "activity_id": "stargazing_tirthan_01", "destination": "Tirthan Valley", "name": "Jalori Pass Stargazing",
        "category": "nature", "duration_minutes": 120, "cost_per_person": 0,
        "available_slots": ["20:00", "21:00"], "risk_level": "low",
        "tags": ["stargazing", "astronomy", "night", "scenic", "offbeat"], "lat": 31.72, "lng": 77.39,
        "fatigue_score_base": 6, "morale_score_base": 8, "best_time_of_day": "night",
        "best_season": ["Oct-Jun"], "accessibility": "moderate",
        "editorial_summary": "Observe the clear night sky at 10,000 feet from Jalori Pass ridge.",
        "opening_hours": ["Monday-Sunday: 24 Hours"], "skip_if": "Cloudy night skies.",
        "insider_tip": "Bring heavy woolens; temperatures drop drastically at night.",
        "confidence_pct": 96
    }
]
activities.extend(tirthan_activities)
