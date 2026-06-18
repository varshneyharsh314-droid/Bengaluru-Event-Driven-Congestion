import os
import sys
import joblib
import pandas as pd
import numpy as np
from app.core.config import settings

# Dynamically add workspace root to system path to import model_engine
workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if workspace_dir not in sys.path:
    sys.path.append(workspace_dir)

try:
    from model_engine import Predictor
except ImportError:
    Predictor = None

class CongestionService:
    def __init__(self):
        self.model = None
        self.reg_predictor = None
        self.load_model()

    def load_model(self):
        # Look for classification model in various possible directories
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
                    break
                except Exception as e:
                    print(f"Error loading model from {path}: {e}")
        
        if self.model is None:
            print("Warning: Congestion model joblib not found. Using high-fidelity rule fallback for classification.")

        # Load dual-target regression models
        if Predictor is not None:
            try:
                # Use workspace root directory where models are saved
                self.reg_predictor = Predictor(model_dir=workspace_dir)
            except Exception as e:
                print(f"Error initializing dual-target Predictor: {e}")
                self.reg_predictor = None
        else:
            print("Warning: Predictor class not importable.")

    def predict(self, input_data: dict) -> dict:
        """
        Runs XGBoost classification & regression inference, returning both classification and continuous targets.
        """
        # --- 1. Classification prediction (for backwards compatibility) ---
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

        pred_class = None
        probs = None

        if self.model is not None:
            try:
                class_names = ["Low", "Medium", "High"]
                pred_code = self.model.predict(df)[0]
                pred_class = class_names[pred_code]
                
                raw_probs = self.model.predict_proba(df)[0]
                probs = {
                    "Low": float(raw_probs[0]),
                    "Medium": float(raw_probs[1]),
                    "High": float(raw_probs[2])
                }
            except Exception as e:
                print(f"Inference pipeline execution failed: {e}. Falling back to rules.")

        # Classification rule-based fallback if model is missing or failed
        if pred_class is None:
            duration = float(input_data['duration_hours'])
            road_closure = bool(input_data['requires_road_closure'])
            priority = input_data['priority']
            
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
                pred_class = "High"
                p_high = base_score
                p_med = 1.0 - base_score - 0.05
                p_low = 0.05
            elif base_score > 0.35:
                pred_class = "Medium"
                p_med = base_score
                p_high = (1.0 - base_score) * 0.4
                p_low = (1.0 - base_score) * 0.6
            else:
                pred_class = "Low"
                p_low = 1.0 - base_score - 0.05
                p_med = base_score
                p_high = 0.05
                
            probs = {
                "Low": float(p_low),
                "Medium": float(p_med),
                "High": float(p_high)
            }

        # --- 2. Regression predictions (Duration & Impact Radius) ---
        if self.reg_predictor is not None:
            # Map standard backend key naming to what the pipeline predictor expects
            pipeline_input = {
                'event_type': input_data.get('event_type'),
                'event_cause': input_data.get('event_cause'),
                'priority': input_data.get('priority'),
                'requires_road_closure': input_data.get('requires_road_closure'),
                'latitude': input_data.get('latitude'),
                'longitude': input_data.get('longitude'),
                'hour': input_data.get('hour'),
                'day_of_week': input_data.get('day_of_week'),
                'description': input_data.get('description', ''),
                'zone': input_data.get('zone'),
                'junction': input_data.get('junction')
            }
            reg_res = self.reg_predictor.predict(pipeline_input)
            pred_dur = reg_res["predicted_duration_minutes"]
            pred_rad = reg_res["predicted_impact_radius_meters"]
        else:
            # Fallback heuristics
            priority = input_data['priority'].lower()
            requires_closure = bool(input_data['requires_road_closure'])
            
            # Simple keyword extraction multiplier matching the pipeline logic
            desc_lower = str(input_data.get('description', '')).lower()
            severity_mult = 1.0
            if "water logging" in desc_lower or "flood" in desc_lower or "rain" in desc_lower:
                severity_mult = 2.0
            elif "closure" in desc_lower or "blocked" in desc_lower:
                severity_mult = 1.8
            elif "protest" in desc_lower or "strike" in desc_lower:
                severity_mult = 1.6
            elif "accident" in desc_lower or "crash" in desc_lower:
                severity_mult = 1.5
            elif "severe" in desc_lower or "critical" in desc_lower:
                severity_mult = 1.4

            # Duration fallback
            base_dur = 45.0
            if priority == "high":
                base_dur += 60.0
            elif priority == "medium":
                base_dur += 20.0
            if requires_closure:
                base_dur += 90.0
            pred_dur = base_dur * severity_mult
            
            # Radius fallback
            base_rad = 120.0
            if priority == "high":
                base_rad += 200.0
            elif priority == "medium":
                base_rad += 80.0
            if requires_closure:
                base_rad += 350.0
            pred_rad = base_rad * severity_mult

        return {
            "predicted_congestion": pred_class,
            "probabilities": probs,
            "predicted_duration_minutes": pred_dur,
            "predicted_impact_radius_meters": pred_rad
        }

congestion_service = CongestionService()

