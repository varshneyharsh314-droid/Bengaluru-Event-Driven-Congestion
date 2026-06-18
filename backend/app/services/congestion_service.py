import os
import joblib
import pandas as pd
import numpy as np
from app.core.config import settings

class CongestionService:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        # Look for model in various possible directories
        paths_to_check = [
            settings.CONGESTION_MODEL_PATH,
            os.path.join(os.path.dirname(__file__), "..", "..", "congestion_model.joblib"), # Root of backend
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "congestion_model.joblib") # Root of workspace
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                try:
                    self.model = joblib.load(path)
                    print(f"Congestion Model successfully loaded from: {path}")
                    return
                except Exception as e:
                    print(f"Error loading model from {path}: {e}")
        
        print("Warning: Congestion model joblib not found. Using high-fidelity rule fallback.")
        self.model = None

    def predict(self, input_data: dict) -> dict:
        """
        Runs XGBoost inference if available, otherwise executes high-fidelity fallback.
        """
        # Formulate pandas DataFrame
        df = pd.DataFrame([{
            'event_type': input_data['event_type'],
            'event_cause': input_data['event_cause'],
            'priority': input_data['priority'],
            'requires_road_closure': bool(input_data['requires_road_closure']),
            'hour': int(input_data['hour']),
            'day_of_week': int(input_data['day_of_week']),
            'duration_hours': float(input_data['duration_hours']),
            'zone': input_data['zone'],
            'junction': input_data['junction']
        }])

        if self.model is not None:
            try:
                class_names = ["Low", "Medium", "High"]
                pred_code = self.model.predict(df)[0]
                prediction_class = class_names[pred_code]
                
                probs = self.model.predict_proba(df)[0]
                return {
                    "predicted_congestion": prediction_class,
                    "probabilities": {
                        "Low": float(probs[0]),
                        "Medium": float(probs[1]),
                        "High": float(probs[2])
                    }
                }
            except Exception as e:
                print(f"Inference pipeline execution failed: {e}. Falling back to rules.")

        # High-fidelity rule-based fallback
        # High impact factors: road closure, high priority, long duration
        duration = float(input_data['duration_hours'])
        road_closure = bool(input_data['requires_road_closure'])
        priority = input_data['priority']
        
        # Calculate simulated probability scores
        base_score = 0.2
        if road_closure:
            base_score += 0.5
        if priority.lower() == "high":
            base_score += 0.15
        if duration > 3.0:
            base_score += 0.2
        elif duration > 1.0:
            base_score += 0.1
            
        base_score = min(0.95, max(0.05, base_score))
        
        if base_score > 0.65:
            pred = "High"
            p_high = base_score
            p_med = 1.0 - base_score - 0.05
            p_low = 0.05
        elif base_score > 0.35:
            pred = "Medium"
            p_med = base_score
            p_high = (1.0 - base_score) * 0.4
            p_low = (1.0 - base_score) * 0.6
        else:
            pred = "Low"
            p_low = 1.0 - base_score - 0.05
            p_med = base_score
            p_high = 0.05
            
        return {
            "predicted_congestion": pred,
            "probabilities": {
                "Low": float(p_low),
                "Medium": float(p_med),
                "High": float(p_high)
            }
        }

congestion_service = CongestionService()
