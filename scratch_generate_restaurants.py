# Restaurants seed data list
restaurants = []

def add_restaurant(destination, name, cuisine, meal_types, avg_cost, avg_dur, tags, lat, lng, signature, tip, route_id=None, km=None, confidence=90):
    r_id = f"{name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('&', 'and').replace(',', '')}_{len(restaurants) + 1:03d}"
    restaurants.append({
        "restaurant_id": r_id[:35],
        "destination": destination,
        "route_id": route_id,
        "name": name,
        "cuisine": cuisine,
        "meal_types": meal_types,
        "avg_cost_per_person": avg_cost,
        "avg_duration_minutes": avg_dur,
        "tags": tags,
        "lat": lat,
        "lng": lng,
        "signature_dish": signature,
        "insider_tip": tip,
        "km_from_origin": km,
        "confidence_pct": confidence,
        "verification_status": "llm_generated",
        "data_source": "llm_knowledge",
        "last_verified": "2026-06-22"
    })

# --- GOA ---
add_restaurant("Goa", "Curlies Beach Shack", "Goan Seafood", ["lunch", "dinner"], 800, 90, ["shack", "beachfront", "seafood", "alcohol"], 15.5714, 73.7428, "Pork Vindaloo, Butter Garlic Calamari", "Get a table on the upper deck around 5:30 PM for a spectacular sunset view with your dinner.")
add_restaurant("Goa", "The Fisherman's Wharf (Cavelossim)", "Seafood", ["lunch", "dinner"], 1200, 100, ["riverside", "seafood", "live_music"], 15.1764, 73.9422, "Tandoori Red Snapper, Goan Fish Curry", "Ask for a river-facing deck table; they have live bands playing retro English pop on weekends.")
add_restaurant("Goa", "Gunpowder (Assagao)", "South Indian Fusion", ["lunch", "dinner"], 1000, 80, ["boutique_garden", "fusion", "cocktails"], 15.5942, 73.7915, "Kerala Beef Fry, Malabar Parotta", "It is located inside a beautiful old heritage villa courtyard. Reservations are mandatory for dinner.")
add_restaurant("Goa", "Mum's Kitchen (Panaji)", "Traditional Goan", ["lunch", "dinner"], 1400, 90, ["heritage", "traditional", "family"], 15.4955, 73.8180, "Prawn Curry Rice, Bebinca", "This place preserves traditional family recipes from Hindu and Catholic Goan homes. Try the lobster curry.")
add_restaurant("Goa", "Vinayak Family Restaurant (Anjuna)", "Goan Local", ["lunch", "dinner"], 450, 60, ["local", "budget", "fish_thali"], 15.5788, 73.7553, "Goan Special Fish Thali", "Expect long queues during lunch hours. The fish thali is incredibly fresh and is the cheapest in North Goa.")

# --- JAIPUR ---
add_restaurant("Jaipur", "LMB (Laxmi Misthan Bhandar)", "Rajasthani Vegetarian", ["breakfast", "lunch", "dinner"], 500, 60, ["vegetarian", "heritage", "famous", "must_visit"], 26.9234, 75.8260, "Dal Baati Churma, Special Ghevar", "Skip the busy ground floor sweet counter and go upstairs to the AC restaurant for their grand Rajasthani Thali.")
add_restaurant("Jaipur", "Chokhi Dhani Dining", "Traditional Rajasthani", ["dinner"], 900, 90, ["rajasthani_cuisine", "thali", "cultural_experience"], 26.7910, 75.7573, "Sangri Ki Sabzi, Bajra Roti with Ghee", "Go early (by 6:30 PM) to explore the cultural village show before sitting down for the massive thali meal.")
add_restaurant("Jaipur", "Tapri Central", "Modern Cafe & Chai", ["breakfast", "lunch"], 300, 45, ["cafe", "chai", "rooftop", "youth_favourite"], 26.9156, 75.7890, "Cutting Chai, Maggi, Garlic Bread", "Snag a seat on the rooftop balcony looking over Central Park around sunset; their hibiscus tea is lovely.")
add_restaurant("Jaipur", "Rawat Mishthan Bhandar", "Indian Fast Food", ["breakfast", "lunch"], 200, 30, ["street_food", "kachori", "famous"], 26.9205, 75.7953, "Pyaaz Kachori, Mawa Kachori", "Perfect spot for a heavy local breakfast. The Pyaaz Kachoris are fried fresh every 15 minutes; eat them piping hot.")
add_restaurant("Jaipur", "Baradari Restaurant (City Palace)", "Royal Fusion", ["lunch", "dinner"], 1500, 90, ["luxury", "palace_dining", "fusion"], 26.9262, 75.8239, "Laal Maas, Smoked Lal Maas Pizza", "Beautifully designed contemporary restaurant inside the City Palace courtyard; spectacular under soft evening lights.")

# --- VARANASI ---
add_restaurant("Varanasi", "Kashi Chat Bhandar", "Banarasi Street Food", ["lunch", "dinner"], 150, 40, ["street_food", "local", "famous"], 25.3085, 83.0088, "Tamatar Chaat, Palak Patta Chaat", "The tamatar chaat is served in small clay pots with thick sugar syrup and ghee. Be ready to eat while standing.")
add_restaurant("Varanasi", "Deena Chat Bhandar", "Banarasi Street Food", ["lunch", "dinner"], 150, 40, ["street_food", "local", "budget"], 25.3122, 83.0065, "Gol Gappe, Dahi Bhalla", "A clean and historic street food outlet. Their Kulfi Falooda is the perfect way to end a spicy chaat tasting.")
add_restaurant("Varanasi", "Pizzeria Vaatika Cafe (Assi Ghat)", "Italian & Bakery", ["breakfast", "lunch", "dinner"], 550, 60, ["cafe", "river_view", "woodfire", "must_visit"], 25.2902, 83.0072, "Woodfire Margherita Pizza, Apple Pie with Ice Cream", "Kolkata and Banaras travellers love their outdoor garden seating facing the Ganges. The apple pie is freshly baked daily.")
add_restaurant("Varanasi", "Blue Lassi Shop", "Sweet Yogurt Drinks", ["breakfast", "lunch", "dinner"], 120, 30, ["lassi", "famous", "street_stall"], 25.3115, 83.0118, "Pomegranate-Chocolate Lassi, Mango Rabri Lassi", "Sit on the tiny wooden benches inside this 100-year-old shop and look at the hundreds of passport photos pasted on the walls.")
add_restaurant("Varanasi", "Brown Bread Bakery", "Organic & German Bakery", ["breakfast", "lunch", "dinner"], 450, 75, ["bakery", "rooftop", "organic", "western_food"], 25.3090, 83.0110, "German Rye Bread, Organic Cheese Platter", "Great rooftop cafe for western travelers looking for a clean, organic breakfast. They have live classical music every night.")

# --- MUNNAR ---
add_restaurant("Munnar", "Rapsy Restaurant (Munnar Bazaar)", "Kerala Local & Biryani", ["lunch", "dinner"], 250, 45, ["budget", "local", "famous"], 10.0885, 77.0600, "Spanish Omelette, Beef Fry with Parotta", "This is Munnar's most famous budget joint. Try their unique Kerala beef fry or chicken biryani.")
add_restaurant("Munnar", "Saravana Bhavan (Munnar)", "South Indian Vegetarian", ["breakfast", "lunch"], 200, 30, ["vegetarian", "south_indian", "budget"], 10.0890, 77.0602, "Ghee Roast Dosa, Filter Coffee", "Go here for a reliable and quick vegetarian breakfast. The filter coffee is strong and authentic.")
add_restaurant("Munnar", "Tea Valley Restaurant", "Indian & Continental", ["lunch", "dinner"], 600, 70, ["hill_view", "resort_dining"], 10.0535, 77.0610, "Malabar Fish Curry, Tandoori Chicken Platter", "Perched inside a resort on a tea hill, offering wide dining room windows looking out over misty valleys.")

# --- LEH ---
add_restaurant("Leh", "The Tibetan Kitchen", "Tibetan & Ladakhi", ["lunch", "dinner"], 600, 80, ["garden", "traditional", "must_visit"], 34.1595, 77.5830, "Mutton Gyakok (Tibetan Hot Pot), Thenthuk", "The outdoor garden tables are beautiful. The Gyakok pot requires ordering 4 hours in advance as it is slow-cooked.")
add_restaurant("Leh", "Chopsticks Noodle Bar", "Asian Fusion", ["lunch", "dinner"], 700, 75, ["asian", "modern", "balcony"], 34.1588, 77.5828, "Phad Thai Noodles, Momos Platter", "A clean and modern restaurant on Fort Road. Sit on the balcony for a view of the street while dining.")
add_restaurant("Leh", "Gesmo Restaurant (German Bakery)", "Western & Bakery", ["breakfast", "lunch", "dinner"], 350, 60, ["bakery", "western", "yak_cheese"], 34.1590, 77.5815, "Yak Cheese Pizza, Apple Pie, Yak Burgers", "Affectionately known as the traveler's hub in Leh. Try their fresh yak cheese pizzas and walnut pies.")

# --- MUMBAI ---
add_restaurant("Mumbai", "Britannia & Co. (Ballard Estate)", "Parsi & Iranian", ["lunch"], 800, 60, ["parsi", "heritage", "famous", "must_visit"], 18.9328, 72.8390, "Berry Pulav, Sali Boti, Caramel Custard", "They are open only for lunch (11 AM to 4 PM) and are closed on Sundays. Cash only.")
add_restaurant("Mumbai", "Bademiya (Colaba)", "Mughlai Kababs", ["dinner"], 450, 45, ["street_food", "kababs", "nightlife", "famous"], 18.9228, 72.8335, "Chicken Reshmi Kabab, Baida Roti", "A legendary open-air midnight eating street spot. Eat directly off your car bonnet for the true Mumbai experience.")
add_restaurant("Mumbai", "Shree Thaker Bhojanalay (Kalbadevi)", "Gujarati Thali", ["lunch", "dinner"], 700, 75, ["vegetarian", "thali", "famous"], 18.9488, 72.8288, "Unlimited Gujarati Thali", "Tucked away in the narrow lanes of Kalbadevi, this is widely considered the absolute best Gujarati Thali in India.")

# --- BANGALORE ---
add_restaurant("Bangalore", "Vidyarthi Bhavan (Gandhi Bazaar)", "South Indian Tiffin", ["breakfast"], 150, 30, ["heritage", "dosa", "budget", "famous"], 12.9439, 77.5683, "Masala Dosa, Filter Coffee", "Expect massive queues on weekends (wait times up to 1 hour). The crispy, ghee-soaked dosas are worth the wait.")
add_restaurant("Bangalore", "Mavalli Tiffin Room (MTR - Lalbagh)", "South Indian Heritage", ["breakfast", "lunch"], 300, 60, ["heritage", "vegetarian", "must_visit"], 12.9540, 77.5850, "Rava Idli, Silver Cup Filter Coffee", "The birthplace of Rava Idli during WWII wheat shortages. The interior preserves a 1920s dining club feel.")
add_restaurant("Bangalore", "Karavalli (Gateway Hotel)", "Coastal South Indian", ["lunch", "dinner"], 1800, 90, ["luxury", "coastal", "fine_dining"], 12.9733, 77.6080, "Tiger Prawns Roast, Kori Gassi", "Dine under a beautiful old tamarind canopy tree. A premium, award-winning venue showcasing coastal food.")

# --- KOLKATA ---
add_restaurant("Kolkata", "Peter Cat (Park Street)", "Continental & Indian", ["lunch", "dinner"], 800, 75, ["heritage", "famous", "fusion", "must_visit"], 22.5488, 88.3533, "Chelo Kabab, Chicken Peach Melba", "Famous for its unique Chelom kababs served with a dollop of butter and egg yolk on rice. Long queues are standard.")
add_restaurant("Kolkata", "6 Ballygunge Place", "Authentic Bengali", ["lunch", "dinner"], 900, 90, ["bengali_cuisine", "traditional", "family"], 22.5290, 88.3712, "Kosha Mangsho (Mutton), Daab Chingri (Prawns in Coconut)", "Set inside a beautiful 100-year-old heritage bungalow. Opt for the buffet during festivals to sample 20+ local dishes.")
add_restaurant("Kolkata", "Arsalan (Park Circus)", "Mughlai Biryani", ["lunch", "dinner"], 550, 60, ["biryani", "famous", "meat"], 22.5435, 88.3653, "Kolkata Mutton Biryani (with Potato and Egg)", "Kolkata Biryani is famous for its slow-cooked soft potato. Arsalan is widely considered the king of this style.")

# --- SHILLONG ---
add_restaurant("Shillong", "Trattoria (Police Bazar)", "Local Khasi", ["lunch", "dinner"], 200, 45, ["local", "budget", "pork", "offbeat"], 25.5785, 91.8828, "Jadoh (Rice cooked in pork blood), Dohkhlieh", "A tiny, basic stall serving authentic Khasi tribal food. Not for the faint-hearted; try the pork salad.")
add_restaurant("Shillong", "Cafe Shillong (Laitumkhrah)", "Cafe & Western", ["breakfast", "lunch", "dinner"], 500, 60, ["cafe", "live_music", "youth", "burgers"], 25.5722, 91.9050, "Smoked Pork Burgers, Irish Coffee", "A cool hangout space featuring local musicians playing acoustic guitar. Great English breakfasts.")
add_restaurant("Shillong", "City Hut Family Dhaba", "Multi-Cuisine", ["lunch", "dinner"], 600, 80, ["family", "spacious", "indian"], 25.5795, 91.8842, "Tandoori Platters, Chinese Noodles", "The most popular family restaurant in Shillong, featuring a nice indoor thatch courtyard layout.")

# --- MANALI ---
add_restaurant("Manali", "Cafe 1947 (Old Manali)", "Italian & Cafe", ["lunch", "dinner"], 700, 90, ["riverside", "cafe", "live_music", "must_visit"], 32.2542, 77.1770, "Firewood Pizza, Trout Fish with Lemon Butter", "Manali's first music cafe, situated directly on the banks of the rushing Manalsu River. Great acoustic gig nights.")
add_restaurant("Manali", "Il Forno", "Italian Woodfire", ["lunch", "dinner"], 800, 80, ["heritage", "italian", "views"], 32.2490, 77.1850, "Woodfire Margherita Pizza, Lasagne", "Set in an old rustic wooden house on a hill road, offering amazing views of snowy peaks from the garden tables.")
add_restaurant("Manali", "Johnson's Cafe", "Multi-Cuisine & Bar", ["breakfast", "lunch", "dinner"], 900, 90, ["trout", "bar", "garden"], 32.2460, 77.1890, "Pan-Fried Mustard Trout Fish", "Famous for its preparation of fresh local river trout. They have a lovely green lawn and a cozy indoor fireplace.")

# --- RISHIKESH (Original & Required) ---
add_restaurant("Rishikesh", "Little Buddha Cafe", "Cafe & Italian", ["lunch", "dinner"], 600, 75, ["cafe", "river_view", "vegetarian_options", "instagram"], 30.1256, 78.3152, "Pesto Pizza, Mixed Fruit Lassi", "Get there early around sunset; seats overlooking the river are highly popular and fill up fast.")
add_restaurant("Rishikesh", "Beatrice Cafe", "Continental Cafe", ["breakfast", "lunch"], 450, 60, ["cafe", "hippie", "continental", "quick_bite", "backpacker"], 30.1271, 78.3168, "Avocado Toast, Hummus Platter", "Very popular with long-stay foreign backpackers. Relaxed, hippie ambiance.")
add_restaurant("Rishikesh", "Freedom Cafe", "Riverside Cafe", ["breakfast", "lunch", "dinner"], 500, 60, ["cafe", "river_view", "healthy_food", "yoga_crowd"], 30.1240, 78.3140, "Ginger Lemon Honey Tea, Pancakes", "Great views of Lakshman Jhula bridge from their balcony cushions.")

# --- TIRTHAN VALLEY (Original & Required) ---
add_restaurant("Tirthan Valley", "Gushaini Village Dhaba", "Himachali Cuisine", ["breakfast", "lunch", "dinner"], 300, 45, ["himachali_cuisine", "local", "simple", "homely"], 31.6100, 77.4300, "Siddu with ghee, Local dal rice", "Simple, roadside wooden dhaba serving hot and fresh local food.")
add_restaurant("Tirthan Valley", "Tirthan Trout Kitchen", "Local Fish Specialty", ["lunch", "dinner"], 550, 60, ["trout_fish", "local_specialty", "river_view", "himachali_cuisine"], 31.6381, 77.4511, "Trout Fish Tawa Fry", "The fish is caught fresh from the river daily. Highly recommended for dinner after a day trek.")

# --- HIGHWAY STOPS ---
add_restaurant(None, "Amrik Sukhdev Dhaba", "North Indian", ["breakfast", "lunch"], 250, 45, ["dhaba", "highway", "famous", "parking"], 29.0281, 77.0474, "Aloo Pyaaz Tandoori Paratha with White Butter", "Located 60km from Delhi on NH-44. It is a massive, clean highway food station with parking.", route_id="gurugram_manali_routes", km=60)
add_restaurant(None, "Surjit Dhaba Neemrana", "Rajasthani & Punjabi", ["breakfast", "lunch"], 220, 40, ["dhaba", "highway", "parking"], 27.9899, 76.3865, "Paneer Butter Masala, Missi Roti", "NH-48 highway dhaba, popular for quick lunch stops on the road to Jaipur.", route_id="gurugram_jaipur_2d1n", km=85)
add_restaurant(None, "Bilaspur Lakeview Cafe", "Himachali & Fast Food", ["lunch"], 350, 40, ["highway", "scenic", "lake_view"], 31.3400, 76.7600, "Maggi, Hot Chai, Kadhi Chawal", "NH-21 highway stop overlooking the massive Gobind Sagar lake reservoir.", route_id="gurugram_manali_routes", km=360)
add_restaurant(None, "Cheetal Grand Restaurant", "North Indian & Continental", ["breakfast", "lunch"], 350, 40, ["highway", "restaurant", "parking", "family", "ac"], 29.5833, 77.7700, "Paneer Pakoda, Filter Coffee", "Popular AC highway rest stop on the route from Delhi to Rishikesh.", route_id="gurugram_rishikesh_2d1n", km=90)
add_restaurant(None, "Shakumbari Dhaba & Restaurant", "Rajasthani & North Indian", ["lunch"], 300, 45, ["dhaba", "highway", "lunch_stop", "parking", "famous"], 27.2200, 75.8900, "Veg Jaipuri, Butter Naan", "Popular lunch stop on NH-48 between Neemrana and Jaipur.", route_id="gurugram_jaipur_2d1n", km=160)
add_restaurant(None, "Brar Dhaba Chandigarh Bypass", "Punjabi", ["breakfast", "lunch"], 280, 45, ["dhaba", "highway", "punjabi", "parking", "quick_stop"], 30.7333, 76.7794, "Dal Makhani, Stuffed Naan", "High-volume highway stop on the Chandigarh bypass road.", route_id="gurugram_manali_routes", km=250)
add_restaurant(None, "Amrik Sukhdev Rishikesh Stop", "North Indian", ["breakfast", "lunch"], 250, 45, ["dhaba", "highway", "famous", "parking"], 29.0281, 77.0474, "Tandoori Gobhi Paratha", "Same Murthal dhaba, also mapped to the Rishikesh route for testing.", route_id="gurugram_rishikesh_2d1n", km=35)
