import os
import pandas as pd
import numpy as np
import time
from app.core.config import settings

class AlertService:
    def __init__(self):
        self.stations_df = None
        self.load_stations()

    def load_stations(self):
        # Paths to look for the CSV
        paths = [
            settings.POLICE_STATION_CSV,
            os.path.join(os.path.dirname(__file__), "..", "..", "police_station.csv"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "police_station.csv")
        ]
        
        for p in paths:
            if os.path.exists(p):
                try:
                    self.stations_df = pd.read_csv(p)
                    print(f"Police station data loaded successfully from: {p}")
                    return
                except Exception as e:
                    print(f"Error reading police stations from {p}: {e}")

        # Fallback inline data seeding
        print("Warning: police_station.csv not found. Loading inline police stations list.")
        data = {
            'id': list(range(1, 11)),
            'station_name': [
                'Madiwala Traffic Police Station', 'HSR Layout Traffic Police Station',
                'Koramangala Traffic Police Station', 'BTM Layout Police Station',
                'Jayanagar Traffic Police Station', 'Hebbal Traffic Police Station',
                'Peenya Traffic Police Station', 'Indiranagar Traffic Police Station',
                'Halasuru Traffic Police Station', 'Shivajinagar Traffic Police Station'
            ],
            'latitude': [12.9225, 12.9102, 12.9332, 12.9154, 12.9282, 13.0362, 13.0289, 12.9745, 12.9778, 12.9856],
            'longitude': [77.6215, 77.6412, 77.6245, 77.6052, 77.5891, 77.5975, 77.5358, 77.6385, 77.6248, 77.6035],
            'phone': [
                '+91 94808-01824', '+91 94808-01826', '+91 94808-01828', '+91 94808-01830',
                '+91 94808-01832', '+91 94808-01834', '+91 94808-01836', '+91 94808-01838',
                '+91 94808-01840', '+91 94808-01842'
            ],
            'available_officers': [18, 14, 22, 11, 15, 16, 12, 20, 15, 19]
        }
        self.stations_df = pd.DataFrame(data)

    @staticmethod
    def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0  # Earth's radius in km
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c

    def find_nearest_station(self, event_lat: float, event_lng: float) -> dict:
        if self.stations_df is None or self.stations_df.empty:
            self.load_stations()
            
        df = self.stations_df.copy()
        
        # Calculate great-circle distances
        df['distance_km'] = df.apply(
            lambda row: self.calculate_haversine(event_lat, event_lng, row['latitude'], row['longitude']),
            axis=1
        )
        
        # Sort and get nearest
        nearest = df.sort_values(by='distance_km').iloc[0]
        
        # ETA (assuming average speed of 25 km/h)
        avg_speed_kph = 25.0
        eta = int((nearest['distance_km'] / avg_speed_kph) * 60)
        eta_minutes = max(3, eta)
        
        # If id column is not present in df, we generate one
        station_id = int(nearest.get('id', 1))
        
        return {
            'id': station_id,
            'station_name': nearest['station_name'],
            'latitude': float(nearest['latitude']),
            'longitude': float(nearest['longitude']),
            'phone': nearest['phone'],
            'available_officers': int(nearest['available_officers']),
            'distance_km': float(nearest['distance_km']),
            'eta_minutes': eta_minutes
        }

    @staticmethod
    def generate_alert_message(data: dict) -> str:
        """
        Creates a compact structured SMS text suitable for GSM-7 (under 160 chars).
        """
        # Truncate location name if too long to save characters
        loc = data['location_name']
        if len(loc) > 25:
            loc = loc[:22] + "..."
            
        alert_text = (
            f"BTP CTRL ALERT: {data['event_type'].upper()} at {loc} "
            f"({data['latitude']:.4f}, {data['longitude']:.4f}). "
            f"Congestion: {data['congestion'].upper()}, Delay: {data['expected_delay']}m. "
            f"Police: {data['police_needed']}, Barricades: {data['barricades']}. Dispatch needed."
        )
        return alert_text

    @staticmethod
    def simulate_sms_dispatch(phone_number: str, message: str) -> dict:
        """
        Transmits actual SMS using Twilio if credentials are set, otherwise falls back to simulation.
        """
        # If Twilio settings are configured, try to send a real SMS
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
                # To bypass Twilio trial verification limitation and deliver to the user's actual phone
                target_phone = settings.TWILIO_RECIPIENT if settings.TWILIO_RECIPIENT else phone_number
                
                # Twilio requires clean number format
                clean_target = "".join(c for c in target_phone if c.isdigit() or c == '+')
                clean_from = "".join(c for c in settings.TWILIO_PHONE_NUMBER if c.isdigit() or c == '+')
                
                print(f"Sending real SMS from {clean_from} to {clean_target}...")
                
                msg = client.messages.create(
                    body=message,
                    from_=clean_from,
                    to=clean_target
                )
                
                return {
                    "status": "SENT",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "recipient_phone": target_phone,
                    "gateway_message_id": msg.sid,
                    "characters_sent": len(message),
                    "payload": message
                }
            except Exception as e:
                print(f"Twilio actual SMS delivery failed: {e}")
                # Return failure log
                return {
                    "status": "FAILED",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "recipient_phone": phone_number,
                    "gateway_message_id": f"ERROR-{int(time.time())}",
                    "characters_sent": len(message),
                    "payload": f"Error: {str(e)}"
                }
        
        # Fallback simulation
        time.sleep(0.15)
        return {
            "status": "SENT",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "recipient_phone": phone_number,
            "gateway_message_id": f"MSG-SMS-{int(time.time())}",
            "characters_sent": len(message),
            "payload": message
        }

    def trigger_automated_dispatch(self, db, event, target_police=None, target_barricades=None):
        """
        Executes automatic and incremental (escalated) resource dispatch for a traffic incident.
        Updates dispatched forces and logs alerts.
        """
        from app.db import models
        from app.services.resource_service import resource_service
        from app.core.websocket_manager import ws_manager
        import datetime
        import asyncio

        # 1. Fetch recommended values if not explicitly provided
        if target_police is None or target_barricades is None:
            # Fallback based on prediction/congestion level
            congestion_level = "Medium"
            if event.prediction:
                congestion_level = event.prediction.predicted_congestion
            
            res = resource_service.calculate_deployment(
                congestion_level, event.priority, event.requires_road_closure
            )
            rec_police = res["police_officers"]
            rec_barricades = res["barricades"]
        else:
            rec_police = int(target_police)
            rec_barricades = int(target_barricades)

        # 2. Get current dispatched forces
        curr_police = event.dispatched_officers or 0
        curr_barricades = event.dispatched_barricades or 0

        # Calculate delta (additional resources needed)
        delta_police = max(0, rec_police - curr_police)
        delta_barricades = max(0, rec_barricades - curr_barricades)

        # 3. Find nearest station
        nearest = self.find_nearest_station(event.latitude, event.longitude)
        station_id = nearest["id"]

        # Ensure station is seeded in DB
        db_station = db.query(models.PoliceStation).filter(models.PoliceStation.id == station_id).first()
        if not db_station:
            db_station = models.PoliceStation(
                id=station_id,
                station_name=nearest["station_name"],
                latitude=nearest["latitude"],
                longitude=nearest["longitude"],
                phone=nearest["phone"],
                available_officers=nearest["available_officers"]
            )
            db.add(db_station)
            db.commit()

        # 4. Construct dispatch message based on situation
        if curr_police == 0 and curr_barricades == 0:
            # Initial dispatch — always send SMS
            msg = (
                f"BTP DISPATCH: Incident {event.event_id} at {event.junction} "
                f"({event.latitude:.4f},{event.longitude:.4f}). "
                f"Crowd detected. Send: {rec_police} officers, {rec_barricades} barricades. "
                f"Nearest: {nearest['station_name']} ({nearest['distance_km']:.1f}km, ETA {nearest['eta_minutes']}min)."
            )
        elif delta_police > 0 or delta_barricades > 0:
            # Escalation — crowd has grown, more resources needed
            msg = (
                f"BTP ESCALATION: Incident {event.event_id} at {event.junction} crowd growing. "
                f"Send {delta_police} MORE officers, {delta_barricades} MORE barricades. "
                f"Total deployed: {rec_police} officers, {rec_barricades} barricades."
            )
        else:
            # Situation stable — crowd at same or lower level, send status update
            msg = (
                f"BTP STATUS: Incident {event.event_id} at {event.junction} — "
                f"Crowd stable. Current deployment: {curr_police} officers, {curr_barricades} barricades sufficient."
            )

        # Always send SMS for any crowd detection
        dispatch_log = self.simulate_sms_dispatch(nearest["phone"], msg)

        # Log alert
        db_alert = models.Alert(
            event_id=event.event_id,
            station_id=station_id,
            recipient_phone=nearest["phone"],
            status=dispatch_log["status"],
            payload=msg
        )
        db.add(db_alert)

        # Update event record with max deployed resources
        event.dispatched_officers = max(curr_police, rec_police)
        event.dispatched_barricades = max(curr_barricades, rec_barricades)
        db.commit()

        # 5. Broadcast to WebSocket Operator Screens
        ws_payload = {
            "event": "DISPATCH_UPDATE",
            "data": {
                "event_id": event.event_id,
                "junction": event.junction,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "congestion_level": event.prediction.predicted_congestion if event.prediction else "Medium",
                "delay_min": event.prediction.predicted_delay_min if event.prediction else 15,
                "police_deployed": event.dispatched_officers,
                "dispatched_officers": event.dispatched_officers,
                "dispatched_barricades": event.dispatched_barricades,
                "delta_officers": delta_police,
                "delta_barricades": delta_barricades,
                "alert_message": msg,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        }
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            loop.create_task(ws_manager.broadcast(ws_payload))
        else:
            loop.run_until_complete(ws_manager.broadcast(ws_payload))

        return msg

alert_service = AlertService()
