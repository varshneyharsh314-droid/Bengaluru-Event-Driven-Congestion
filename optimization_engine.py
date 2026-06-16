import json
import os

class TrafficOptimizationEngine:
    """
    Rule-Based Optimization Engine for Bengaluru Traffic Police Command Center.
    Calculates resource allocations, priority intersections, and emergency response levels.
    """
    
    # Pre-defined mapping of primary junctions to adjacent priority intersections for traffic diversion
    ADJACENT_INTERSECTIONS_MAP = {
        'SilkBoardJunc': [
            "HSR Layout 14th Main & Outer Ring Road",
            "BTM Layout 16th Main & Outer Ring Road",
            "Madiwala Checkpost Intersection",
            "Ibblur Junction Outer Ring Road"
        ],
        'HebbalFlyoverJunc': [
            "Manyata Tech Park Junction (Outer Ring Road)",
            "Hennur Cross Intersection",
            "RT Nagar 80ft Road Junction",
            "Yelahanka Bypass Junction"
        ],
        'Peenya14thCrossJunc': [
            "Tumkur Road - NICE Road Junction",
            "Jalahalli Cross Intersection",
            "Goraguntepalya Junction",
            "Dasarahalli Metro Station Cross"
        ],
        'UrvashiJunction': [
            "JC Road Junction",
            "Lalbagh Road & Double Road Cross",
            "Richmond Circle Flyover Entry",
            "Hudson Circle Intersection"
        ],
        'LalbaghMainGateJunc': [
            "Minerva Circle Intersection",
            "Siddiah Road Cross",
            "Ashoka Pillar Circle (Jayanagar)",
            "Double Road & KH Road Junction"
        ],
        'IbblurJunction': [
            "Silk Board Junction",
            "Sarjapur Road - Kaikondrahalli Junction",
            "Bellandur Outer Ring Road Junction",
            "Haralur Road Cross"
        ],
        'Sumanhalli': [
            "Goraguntepalya Flyover Entry",
            "Magadi Road Tollgate Intersection",
            "Nayandahalli Junction (Outer Ring Road)",
            "Kamaxipalya Cross"
        ]
    }
    
    @staticmethod
    def optimize_resources(congestion_level, event_type, road_closure, duration_hours, primary_junction="Unknown"):
        """
        Calculates logistics allocation and response plans based on event characteristics.
        """
        congestion_upper = str(congestion_level).upper()
        event_lower = str(event_type).lower()
        road_closure_bool = bool(road_closure)
        
        # 1. Police Personnel Calculation
        # Base personnel on congestion level
        if congestion_upper == "HIGH":
            police = 8
        elif congestion_upper == "MEDIUM":
            police = 4
        else:
            police = 2
            
        # Modifiers based on operational complexity
        if road_closure_bool:
            police += 4  # Need officers at diversion points
        if event_lower == "unplanned":
            police += 2  # Unplanned events lack pre-announced detours, causing sudden queueing
        if duration_hours > 4.0:
            police += 2  # Requires shift coverage and buffer rotation
            
        # Cap personnel
        police = min(20, police)
        
        # 2. Barricades Calculation
        if congestion_upper == "HIGH":
            barricades = 12
        elif congestion_upper == "MEDIUM":
            barricades = 6
        else:
            barricades = 2
            
        if road_closure_bool:
            barricades += 10  # Need to physical cordon off lanes
        if event_lower == "planned":
            barricades += 4   # Planned works need reflective signs & construction warnings
        if duration_hours > 6.0:
            barricades += 4   # Extended blockages require sturdier barriers
            
        barricades = min(30, barricades)
        
        # 3. Priority Intersections for Diversion Control
        priority_intersections = TrafficOptimizationEngine.ADJACENT_INTERSECTIONS_MAP.get(
            primary_junction, 
            [
                "Immediate Upstream Arterial Crossroad",
                "Adjacent Service Road Confluence"
            ]
        )
        
        # 4. Emergency Response Level Determination
        if congestion_upper == "HIGH" and (road_closure_bool or duration_hours > 6.0):
            response_level = "Level 1 (Critical)"
            dispatch_officer = "Traffic Police Inspector (TI)"
            actions = [
                "Activate automated diversion signs on Outer Ring Road VMS boards",
                "Broadcast alert to Google Maps, Waze, and MapmyIndia APIs",
                "Deploy towing crane to the site immediately",
                "Sync traffic signals at priority junctions to increase green time on discharge corridors"
            ]
        elif congestion_upper == "HIGH" or (congestion_upper == "MEDIUM" and road_closure_bool):
            response_level = "Level 2 (High)"
            dispatch_officer = "Sub-Inspector (SI)"
            actions = [
                "Manually override traffic signals at primary junction",
                "Issue public warning via Social Media handles & Local Radio stations",
                "Set up physical diversion signs 500m ahead of blockage"
            ]
        elif congestion_upper == "MEDIUM":
            response_level = "Level 3 (Moderate)"
            dispatch_officer = "Assistant Sub-Inspector (ASI)"
            actions = [
                "Deploy local ward officers to manage merging lanes",
                "Monitor queue lengths via CCTV feed"
            ]
        else:
            response_level = "Level 4 (Routine)"
            dispatch_officer = "Head Constable (HC)"
            actions = [
                "Conduct routine patrol clearance",
                "Standard log entry updated in central system"
            ]
            
        # Compile response dictionary
        response = {
            "input_parameters": {
                "congestion_level": congestion_level,
                "event_type": event_type,
                "road_closure": road_closure,
                "duration_hours": duration_hours,
                "primary_junction": primary_junction
            },
            "resource_allocation": {
                "police_personnel": police,
                "barricades_needed": barricades
            },
            "field_logistics": {
                "emergency_response_level": response_level,
                "dispatch_commanding_officer": dispatch_officer,
                "recommended_actions": actions,
                "priority_intersections_for_diversions": priority_intersections
            }
        }
        
        return response

if __name__ == "__main__":
    # Test cases to generate JSON output examples
    test_cases = [
        # Case A: Critical Accident at Silk Board during commute hour
        ("High", "unplanned", True, 2.5, "SilkBoardJunc"),
        # Case B: Routine construction at Peenya
        ("Medium", "planned", False, 12.0, "Peenya14thCrossJunc"),
        # Case C: Minor breakdown in South zone
        ("Low", "unplanned", False, 0.5, "Unknown")
    ]
    
    print("--- GENERATING TEST CASE JSON OUTPUTS ---")
    for i, tc in enumerate(test_cases, 1):
        res = TrafficOptimizationEngine.optimize_resources(*tc)
        print(f"\n================ TEST CASE {i} ================")
        print(json.dumps(res, indent=4))
