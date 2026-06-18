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

alert_service = AlertService()
