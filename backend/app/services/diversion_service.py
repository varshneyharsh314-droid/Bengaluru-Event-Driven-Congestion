class DiversionService:
    def __init__(self):
        self.diversion_routes = {
            'SilkBoardJunc': "Divert heavy vehicles to HSR Layout 27th Main or BTM Layout 16th Main. Use underpasses for light commuters.",
            'HebbalFlyoverJunc': "Divert inbound airport traffic via Hennur-Bagalur road or Thanisandra main road. Keep central lane clear.",
            'Peenya14thCrossJunc': "Divert industrial trucks to NICE Road. Re-route city buses through Peenya 1st Stage collector streets.",
            'UrvashiJunction': "Re-route traffic through Lalbagh Road and JC Road. Restrict parking on parallel access service roads.",
            'IbblurJunction': "Re-route ORR commuters through Sarjapur Outer Ring Road service loops. Shift signal phases upstream.",
            'Unknown': "Implement local loop diversions within 500m of the incident scene. Shift signal splits upstream."
        }

    def suggest_diversion(self, junction: str, zone: str) -> str:
        text = self.diversion_routes.get(junction)
        if not text:
            # Fallback containing zone contextual naming
            text = f"Implement local loop diversions within 500m of the incident scene in {zone}. Shift signal splits upstream."
        return text

diversion_service = DiversionService()
