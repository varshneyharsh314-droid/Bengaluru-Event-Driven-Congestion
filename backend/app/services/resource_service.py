class ResourceService:
    @staticmethod
    def calculate_deployment(predicted_congestion: str, priority: str, requires_road_closure: bool) -> dict:
        """
        Returns recommended police officers and barricades based on constraints.
        """
        congestion_upper = predicted_congestion.upper()
        
        # Base police allocation
        police_base = {"LOW": 2, "MEDIUM": 4, "HIGH": 8, "EXTREME": 15}
        police_req = police_base.get(congestion_upper, 2)
        
        # Priority modifications
        if priority.upper() == "HIGH":
            police_req += 2
        if requires_road_closure:
            police_req += 4
            
        # Cap police personnel to 20 under normal limits
        police_req = min(20, police_req)
        
        # Base barricade allocation
        barricade_base = {"LOW": 1, "MEDIUM": 5, "HIGH": 12, "EXTREME": 20}
        barricades_req = barricade_base.get(congestion_upper, 1)
        
        # Closure modifications
        if requires_road_closure:
            barricades_req += 8
            
        # Cap barricades to 30 units
        barricades_req = min(30, barricades_req)
        
        return {
            "police_officers": police_req,
            "barricades": barricades_req
        }

resource_service = ResourceService()
