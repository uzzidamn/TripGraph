"""
Bucket 3 Validation Script.
Tests the FastAPI backend routes and API layer using TestClient.
"""
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TripGraph AI" in response.text

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    assert "pipeline_mode" in response.json()

def test_set_config():
    payload = {"pipeline_mode": "augmented"}
    response = client.post("/api/config", json=payload)
    assert response.status_code == 200
    assert response.json() == {"pipeline_mode": "augmented"}

    # Test invalid config
    payload_invalid = {"pipeline_mode": "invalid_mode"}
    response_invalid = client.post("/api/config", json=payload_invalid)
    assert response_invalid.status_code == 400

@patch("backend.agents.workflow.run_workflow")
def test_parse_chat(mock_run_workflow):
    # Setup mock return
    mock_run_workflow.return_value = {
        "extracted_constraints": {
            "origin": "Gurugram",
            "destination": "Jaipur",
            "destination_type": "heritage",
            "budget_per_person": 15000,
            "dates": None,
            "trip_duration": "2D1N",
            "transport_preference": ["cab_with_driver"],
            "avoid_night_driving": True,
            "must_include": ["rafting", "cafes"],
            "return_deadline": "Monday morning",
            "hotel_tier": "comfort",
            "risk_tolerance": "medium",
            "group_size": 4,
            "special_requirements": []
        },
        "missing_fields": [],
        "assumptions": {"group_size": "4 (default)", "risk_tolerance": "medium (default)"},
        "conflict_report": {"has_conflicts": False, "conflicts": []}
    }
    
    payload = {"chat_messages": ["Let's go to Jaipur from Gurugram"]}
    response = client.post("/api/parse-chat", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["extracted_constraints"]["origin"] == "Gurugram"
    assert json_data["extracted_constraints"]["destination"] == "Jaipur"
    mock_run_workflow.assert_called_once_with(["Let's go to Jaipur from Gurugram"])

@patch("backend.agents.workflow.run_workflow_from_constraints")
def test_generate_itinerary(mock_run_workflow):
    # Setup mock return
    mock_run_workflow.return_value = {
        "selected_itinerary": {
            "destination": "Jaipur",
            "total_cost_per_person": 5000,
            "route": {"route_id": "r_jaipur", "origin": "Gurugram", "destination": "Jaipur", "distance_km": 240},
            "transport": {"mode": "cab", "cost_total": 8000},
            "hotel": {"name": "Heritage Stay", "price_per_night": 4000},
            "activities": []
        },
        "alternative_itineraries": [],
        "validation_report": {"is_valid": True, "hard_constraint_violations": [], "soft_constraint_warnings": []},
        "score_breakdown": {
            "preference_match": 10.0,
            "budget_efficiency": 10.0,
            "comfort": 10.0,
            "scenic": 10.0,
            "fatigue": 10.0,
            "risk": 10.0,
            "final_score": 85.0
        },
        "timeline": [{"day": 1, "start_time": "09:00", "end_time": "12:00", "title": "Travel", "type": "travel"}],
        "map_points": [{"lat": 28.45, "lng": 77.02, "label": "Gurugram", "type": "origin"}],
        "cost_breakdown": {"transport": 2000, "hotel": 1000, "activities": 0, "food": 1000, "miscellaneous": 1000, "total": 5000},
        "explanation": "Mocked itinerary to Jaipur"
    }

    payload = {
        "constraints": {
            "origin": "Gurugram",
            "destination": "Jaipur",
            "budget_per_person": 10000
        }
    }
    response = client.post("/api/generate-itinerary", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["recommended_itinerary"]["destination"] == "Jaipur"
    assert json_data["score_breakdown"]["final_score"] == 85.0
    assert len(json_data["timeline"]) == 1

@patch("backend.agents.workflow.run_replan_workflow")
def test_simulate_delay(mock_run_replan_workflow):
    mock_run_replan_workflow.return_value = {
        "replanned_itinerary": {
            "destination": "Jaipur",
            "changes": ["Breakfast shortened by 20 mins"]
        },
        "validation_report": {"is_valid": True, "hard_constraint_violations": [], "soft_constraint_warnings": []},
        "replanning_explanation": "Delay absorbed successfully."
    }

    payload = {
        "delay_type": "departure_delay",
        "delay_minutes": 60,
        "constraints": {"origin": "Gurugram"},
        "selected_itinerary": {"destination": "Jaipur"}
    }
    response = client.post("/api/simulate-delay", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["changes"] == ["Breakfast shortened by 20 mins"]
    assert json_data["explanation"] == "Delay absorbed successfully."
