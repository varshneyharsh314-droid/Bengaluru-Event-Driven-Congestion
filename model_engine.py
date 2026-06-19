import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

# Import from our data pipeline
from data_pipeline import load_and_prepare_data, extract_severity_multiplier

# Configuration
DATASET_PATH = "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
MODEL_DIR = "."

def train_and_save_models():
    # 1. Load and prepare data
    df = load_and_prepare_data(DATASET_PATH)
    
    # Define features and targets
    features = [
        'event_type', 'event_cause', 'priority', 'requires_road_closure',
        'latitude', 'longitude', 'hour_of_day', 'day_of_week', 
        'is_weekend', 'is_peak_hour', 'severity_multiplier', 'zone', 'junction'
    ]
    
    X = df[features]
    y_duration = df['Actual_Duration_Minutes']
    y_radius = df['Actual_Impact_Radius_Meters']
    
    # Split categorical and numerical features for ColumnTransformer
    categorical_features = ['event_type', 'event_cause', 'priority', 'zone', 'junction']
    numerical_features = [
        'latitude', 'longitude', 'hour_of_day', 'day_of_week', 
        'is_weekend', 'is_peak_hour', 'severity_multiplier'
    ]
    
    # Preprocessor pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
            ('bool', StandardScaler(), ['requires_road_closure'])
        ],
        remainder='drop'
    )
    
    # 2. Split dataset for duration model
    X_train, X_test, y_dur_train, y_dur_test = train_test_split(X, y_duration, test_size=0.2, random_state=42)
    _, _, y_rad_train, y_rad_test = train_test_split(X, y_radius, test_size=0.2, random_state=42)
    
    # Fit the preprocessor
    print("Fitting preprocessor pipeline...")
    X_train_preprocessed = preprocessor.fit_transform(X_train)
    X_test_preprocessed = preprocessor.transform(X_test)
    
    # 3. Train Duration XGBoost Model
    print("Training XGBoost Duration Regressor...")
    duration_model = XGBRegressor(
        n_estimators=150,
        learning_rate=0.08,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    duration_model.fit(X_train_preprocessed, y_dur_train)
    
    # Evaluate Duration Model
    y_dur_pred = duration_model.predict(X_test_preprocessed)
    dur_mae = mean_absolute_error(y_dur_test, y_dur_pred)
    dur_rmse = np.sqrt(mean_squared_error(y_dur_test, y_dur_pred))
    dur_r2 = r2_score(y_dur_test, y_dur_pred)
    
    print("\n--- Duration Prediction Model Performance ---")
    print(f"MAE:  {dur_mae:.2f} minutes")
    print(f"RMSE: {dur_rmse:.2f} minutes")
    print(f"R²:   {dur_r2:.4f}")
    
    # 4. Train Impact Radius XGBoost Model
    print("\nTraining XGBoost Impact Radius Regressor...")
    radius_model = XGBRegressor(
        n_estimators=150,
        learning_rate=0.08,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    radius_model.fit(X_train_preprocessed, y_rad_train)
    
    # Evaluate Radius Model
    y_rad_pred = radius_model.predict(X_test_preprocessed)
    rad_mae = mean_absolute_error(y_rad_test, y_rad_pred)
    rad_rmse = np.sqrt(mean_squared_error(y_rad_test, y_rad_pred))
    rad_r2 = r2_score(y_rad_test, y_rad_pred)
    
    print("\n--- Impact Radius Prediction Model Performance ---")
    print(f"MAE:  {rad_mae:.2f} meters")
    print(f"RMSE: {rad_rmse:.2f} meters")
    print(f"R²:   {rad_r2:.4f}")
    
    # 5. Save preprocessor and models
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(preprocessor, os.path.join(MODEL_DIR, 'preprocessor.joblib'))
    joblib.dump(duration_model, os.path.join(MODEL_DIR, 'duration_model.joblib'))
    joblib.dump(radius_model, os.path.join(MODEL_DIR, 'radius_model.joblib'))
    print(f"\nModels successfully saved to: {MODEL_DIR}")

class Predictor:
    def __init__(self, model_dir=MODEL_DIR):
        self.preprocessor_path = os.path.join(model_dir, 'preprocessor.joblib')
        self.duration_model_path = os.path.join(model_dir, 'duration_model.joblib')
        self.radius_model_path = os.path.join(model_dir, 'radius_model.joblib')
        self.is_loaded = False
        
        self.load_models()

    def load_models(self):
        if (os.path.exists(self.preprocessor_path) and 
            os.path.exists(self.duration_model_path) and 
            os.path.exists(self.radius_model_path)):
            try:
                self.preprocessor = joblib.load(self.preprocessor_path)
                self.duration_model = joblib.load(self.duration_model_path)
                self.radius_model = joblib.load(self.radius_model_path)
                self.is_loaded = True
                print("XGBoost prediction models loaded successfully.")
            except Exception as e:
                print(f"Error loading models: {e}. Fallback logic will be used.")
                self.is_loaded = False
        else:
            print("Warning: Model joblib files not found. Fallback logic will be used.")
            self.is_loaded = False

    def predict(self, input_data: dict) -> dict:
        """
        Inputs: input_data containing incident details:
        {
            'event_type': 'unplanned',
            'event_cause': 'accident',
            'priority': 'high',
            'requires_road_closure': True,
            'latitude': 12.9172,
            'longitude': 77.6366,
            'hour': 18,
            'day_of_week': 3,
            'description': 'Severe accident near junction',
            'zone': 'HSR Layout',
            'junction': 'HSRLayout14thMain'
        }
        """
        description = input_data.get('description', '')
        severity_mult = extract_severity_multiplier(description)
        
        hour = int(input_data.get('hour', 12))
        day_of_week = int(input_data.get('day_of_week', 0))
        is_weekend = 1 if day_of_week >= 5 else 0
        is_peak = 1 if hour in [8, 9, 10, 17, 18, 19] else 0
        
        # Prepare inputs as a dataframe row matching trained features structure
        row = {
            'event_type': input_data.get('event_type', 'unplanned'),
            'event_cause': input_data.get('event_cause', 'unknown'),
            'priority': input_data.get('priority', 'low'),
            'requires_road_closure': bool(input_data.get('requires_road_closure', False)),
            'latitude': float(input_data.get('latitude', 12.9716)),
            'longitude': float(input_data.get('longitude', 77.5946)),
            'hour_of_day': hour,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'is_peak_hour': is_peak,
            'severity_multiplier': severity_mult,
            'zone': input_data.get('zone', 'Unknown'),
            'junction': input_data.get('junction', 'Unknown')
        }
        
        df_input = pd.DataFrame([row])
        
        if self.is_loaded:
            try:
                preprocessed_X = self.preprocessor.transform(df_input)
                pred_duration = float(self.duration_model.predict(preprocessed_X)[0])
                pred_radius = float(self.radius_model.predict(preprocessed_X)[0])
                
                # Make sure predictions are reasonable
                pred_duration = max(5.0, pred_duration)
                pred_radius = max(50.0, pred_radius)
                
                return {
                    "predicted_duration_minutes": pred_duration,
                    "predicted_impact_radius_meters": pred_radius,
                    "severity_multiplier": severity_mult,
                    "model_source": "XGBoost ML Pipeline"
                }
            except Exception as e:
                print(f"ML Prediction failed: {e}. Falling back to rule engine.")
                
        # Rule-based fallback
        priority = row['priority'].lower()
        requires_closure = row['requires_road_closure']
        
        # Duration fallback
        base_dur = 45.0
        if priority == "high":
            base_dur += 60.0
        elif priority == "medium":
            base_dur += 20.0
        if requires_closure:
            base_dur += 90.0
        pred_duration = base_dur * severity_mult
        
        # Radius fallback
        base_rad = 120.0
        if priority == "high":
            base_rad += 200.0
        elif priority == "medium":
            base_rad += 80.0
        if requires_closure:
            base_rad += 350.0
        pred_radius = base_rad * severity_mult
        
        return {
            "predicted_duration_minutes": pred_duration,
            "predicted_impact_radius_meters": pred_radius,
            "severity_multiplier": severity_mult,
            "model_source": "Heuristic Rule-Based Fallback"
        }

if __name__ == "__main__":
    train_and_save_models()
    
    # Run test prediction
    print("\nRunning sample prediction test...")
    predictor = Predictor()
    sample_incident = {
        'event_type': 'unplanned',
        'event_cause': 'water logging',
        'priority': 'high',
        'requires_road_closure': True,
        'latitude': 12.9261,
        'longitude': 77.6508,
        'hour': 18,
        'day_of_week': 2,
        'description': 'severe water logging after heavy rain, vehicles stranded',
        'zone': 'Koramangala',
        'junction': 'AgaraJunction'
    }
    pred = predictor.predict(sample_incident)
    print("Prediction Result:")
    print(pred)
