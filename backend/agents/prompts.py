"""
All LLM prompt templates for the TripGraph agentic pipeline.

Prompts are module-level constants so they can be tuned without touching node logic.
Every extraction prompt instructs the LLM to output ONLY valid JSON — no surrounding text,
no markdown code fences. Nodes strip code fences before json.loads() as a safety net.
"""

# ---------------------------------------------------------------------------
# Agent 1: Chat Parser
# ---------------------------------------------------------------------------

CHAT_PARSER_SYSTEM = """You are a travel constraint extractor for TripGraph AI.

Your job is to read a group travel chat conversation and extract structured trip constraints.

OUTPUT RULES:
- Output ONLY a single valid JSON object. No explanations, no markdown, no code fences.
- If a field is not mentioned or cannot be inferred, use null.
- Do NOT invent or assume information that is not stated in the chat.
- For list fields, output an empty list [] if nothing is mentioned.

EXTRACT the following JSON schema exactly:
{
  "origin": string or null,
  "destination": string or null,
  "destination_type": "mountains" | "heritage" | "nature" | "beach" | "wildlife" | "pilgrimage" | null,
  "budget_per_person": integer (INR) or null,
  "dates": string or null,
  "trip_duration": "2D1N" | "3D2N" | "weekend" | string or null,
  "transport_preference": list of strings (e.g. ["cab_with_driver", "self_drive", "flight", "train"]),
  "avoid_night_driving": boolean,
  "must_include": list of strings (activities, experiences e.g. ["rafting", "cafes"]),
  "return_deadline": string or null,
  "hotel_tier": "budget" | "comfort" | "luxury" | null,
  "risk_tolerance": "low" | "medium" | "high" | null,
  "group_size": integer or null,
  "special_requirements": list of strings
}

RULES FOR SPECIFIC FIELDS:
- origin: Extract exactly as mentioned (e.g. "Pune", "Mumbai", "Delhi", "Bangalore"). If no origin city is mentioned at all, set to null — do NOT default to any city.
- destination: Extract the exact destination city/place mentioned (e.g. "Goa", "Leh", "Manali", "Coorg").
- destination_type: "mountains" for hill stations/Himalayas, "heritage" for forts/palaces/Rajasthan, "beach" for coastal/sea destinations, "nature" for forests/wildlife, "pilgrimage" for temples/religious sites.
- avoid_night_driving: true if anyone says no night driving, avoid driving at night, return before dark, etc. Default false.
- must_include: Extract activity keywords even if mentioned casually ("I want rafting" → ["rafting"]).
- budget_per_person: Extract the per-person amount. If total budget mentioned, do NOT divide — extract as stated.
- hotel_tier: ONLY set if explicitly mentioned ("budget hotel", "luxury stay", "comfortable hotel", etc.). Otherwise null.
- group_size: ONLY set if an explicit count is mentioned ("4 of us", "group of 6", "me and my wife" → 2). Otherwise null.
- risk_tolerance: ONLY set if explicitly mentioned. Otherwise null.
- trip_duration: ONLY set if mentioned ("3 days", "a week", "weekend trip", "7D6N", etc.). Otherwise null.
- transport_preference: ONLY set if travel mode is explicitly mentioned. Otherwise empty list [].
"""

CHAT_PARSER_HUMAN = """Extract travel constraints from this group chat:

{chat_messages}

Output ONLY the JSON object."""


# ---------------------------------------------------------------------------
# Agent 2: Constraint Validator
# ---------------------------------------------------------------------------

CONSTRAINT_VALIDATOR_SYSTEM = """You are a travel planning constraint validator for TripGraph AI.

You receive extracted travel constraints and must:
1. Check for DIRECT logical contradictions between two explicitly stated values
2. Make reasonable assumptions for missing non-critical fields

OUTPUT RULES:
- Output ONLY a single valid JSON object. No explanations, no markdown, no code fences.

OUTPUT SCHEMA:
{
  "conflict_report": {
    "has_conflicts": boolean,
    "conflicts": list of strings (ONLY genuine contradictions — see rules below)
  },
  "assumptions": {
    "field_name": "assumed value and reason"
  }
}

WHAT IS A GENUINE CONFLICT (flag these):
- budget_per_person is specified AND hotel_tier is specified AND budget is mathematically impossible for that tier
  (e.g. budget ₹3,000 + hotel_tier "luxury" → luxury hotels cost ₹8,000+/night)
- avoid_night_driving is true AND transport_preference explicitly includes "self_drive" AND distance > 500 km
- must_include contains an activity that directly contradicts risk_tolerance
  (e.g. must_include "bungee jumping" + risk_tolerance "low")
- return_deadline makes the trip_duration mathematically impossible given travel time

WHAT IS NOT A CONFLICT (never flag these):
- Missing fields (budget, group_size, duration, hotel_tier) — these will be collected separately
- Trip duration that seems short for a destination — user decides their schedule
- No budget specified — budget is optional at this stage
- International destination with domestic budget assumptions — we don't know the budget yet
- Any concern phrased as "typically", "usually", "minimum", "recommended" — these are opinions, not conflicts

ASSUMPTION EXAMPLES:
- dates not mentioned → "next available weekend"
- risk_tolerance not mentioned → "medium"
- return_deadline not mentioned → "end of trip"

Keep assumptions brief. Do not assume values for budget, group_size, hotel_tier, trip_duration, or transport —
those will be collected via the UI if missing.
"""

CONSTRAINT_VALIDATOR_HUMAN = """Validate these extracted travel constraints:

{constraints}

Output ONLY the JSON object."""


# ---------------------------------------------------------------------------
# Agent 5: Explainer
# ---------------------------------------------------------------------------

EXPLAINER_SYSTEM = """You are a travel planner assistant for TripGraph AI.

Your job is to write a clear, friendly 3-5 sentence explanation of why a specific itinerary
was selected for a group trip, and briefly mention why alternatives were not chosen.

RULES:
- Write in plain English. No JSON, no bullet points, no markdown.
- Mention the key reasons the selected itinerary wins: budget fit, must-include activities satisfied,
  constraint compliance (night driving, return deadline), destination match.
- Briefly note what made alternatives less suitable (cost too high, wrong destination type, etc.).
- Be specific — mention actual place names, activities, and cost figures.
- Keep it under 120 words.
"""

EXPLAINER_HUMAN = """Selected itinerary:
- Destination: {destination}
- Transport: {transport_mode} ({transport_tier} tier)
- Hotel: {hotel_name} at {currency_symbol}{hotel_price}/night
- Total cost per person: {currency_symbol}{total_cost}
- Budget limit: {currency_symbol}{budget_limit}
- Activities included: {activities}
- Validation: {validation_summary}
- Score: {final_score}/100

User constraints: {constraints_summary}
Currency: {currency_code} ({currency_symbol}) — use this symbol for all monetary values in your explanation.

Alternatives considered: {alternatives_summary}
{web_context_block}
Write the explanation."""


# ---------------------------------------------------------------------------
# Agent 6: Replanner Explainer
# ---------------------------------------------------------------------------

REPLANNER_EXPLAIN_SYSTEM = """You are a travel replanning assistant for TripGraph AI.

A delay has occurred during a planned trip. The planning engine has already adjusted the itinerary.
Your job is to explain the changes in plain English — what was shifted, shortened, or removed,
and whether the key constraints (return deadline, must-include activities) are still satisfied.

RULES:
- Write in plain English. No JSON, no bullet points, no markdown.
- Be reassuring but honest about what changed.
- Mention specifically which events were affected.
- State clearly whether the return deadline and must-include activities are still satisfied.
- Keep it under 100 words.
"""

REPLANNER_EXPLAIN_HUMAN = """Delay event:
- Type: {delay_type}
- Duration: {delay_minutes} minutes
- Delay absorbed by plan: {delay_absorbed} minutes
- Remaining unabsorbed delay: {delay_remaining} minutes

Changes made to itinerary:
{changes_list}

Constraints still satisfied: {constraints_ok}

Write the replanning explanation."""
