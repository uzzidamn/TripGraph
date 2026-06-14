"""
Test runner script to verify the Graph Planning Engine.
Does not require a live Neo4j database as it injects mock retrieved data.
"""
import sys
from backend.planner.candidate_generator import generate_candidates
from backend.planner.scorer import score_itinerary
from backend.planner.validator import validate_itinerary
from backend.planner.timeline_generator import generate_timeline
from backend.planner.replanner import replan_itinerary


def run_tests():
    print("🧪 Starting Planning Engine offline verification tests...\n")

    # 1. Prepare Mock retrieved data
    mock_data = {
        "routes": [
            {
                "route_id": "r_jaipur",
                "origin": "Gurugram",
                "destination": "Jaipur",
                "base_drive_minutes": 300,
                "scenic_score": 7,
                "risk_level": "low",
                "destination_type": "heritage"
            },
            {
                "route_id": "r_rishikesh",
                "origin": "Gurugram",
                "destination": "Rishikesh",
                "base_drive_minutes": 390,
                "scenic_score": 8,
                "risk_level": "medium",
                "destination_type": "adventure"
            }
        ],
        "hotels": [
            {
                "hotel_id": "h_jaipur_comfort",
                "name": "Heritage Haveli Resort",
                "destination": "Jaipur",
                "tier": "comfort",
                "price_per_night": 6000,
                "comfort_score": 8
            },
            {
                "hotel_id": "h_rishikesh_budget",
                "name": "Ganges View Ashram",
                "destination": "Rishikesh",
                "tier": "budget",
                "price_per_night": 2000,
                "comfort_score": 4
            }
        ],
        "transport": [
            {
                "transport_id": "t_jaipur_cab",
                "route_id": "r_jaipur",
                "mode": "cab",
                "cost_total": 8000,
                "comfort_score": 8,
                "fatigue_score": 3,
                "night_driving_allowed": False
            },
            {
                "transport_id": "t_rishikesh_self",
                "route_id": "r_rishikesh",
                "mode": "self_drive",
                "cost_total": 4000,
                "comfort_score": 5,
                "fatigue_score": 6,
                "night_driving_allowed": True
            }
        ],
        "activities": [
            {
                "activity_id": "act_jaipur_1",
                "name": "Amer Fort Guided Tour",
                "destination": "Jaipur",
                "tags": ["heritage", "sightseeing"],
                "cost_per_person": 500,
                "duration_minutes": 120
            },
            {
                "activity_id": "act_jaipur_2",
                "name": "Optional Bazaar Shopping",
                "destination": "Jaipur",
                "tags": ["heritage", "optional"],
                "cost_per_person": 0,
                "duration_minutes": 90
            },
            {
                "activity_id": "act_rishikesh_1",
                "name": "White Water Rafting",
                "destination": "Rishikesh",
                "tags": ["adventure", "sports"],
                "cost_per_person": 1500,
                "duration_minutes": 180
            }
        ],
        "food": [
            {
                "restaurant_id": "res_jaipur_1",
                "name": "Lassiwala",
                "destination": "Jaipur",
                "avg_cost_per_person": 150,
                "avg_duration_minutes": 30
            },
            {
                "restaurant_id": "res_jaipur_2",
                "name": "Chokhi Dhani Dinner",
                "destination": "Jaipur",
                "avg_cost_per_person": 1100,
                "avg_duration_minutes": 120
            }
        ],
        "waypoints": [
            {
                "waypoint_id": "wp_jaipur_1",
                "route_id": "r_jaipur",
                "name": "Highway Dhaba Halt",
                "typical_stop_minutes": 30,
                "lat": 27.65,
                "lng": 76.33,
                "order": 1
            }
        ]
    }

    # 2. Test Case A: Heritage Route (Jaipur)
    constraints_a = {
        "group_size": 4,
        "budget_per_person": 10000,
        "must_include": ["heritage"],
        "destination_type": "heritage",
        "avoid_night_driving": True
    }

    print("Step 1: Generating candidates...")
    candidates = generate_candidates(constraints_a, mock_data)
    print(f"-> Generated {len(candidates)} candidate itineraries.\n")
    assert len(candidates) > 0, "No candidates generated"

    print("Step 2: Scoring and validating candidates...")
    validated_candidates = []
    for idx, cand in enumerate(candidates):
        score_report = score_itinerary(cand, constraints_a)
        val_report = validate_itinerary(cand, constraints_a)
        
        cand["scores"] = score_report
        cand["validation"] = val_report
        
        print(f"Candidate {idx+1} (Dest: {cand['destination']}, Hotel: {cand['hotel'].get('name')}, Transport: {cand['transport'].get('mode')}):")
        print(f"  - Cost: ₹{cand['total_cost_per_person']:,} per person")
        print(f"  - Score: {score_report['final_score']:.2f}")
        print(f"  - Valid: {val_report['is_valid']}")
        if not val_report["is_valid"]:
            print(f"    Violations: {val_report['hard_constraint_violations']}")
        validated_candidates.append(cand)
    print()

    # Find the best valid candidate
    valid_candidates = [c for c in validated_candidates if c["validation"]["is_valid"]]
    assert len(valid_candidates) > 0, "No valid candidates found for Constraints A!"
    best_candidate = max(valid_candidates, key=lambda c: c["scores"]["final_score"])
    print(f"🏆 Best Valid Candidate Chosen: {best_candidate['destination']} with {best_candidate['transport'].get('mode')}\n")

    print("Step 3: Generating timeline for best candidate...")
    timeline = generate_timeline(best_candidate)
    print("Timeline Events:")
    for event in timeline:
        cost_str = f" (Cost: ₹{event['cost']})" if "cost" in event else ""
        print(f"  Day {event['day']} | {event['start_time']} - {event['end_time']} | {event['title']} [{event['type']}] {cost_str}")
    print()

    print("Step 4: Simulating 90-minute delay and replanning...")
    delay_event = {
        "delay_minutes": 90,
        "delay_type": "departure_delay"
    }
    replan_report = replan_itinerary(best_candidate, delay_event, constraints_a)
    
    print("Changes Made:")
    for change in replan_report["changes"]:
        print(f"  - {change}")
    print(f"Delay Absorbed: {replan_report['delay_absorbed']} mins")
    print(f"Delay Remaining: {replan_report['delay_remaining']} mins")
    
    print("\nUpdated Timeline:")
    for event in replan_report["updated_itinerary"]["timeline"]:
        print(f"  Day {event['day']} | {event['start_time']} - {event['end_time']} | {event['title']} [{event['type']}]")
    print()

    # 3. Test Case B: Destination type constraint mismatch (Jaipur route rejected when destination_type is "mountains")
    constraints_b = {
        "group_size": 4,
        "budget_per_person": 10000,
        "must_include": [],
        "destination_type": "mountains"
    }
    print("Step 5: Testing negative constraint (destination_type = 'mountains' should reject Jaipur)...")
    candidates_b = generate_candidates(constraints_b, mock_data)
    jaipur_cand = [c for c in candidates_b if c["destination"] == "Jaipur"][0]
    val_report_b = validate_itinerary(jaipur_cand, constraints_b)
    print(f"  - Jaipur Route Valid for 'mountains' request? {val_report_b['is_valid']}")
    print(f"  - Violations: {val_report_b['hard_constraint_violations']}")
    assert not val_report_b["is_valid"], "Jaipur route should have been rejected for mountain preference!"
    assert any("does not match preference" in v for v in val_report_b["hard_constraint_violations"]), "Mismatch violation missing"

    print("\n✅ All Offline Planning Engine tests PASSED successfully!")


if __name__ == "__main__":
    run_tests()
