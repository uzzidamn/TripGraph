# Task 2: Agentic AI Pipeline (LangGraph) — Mini Spec

> **Owner**: Task 2 assignee
> **Priority**: P1 — Can start Day 1 with mock tools; integrate real tools later
> **Estimated effort**: 10-14 days
> **Reference**: Read `MASTER_SPEC.md` (same folder) for full project context

---

## Overview

Your job is to build the **LangGraph-based agentic AI pipeline** that orchestrates the entire planning workflow. You implement 6 agent nodes, connect them in a state graph, design the prompt templates, and create a swappable LLM client.

The pipeline receives raw chat messages and produces a complete `TripState` containing extracted constraints, itineraries, validation reports, timelines, map points, cost breakdowns, and explanations.

### Key Principle
> The LLM handles language (extraction, explanation). Python handles math (cost, timing, validation). The planner handles optimization (graph-based itinerary construction). **Your agents coordinate these responsibilities — they do NOT calculate costs or invent data.**

---

## What You Deliver

| # | Deliverable | File |
|---|------------|------|
| 1 | LLM client (swappable) | `backend/agents/llm_client.py` |
| 2 | TripState schema | `backend/agents/state.py` |
| 3 | Prompt templates | `backend/agents/prompts.py` |
| 4 | LangGraph workflow | `backend/agents/workflow.py` |
| 5 | Chat Parser node | `backend/agents/nodes/chat_parser.py` |
| 6 | Constraint Validator node | `backend/agents/nodes/constraint_validator.py` |
| 7 | Data Retriever node | `backend/agents/nodes/data_retriever.py` |
| 8 | Planner Orchestrator node | `backend/agents/nodes/planner_orchestrator.py` |
| 9 | Explainer node | `backend/agents/nodes/explainer.py` |
| 10 | Replanner Agent node | `backend/agents/nodes/replanner_agent.py` |
| 11 | `__init__.py` files | `backend/agents/__init__.py`, `backend/agents/nodes/__init__.py` |

---

## Step-by-Step Instructions

### Step 1: Set Up the Development Environment

```bash
# From the project root
cd backend
python -m venv venv
source venv/bin/activate  # Mac/Linux

pip install langgraph langchain langchain-google-genai python-dotenv
```

Create a `.env` file in `backend/`:
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=your_api_key_here
```

Get your free Gemini API key from: https://aistudio.google.com/apikey

### Step 2: Create `llm_client.py` — Swappable LLM Factory

This is the abstraction layer that allows switching between Gemini, OpenAI, or local models by changing `.env`.

```python
"""
Swappable LLM client. Change LLM_PROVIDER and LLM_MODEL in .env to switch models.
Supported providers: gemini, openai, ollama
"""
import os
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()

def get_llm() -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0"))

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
```

### Step 3: Create `state.py` — TripState Schema

```python
"""
TripState: The shared state object passed through all LangGraph nodes.
Each node reads from and writes to this state.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph import add_messages

class TripState(TypedDict):
    # ----- Input -----
    raw_chat: List[str]

    # ----- Constraint Extraction (Chat Parser) -----
    extracted_constraints: Dict[str, Any]
    missing_fields: List[str]
    assumptions: Dict[str, str]

    # ----- Constraint Validation -----
    conflict_report: Dict[str, Any]
    is_ready_to_plan: bool

    # ----- Data Retrieval -----
    route_candidates: List[Dict[str, Any]]
    hotel_candidates: List[Dict[str, Any]]
    transport_candidates: List[Dict[str, Any]]
    activity_candidates: List[Dict[str, Any]]
    food_candidates: List[Dict[str, Any]]
    waypoint_candidates: List[Dict[str, Any]]

    # ----- Planning -----
    itinerary_candidates: List[Dict[str, Any]]
    selected_itinerary: Optional[Dict[str, Any]]
    alternative_itineraries: List[Dict[str, Any]]
    validation_report: Dict[str, Any]
    score_breakdown: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    map_points: List[Dict[str, Any]]
    cost_breakdown: Dict[str, Any]

    # ----- Explanation -----
    explanation: str

    # ----- Replanning -----
    delay_event: Optional[Dict[str, Any]]
    replanned_itinerary: Optional[Dict[str, Any]]
    replanning_explanation: Optional[str]
```

### Step 4: Create `prompts.py` — Prompt Templates

```python
"""
Prompt templates for each agent node. Keep prompts focused and structured.
"""

CHAT_PARSER_SYSTEM = """You are a travel planning assistant. Your task is to extract structured trip requirements from a group chat conversation.

Extract the following fields from the chat messages. If a field is not mentioned, set it to null.

Output ONLY valid JSON matching this schema:
{
  "origin": "string or null",
  "destination": "string or null",
  "destination_type": "mountains | heritage | nature | beach | null",
  "budget_per_person": "number or null",
  "dates": "string or null",
  "trip_duration": "string like '2D1N' or 'weekend' or null",
  "transport_preference": ["cab_with_driver", "self_drive", "bus", "train", "flight"],
  "avoid_night_driving": "boolean",
  "must_include": ["list of must-have activities"],
  "return_deadline": "string or null",
  "hotel_tier": "budget | comfort | expedition | null",
  "risk_tolerance": "low | medium | high | null",
  "group_size": "number or null",
  "special_requirements": ["list of any other requirements"]
}

Do NOT invent information. Only extract what is explicitly or strongly implied in the messages."""

CHAT_PARSER_HUMAN = """Extract trip requirements from this group chat:

{chat_messages}

Output only the JSON object, no other text."""


CONSTRAINT_VALIDATOR_SYSTEM = """You are a trip planning validator. Check whether the extracted constraints are complete enough to generate a travel plan.

Required fields (plan cannot proceed without these):
- origin
- budget_per_person OR trip_duration
- At least one preference (destination_type, must_include, or destination)

Check for conflicts:
- Budget too low for requested tier
- Destination type conflicts with specific destination
- Must-include activities not available at destination type
- Trip duration too short for requested destination

Output JSON:
{
  "is_ready": boolean,
  "missing_required": ["list of missing required fields"],
  "conflicts": [{"field1": "...", "field2": "...", "reason": "..."}],
  "suggestions": ["list of default values to assume for missing non-critical fields"]
}"""

CONSTRAINT_VALIDATOR_HUMAN = """Validate these extracted constraints:

{constraints}

Output only the JSON object."""


EXPLAINER_SYSTEM = """You are a travel planning assistant explaining why a particular itinerary was selected.

Given the user's constraints, the selected itinerary, rejected alternatives, and the validation/scoring data, write a clear, friendly 3-5 sentence explanation of:
1. Why this itinerary was chosen
2. Why alternatives were rejected
3. Any trade-offs made
4. Key highlights of the selected plan

Be specific — mention actual constraint values (budget, deadline, activities) and how the plan satisfies them."""

EXPLAINER_HUMAN = """User constraints:
{constraints}

Selected itinerary:
{selected_itinerary}

Alternatives (rejected or lower-scored):
{alternatives}

Validation report:
{validation_report}

Score breakdown:
{score_breakdown}

Write a clear explanation of why the selected itinerary was chosen."""


REPLANNER_EXPLAIN_SYSTEM = """You are explaining how a travel itinerary was adjusted after a delay.

Given the original itinerary, the delay event, and the updated itinerary, write a clear 2-4 sentence explanation of:
1. What was delayed and by how much
2. What changes were made (shifted, shortened, removed)
3. Whether all hard constraints are still satisfied
4. What was preserved despite the delay"""

REPLANNER_EXPLAIN_HUMAN = """Original itinerary:
{original_itinerary}

Delay event:
{delay_event}

Updated itinerary:
{updated_itinerary}

Changes made:
{changes}

Write a clear explanation of the replanning."""
```

### Step 5: Create Agent Nodes

Each node is a function that takes `TripState`, does its work, and returns a partial state update.

#### `nodes/chat_parser.py`
```python
"""Agent 1: Extracts structured constraints from raw group chat."""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from backend.agents.llm_client import get_llm
from backend.agents.prompts import CHAT_PARSER_SYSTEM, CHAT_PARSER_HUMAN
from backend.agents.state import TripState


def chat_parser_node(state: TripState) -> dict:
    llm = get_llm()
    chat_text = "\n".join(state["raw_chat"])

    response = llm.invoke([
        SystemMessage(content=CHAT_PARSER_SYSTEM),
        HumanMessage(content=CHAT_PARSER_HUMAN.format(chat_messages=chat_text)),
    ])

    # Parse JSON from LLM response
    try:
        constraints = json.loads(response.content)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        constraints = json.loads(content.strip())

    return {
        "extracted_constraints": constraints,
    }
```

#### `nodes/constraint_validator.py`
```python
"""Agent 2: Validates extracted constraints for completeness and conflicts."""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from backend.agents.llm_client import get_llm
from backend.agents.prompts import CONSTRAINT_VALIDATOR_SYSTEM, CONSTRAINT_VALIDATOR_HUMAN
from backend.agents.state import TripState


def constraint_validator_node(state: TripState) -> dict:
    llm = get_llm()
    constraints_str = json.dumps(state["extracted_constraints"], indent=2)

    response = llm.invoke([
        SystemMessage(content=CONSTRAINT_VALIDATOR_SYSTEM),
        HumanMessage(content=CONSTRAINT_VALIDATOR_HUMAN.format(constraints=constraints_str)),
    ])

    try:
        validation = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        validation = json.loads(content.strip())

    # Apply default assumptions for missing non-critical fields
    constraints = state["extracted_constraints"].copy()
    assumptions = {}
    if not constraints.get("hotel_tier"):
        constraints["hotel_tier"] = "comfort"
        assumptions["hotel_tier"] = "comfort (default)"
    if not constraints.get("group_size"):
        constraints["group_size"] = 4
        assumptions["group_size"] = "4 (default)"
    if not constraints.get("risk_tolerance"):
        constraints["risk_tolerance"] = "medium"
        assumptions["risk_tolerance"] = "medium (default)"

    return {
        "extracted_constraints": constraints,
        "missing_fields": validation.get("missing_required", []),
        "conflict_report": {"conflicts": validation.get("conflicts", [])},
        "assumptions": assumptions,
        "is_ready_to_plan": validation.get("is_ready", True) and len(validation.get("missing_required", [])) == 0,
    }
```

#### `nodes/data_retriever.py`
```python
"""Agent 3: Retrieves travel data from Neo4j via tool functions."""
from backend.agents.state import TripState

# Import tool functions — these are provided by Task 5 (Mainframe)
# During development, use mock versions (see mock section below)
from backend.tools.route_tool import get_routes
from backend.tools.hotel_tool import get_hotels
from backend.tools.activity_tool import get_activities
from backend.tools.transport_tool import get_transport_options
from backend.tools.restaurant_tool import get_restaurants
from backend.tools.waypoint_tool import get_waypoints


def data_retriever_node(state: TripState) -> dict:
    constraints = state["extracted_constraints"]
    origin = constraints.get("origin", "Gurugram")
    dest_type = constraints.get("destination_type")
    tier = constraints.get("hotel_tier", "comfort")

    # Step 1: Get matching routes
    routes = get_routes(origin=origin, destination_type=dest_type)

    # Step 2: For each route, get hotels, activities, transport, food
    all_hotels = []
    all_activities = []
    all_transport = []
    all_food = []
    all_waypoints = []

    for route in routes:
        destination = route["destination"]
        route_id = route["route_id"]

        hotels = get_hotels(destination=destination, tier=tier)
        all_hotels.extend(hotels)

        tags = constraints.get("must_include", [])
        activities = get_activities(destination=destination, tags=tags)
        all_activities.extend(activities)

        transport = get_transport_options(
            route_id=route_id,
            modes=constraints.get("transport_preference"),
        )
        all_transport.extend(transport)

        food = get_restaurants(destination=destination, route_id=route_id)
        all_food.extend(food)

        waypoints = get_waypoints(route_id=route_id)
        all_waypoints.extend(waypoints)

    return {
        "route_candidates": routes,
        "hotel_candidates": all_hotels,
        "transport_candidates": all_transport,
        "activity_candidates": all_activities,
        "food_candidates": all_food,
        "waypoint_candidates": all_waypoints,
    }
```

#### `nodes/planner_orchestrator.py`
```python
"""Agent 4: Coordinates the Graph Planning Engine to generate itineraries."""
from backend.agents.state import TripState

# Import planner functions — these are provided by Task 5 (Mainframe)
from backend.planner.candidate_generator import generate_candidates
from backend.planner.scorer import score_itinerary
from backend.planner.validator import validate_itinerary
from backend.planner.timeline_generator import generate_timeline


def planner_orchestrator_node(state: TripState) -> dict:
    constraints = state["extracted_constraints"]

    data = {
        "routes": state["route_candidates"],
        "hotels": state["hotel_candidates"],
        "transport": state["transport_candidates"],
        "activities": state["activity_candidates"],
        "food": state["food_candidates"],
        "waypoints": state["waypoint_candidates"],
    }

    # Step 1: Generate candidate itineraries
    candidates = generate_candidates(constraints=constraints, data=data)

    # Step 2: Score and validate each candidate
    scored_candidates = []
    for candidate in candidates:
        score = score_itinerary(itinerary=candidate, constraints=constraints)
        validation = validate_itinerary(itinerary=candidate, constraints=constraints)
        candidate["score"] = score
        candidate["validation"] = validation
        scored_candidates.append(candidate)

    # Step 3: Sort by score (valid first, then by score descending)
    valid = [c for c in scored_candidates if c["validation"]["is_valid"]]
    invalid = [c for c in scored_candidates if not c["validation"]["is_valid"]]
    valid.sort(key=lambda c: c["score"]["final_score"], reverse=True)

    selected = valid[0] if valid else scored_candidates[0]
    alternatives = (valid[1:] + invalid)[:3]

    # Step 4: Generate timeline for selected itinerary
    timeline = generate_timeline(itinerary=selected)
    map_points = _extract_map_points(selected)
    cost_breakdown = selected.get("cost_breakdown", {})

    return {
        "itinerary_candidates": scored_candidates,
        "selected_itinerary": selected,
        "alternative_itineraries": alternatives,
        "validation_report": selected["validation"],
        "score_breakdown": selected["score"],
        "timeline": timeline,
        "map_points": map_points,
        "cost_breakdown": cost_breakdown,
    }


def _extract_map_points(itinerary: dict) -> list[dict]:
    """Extract lat/lng points from itinerary for map display."""
    points = []
    # Extract from route, hotels, activities, waypoints
    # Implementation depends on itinerary structure from Task 5
    return points
```

#### `nodes/explainer.py`
```python
"""Agent 5: Generates natural language explanation of the selected plan."""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from backend.agents.llm_client import get_llm
from backend.agents.prompts import EXPLAINER_SYSTEM, EXPLAINER_HUMAN
from backend.agents.state import TripState


def explainer_node(state: TripState) -> dict:
    llm = get_llm()

    response = llm.invoke([
        SystemMessage(content=EXPLAINER_SYSTEM),
        HumanMessage(content=EXPLAINER_HUMAN.format(
            constraints=json.dumps(state["extracted_constraints"], indent=2),
            selected_itinerary=json.dumps(state["selected_itinerary"], indent=2, default=str),
            alternatives=json.dumps(state["alternative_itineraries"], indent=2, default=str),
            validation_report=json.dumps(state["validation_report"], indent=2),
            score_breakdown=json.dumps(state["score_breakdown"], indent=2),
        )),
    ])

    return {"explanation": response.content}
```

#### `nodes/replanner_agent.py`
```python
"""Agent 6: Handles delay events and adjusts the itinerary."""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from backend.agents.llm_client import get_llm
from backend.agents.prompts import REPLANNER_EXPLAIN_SYSTEM, REPLANNER_EXPLAIN_HUMAN
from backend.agents.state import TripState

# Planner function from Task 5
from backend.planner.replanner import replan_itinerary


def replanner_agent_node(state: TripState) -> dict:
    delay_event = state["delay_event"]
    original = state["selected_itinerary"]
    constraints = state["extracted_constraints"]

    # Step 1: Call deterministic replanner (Task 5)
    replan_result = replan_itinerary(
        itinerary=original,
        delay_event=delay_event,
        constraints=constraints,
    )

    # Step 2: Use LLM to explain the changes
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=REPLANNER_EXPLAIN_SYSTEM),
        HumanMessage(content=REPLANNER_EXPLAIN_HUMAN.format(
            original_itinerary=json.dumps(original, indent=2, default=str),
            delay_event=json.dumps(delay_event, indent=2),
            updated_itinerary=json.dumps(replan_result["updated_itinerary"], indent=2, default=str),
            changes=json.dumps(replan_result["changes"], indent=2),
        )),
    ])

    return {
        "replanned_itinerary": replan_result["updated_itinerary"],
        "replanning_explanation": response.content,
    }
```

### Step 6: Create `workflow.py` — LangGraph State Graph

```python
"""
Main LangGraph workflow: Orchestrates the 6 agents into a stateful pipeline.
"""
from langgraph.graph import StateGraph, START, END

from backend.agents.state import TripState
from backend.agents.nodes.chat_parser import chat_parser_node
from backend.agents.nodes.constraint_validator import constraint_validator_node
from backend.agents.nodes.data_retriever import data_retriever_node
from backend.agents.nodes.planner_orchestrator import planner_orchestrator_node
from backend.agents.nodes.explainer import explainer_node
from backend.agents.nodes.replanner_agent import replanner_agent_node


def should_proceed_to_planning(state: TripState) -> str:
    """Conditional edge: check if constraints are ready for planning."""
    if state.get("is_ready_to_plan", False):
        return "retrieve_data"
    else:
        return "end_with_missing"


# ---- Main Workflow (chat → itinerary) ----

def build_main_workflow() -> StateGraph:
    workflow = StateGraph(TripState)

    # Add nodes
    workflow.add_node("parse_chat", chat_parser_node)
    workflow.add_node("validate_constraints", constraint_validator_node)
    workflow.add_node("retrieve_data", data_retriever_node)
    workflow.add_node("plan_itinerary", planner_orchestrator_node)
    workflow.add_node("explain_plan", explainer_node)

    # Add edges
    workflow.add_edge(START, "parse_chat")
    workflow.add_edge("parse_chat", "validate_constraints")
    workflow.add_conditional_edges(
        "validate_constraints",
        should_proceed_to_planning,
        {
            "retrieve_data": "retrieve_data",
            "end_with_missing": END,
        },
    )
    workflow.add_edge("retrieve_data", "plan_itinerary")
    workflow.add_edge("plan_itinerary", "explain_plan")
    workflow.add_edge("explain_plan", END)

    return workflow.compile()


# ---- Replan Workflow (delay → updated itinerary) ----

def build_replan_workflow() -> StateGraph:
    workflow = StateGraph(TripState)

    workflow.add_node("replan", replanner_agent_node)

    workflow.add_edge(START, "replan")
    workflow.add_edge("replan", END)

    return workflow.compile()


# ---- Public API (called by Task 3 Backend) ----

_main_workflow = None
_replan_workflow = None

def get_main_workflow():
    global _main_workflow
    if _main_workflow is None:
        _main_workflow = build_main_workflow()
    return _main_workflow

def get_replan_workflow():
    global _replan_workflow
    if _replan_workflow is None:
        _replan_workflow = build_replan_workflow()
    return _replan_workflow


def run_workflow(chat_messages: list[str]) -> TripState:
    """Run the full planning pipeline. Called by Task 3 Backend API."""
    workflow = get_main_workflow()
    initial_state: TripState = {
        "raw_chat": chat_messages,
        "extracted_constraints": {},
        "missing_fields": [],
        "assumptions": {},
        "conflict_report": {},
        "is_ready_to_plan": False,
        "route_candidates": [],
        "hotel_candidates": [],
        "transport_candidates": [],
        "activity_candidates": [],
        "food_candidates": [],
        "waypoint_candidates": [],
        "itinerary_candidates": [],
        "selected_itinerary": None,
        "alternative_itineraries": [],
        "validation_report": {},
        "score_breakdown": {},
        "timeline": [],
        "map_points": [],
        "cost_breakdown": {},
        "explanation": "",
        "delay_event": None,
        "replanned_itinerary": None,
        "replanning_explanation": None,
    }
    result = workflow.invoke(initial_state)
    return result


def run_replan_workflow(state: TripState, delay_event: dict) -> TripState:
    """Run replanning after a delay event. Called by Task 3 Backend API."""
    workflow = get_replan_workflow()
    state["delay_event"] = delay_event
    result = workflow.invoke(state)
    return result
```

---

## Mock Tools for Early Development

While waiting for Task 5 to deliver real tool functions, use these mock implementations:

```python
# backend/tools/route_tool.py (mock version)
def get_routes(origin: str, destination_type: str | None = None) -> list[dict]:
    """Mock: returns hardcoded route data."""
    mock_routes = [
        {
            "route_id": "gurugram_rishikesh_2d1n",
            "origin": "Gurugram",
            "destination": "Rishikesh",
            "destination_type": "mountains",
            "distance_km": 260,
            "base_drive_minutes": 390,
            "risk_level": "medium",
            "scenic_score": 7,
        },
        {
            "route_id": "gurugram_jaipur_2d1n",
            "origin": "Gurugram",
            "destination": "Jaipur",
            "destination_type": "heritage",
            "distance_km": 240,
            "base_drive_minutes": 300,
            "risk_level": "low",
            "scenic_score": 5,
        },
    ]
    results = [r for r in mock_routes if r["origin"] == origin]
    if destination_type:
        results = [r for r in results if r.get("destination_type") == destination_type]
    return results

# Similar mock implementations for get_hotels, get_activities, etc.
# Return hardcoded dictionaries that match the expected schema.
```

> **Tip**: Start with mock tools on Day 1. Build and test all agents with mocks. Once Task 5 delivers real tools, swap imports — the agent code should NOT change.

---

## Testing Checklist

- [ ] LLM client initializes successfully with Gemini free API key
- [ ] Chat parser extracts correct constraints from sample chat messages
- [ ] Constraint validator detects missing fields and conflicts
- [ ] Data retriever calls all 6 tool functions without error
- [ ] Planner orchestrator produces at least 1 candidate itinerary
- [ ] Explainer generates a coherent explanation
- [ ] Replanner handles a 90-minute departure delay
- [ ] Full workflow runs end-to-end: `run_workflow(["Let's go to mountains from Gurugram"])`
- [ ] State is correctly passed between nodes (no missing keys)
- [ ] LLM swap works: change `.env` to ollama, verify workflow still runs

### Quick Test Script
```python
# test_workflow.py
from backend.agents.workflow import run_workflow

result = run_workflow([
    "Let's do a weekend trip from Gurugram",
    "Budget under 15k per person",
    "Mountains please, not Jaipur",
    "No night driving",
    "Need rafting and good cafes",
    "Back by Monday morning",
])

print("Constraints:", result["extracted_constraints"])
print("Selected:", result["selected_itinerary"])
print("Explanation:", result["explanation"])
```

---

## Coordination with Other Tasks

| You need from | What |
|--------------|------|
| Task 5 (Mainframe) | Tool function signatures (get_routes, get_hotels, etc.) |
| Task 5 (Mainframe) | Planner function signatures (generate_candidates, score_itinerary, etc.) |

| Others need from you | What |
|---------------------|------|
| Task 3 (Backend API) | `run_workflow()` and `run_replan_workflow()` functions |
| Task 3 (Backend API) | `TripState` schema (to build Pydantic response models) |

---

## Git Workflow

```bash
git checkout -b bucket-2/llm-client-state
# Create llm_client.py, state.py, prompts.py
git commit -m "Task 2: Add LLM client, state schema, prompt templates"

git checkout -b bucket-2/agent-nodes
# Create all nodes/ files
git commit -m "Task 2: Add all 6 agent nodes"

git checkout -b bucket-2/langgraph-workflow
# Create workflow.py
git commit -m "Task 2: Add LangGraph workflow with main and replan pipelines"
```

---

## Common Pitfalls

1. **JSON parsing**: Gemini sometimes wraps JSON in markdown code blocks. Always handle both raw JSON and ` ```json ``` ` wrapped responses.
2. **Rate limits**: Free Gemini has 15 RPM. If you hit limits during testing, add a `time.sleep(4)` between workflow runs.
3. **State initialization**: Every field in TripState must have a value (even if empty list/dict/None). Missing keys cause LangGraph errors.
4. **Import cycles**: Tool and planner imports are at the top of node files. Use late imports or dependency injection if circular import issues arise.
