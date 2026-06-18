// Hardcoded mock responses matching API contracts exactly.
// Used as fallback when the backend is unavailable.

export const MOCK_PARSE_CHAT = {
  extracted_constraints: {
    origin: "Gurugram",
    destination: null,
    destination_type: "mountains",
    budget_per_person: 15000,
    dates: null,
    trip_duration: "weekend",
    transport_preference: ["cab_with_driver"],
    avoid_night_driving: true,
    must_include: ["rafting", "cafes"],
    return_deadline: "Monday morning",
    hotel_tier: "comfort",
    risk_tolerance: "medium",
    group_size: 4,
    special_requirements: [],
  },
  missing_fields: [],
  assumptions: {
    group_size: "4 (default)",
    risk_tolerance: "medium (default)",
  },
  conflict_report: { has_conflicts: false, conflicts: [] },
};

export const MOCK_ITINERARY = {
  recommended_itinerary: {
    route: {
      route_id: "gurugram_rishikesh_2d1n",
      origin: "Gurugram",
      destination: "Rishikesh",
      distance_km: 260,
      destination_type: "mountains",
    },
    transport: { mode: "cab_with_driver", tier: "comfort", cost_total: 9500 },
    hotel: { name: "Riverside Comfort Stay", price_per_night: 4200, comfort_score: 8 },
    activities: [
      { name: "White Water Rafting (16 km)", cost_per_person: 1800, category: "adventure" },
      { name: "Ganga Aarti at Triveni Ghat", cost_per_person: 0, category: "spiritual" },
      { name: "Lakshman Jhula Cafe Hopping", cost_per_person: 500, category: "food" },
    ],
    total_cost_per_person: 10275,
    destination: "Rishikesh",
    cost_breakdown: {
      transport: 2375,
      hotel: 1050,
      activities: 1800,
      food: 1050,
      miscellaneous: 2000,
      total: 10275,
    },
  },
  alternatives: [
    {
      route: { route_id: "gurugram_tirthan_3d2n", destination: "Tirthan Valley", distance_km: 510 },
      transport: { mode: "cab_with_driver", tier: "comfort" },
      hotel: { name: "WhiteBridge Nature Resort" },
      total_cost_per_person: 14500,
      destination: "Tirthan Valley",
    },
  ],
  validation_report: {
    is_valid: true,
    hard_constraint_violations: [],
    soft_constraint_warnings: [],
  },
  score_breakdown: {
    preference_match: 25,
    budget_efficiency: 6.3,
    comfort: 12,
    scenic: 7,
    fatigue: 10.5,
    risk: 6,
    night_driving_penalty: 0,
    final_score: 66.8,
  },
  timeline: [
    { day: 1, start_time: "06:00", end_time: "09:00", title: "Drive from Gurugram", type: "travel" },
    { day: 1, start_time: "09:00", end_time: "09:45", title: "Breakfast at Murthal Dhaba", type: "meal", cost: 250 },
    { day: 1, start_time: "09:45", end_time: "13:00", title: "Continue to Rishikesh", type: "travel" },
    { day: 1, start_time: "13:00", end_time: "14:15", title: "Lunch at Little Buddha Cafe", type: "meal", cost: 600 },
    { day: 1, start_time: "14:30", end_time: "16:00", title: "Check-in & Rest at Riverside Comfort Stay", type: "hotel", cost: 1050 },
    { day: 1, start_time: "16:30", end_time: "17:30", title: "Lakshman Jhula Cafe Hopping", type: "activity", cost: 500 },
    { day: 1, start_time: "18:30", end_time: "19:30", title: "Ganga Aarti at Triveni Ghat", type: "activity", cost: 0 },
    { day: 1, start_time: "20:00", end_time: "21:00", title: "Dinner", type: "meal", cost: 500 },
    { day: 2, start_time: "07:30", end_time: "08:15", title: "Breakfast at Hotel", type: "meal", cost: 200 },
    { day: 2, start_time: "09:00", end_time: "12:00", title: "White Water Rafting (16 km)", type: "activity", cost: 1800 },
    { day: 2, start_time: "12:30", end_time: "13:30", title: "Freshen Up", type: "rest" },
    { day: 2, start_time: "13:30", end_time: "14:30", title: "Lunch", type: "meal", cost: 500 },
    { day: 2, start_time: "15:00", end_time: "21:30", title: "Return Drive to Gurugram", type: "travel" },
  ],
  map_points: [
    { lat: 28.4595, lng: 77.0266, label: "Gurugram", type: "origin" },
    { lat: 29.0281, lng: 77.0474, label: "Murthal Dhaba Belt", type: "waypoint" },
    { lat: 30.0869, lng: 78.2676, label: "Rishikesh", type: "destination" },
    { lat: 30.0869, lng: 78.2676, label: "Riverside Comfort Stay", type: "hotel" },
    { lat: 30.1159, lng: 78.3127, label: "White Water Rafting", type: "activity" },
    { lat: 30.1050, lng: 78.2950, label: "Ganga Aarti", type: "activity" },
  ],
  cost_breakdown: {
    transport: 2375,
    hotel: 1050,
    activities: 1800,
    food: 1050,
    miscellaneous: 2000,
    total: 10275,
    budget_limit: 15000,
  },
  explanation:
    "This itinerary was selected because it stays within the ₹15,000 budget at ₹10,275 per person, avoids night driving on both legs, includes white water rafting and riverside cafe hopping as requested, and returns to Gurugram by 9:30 PM Sunday — well before Monday morning.",
};

export const MOCK_DELAY = {
  updated_itinerary: {
    ...MOCK_ITINERARY.recommended_itinerary,
    total_cost_per_person: 10275,
  },
  changes: [
    "Departure delayed from 06:00 to 07:30",
    "Breakfast shortened from 45 min to 25 min",
    "Rest period reduced from 90 min to 45 min",
    "Cafe hopping removed to save time",
  ],
  validation_report: {
    is_valid: true,
    hard_constraint_violations: [],
    soft_constraint_warnings: ["Rest time below recommended minimum"],
  },
  explanation:
    "The 90-minute departure delay was absorbed by compressing flexible events. Breakfast was shortened, the rest period was halved, and riverside cafe hopping was removed. Rafting, Ganga Aarti, and the return deadline are all preserved.",
};
