class ResourceService:
    @staticmethod
    def calculate_deployment(
        predicted_congestion: str, 
        priority: str, 
        requires_road_closure: bool,
        predicted_duration_minutes: float = 60.0,
        predicted_impact_radius_meters: float = 200.0
    ) -> dict:
        """
        Returns recommended police officers, barricades, and VMS boards based on constraints,
        incorporating predicted duration and impact radius.
        """
        congestion_upper = predicted_congestion.upper()
        priority_upper = priority.upper()
        
        # 1. Police officers calculation
        # Base cops based on severity
        police_base = {"LOW": 1, "MEDIUM": 3, "HIGH": 6, "EXTREME": 10}
        police_req = police_base.get(congestion_upper, 2)
        
        # Priority modifiers
        if priority_upper == "HIGH":
            police_req += 3
        elif priority_upper == "MEDIUM":
            police_req += 1
            
        # Closure modifier
        if requires_road_closure:
            police_req += 4
            
        # Duration modifier (1 cop per hour of congestion)
        duration_cops = int(predicted_duration_minutes / 60.0)
        police_req += max(0, min(6, duration_cops))
        
        # Cap police personnel to 20
        police_req = min(20, police_req)
        
        # 2. Barricades calculation
        barricade_base = {"LOW": 2, "MEDIUM": 5, "HIGH": 12, "EXTREME": 20}
        barricades_req = barricade_base.get(congestion_upper, 2)
        
        # Priority modifiers
        if priority_upper == "HIGH":
            barricades_req += 8
        elif priority_upper == "MEDIUM":
            barricades_req += 3
            
        # Closure modifier
        if requires_road_closure:
            barricades_req += 10
            
        # Cap barricades to 30 units
        barricades_req = min(30, barricades_req)
        
        # 3. VMS Boards calculation (new feature)
        vms_req = 1
        if predicted_impact_radius_meters > 1000.0:
            vms_req += 2
        elif predicted_impact_radius_meters > 500.0:
            vms_req += 1
            
        if priority_upper == "HIGH":
            vms_req += 1
            
        vms_req = min(5, vms_req)
        
        return {
            "police_officers": police_req,
            "barricades": barricades_req,
            "vms_boards": vms_req
        }

resource_service = ResourceService()

