"""LangGraph node 4d: fetch food/restaurant candidates for all route destinations."""
from backend.agents.nodes.data_retriever import retrieve_food
from backend.agents.state import TripState


def food_retriever_node(state: TripState) -> dict:
    routes = state.get("all_route_candidates") or []
    constraints = state.get("extracted_constraints") or {}
    food: list[dict] = []
    for route in routes:
        dest = str(route.get("destination", "")).strip().title()
        food.extend(retrieve_food(dest, constraints))
    return {"food_candidates": food}
