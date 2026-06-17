import pandas as pd
import numpy as np
import os

class PoliceStationFinder:
    """
    Finder module to locate the nearest police station from an incident coordinate
    using the Haversine distance formula.
    """
    def __init__(self, csv_path="police_station.csv"):
        self.csv_path = csv_path
        self.stations_df = None
        self.load_stations()

    def load_stations(self):
        """Loads police station data from the CSV file."""
        if os.path.exists(self.csv_path):
            self.stations_df = pd.read_csv(self.csv_path)
        else:
            # Fallback inline data if CSV is missing
            data = {
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
            # Save it so it exists
            self.stations_df.to_csv(self.csv_path, index=False)

    @staticmethod
    def calculate_haversine(lat1, lon1, lat2, lon2):
        """
        Computes the great-circle distance (in km) between two points on the Earth.
        """
        R = 6371.0 # Earth's radius in km
        
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c

    def find_nearest_station(self, event_lat, event_lng):
        """
        Finds the nearest police station from given coordinates.
        Returns a dictionary with station details and distance.
        """
        if self.stations_df is None or self.stations_df.empty:
            self.load_stations()

        df = self.stations_df.copy()
        
        # Calculate distance for all stations
        df['distance_km'] = df.apply(
            lambda row: self.calculate_haversine(event_lat, event_lng, row['latitude'], row['longitude']),
            axis=1
        )
        
        # Sort and get closest station
        nearest = df.sort_values(by='distance_km').iloc[0]
        
        # Estimate ETA (assume average speed of 25 km/h in Bengaluru traffic)
        avg_speed_kph = 25.0
        eta_minutes = int((nearest['distance_km'] / avg_speed_kph) * 60)
        # Minimum ETA is 3 minutes
        eta_minutes = max(3, eta_minutes)
        
        return {
            'station_name': nearest['station_name'],
            'latitude': float(nearest['latitude']),
            'longitude': float(nearest['longitude']),
            'phone': nearest['phone'],
            'available_officers': int(nearest['available_officers']),
            'distance_km': float(nearest['distance_km']),
            'eta_minutes': eta_minutes
        }

if __name__ == "__main__":
    # Test case: incident near Silk Board coordinates
    finder = PoliceStationFinder()
    result = finder.find_nearest_station(12.9176, 77.6246)
    print("Nearest Station Test:")
    for k, v in result.items():
        print(f"  {k}: {v}")
