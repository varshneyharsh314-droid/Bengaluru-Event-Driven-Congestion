import pandas as pd
import numpy as np
import os
import re

def clean_description(desc):
    if pd.isna(desc):
        return ""
    return str(desc).lower()

def extract_severity_multiplier(desc_text):
    text = clean_description(desc_text)
    
    # Define keywords and their corresponding multipliers
    keywords = {
        r"water\s*logging|flood|waterlogging|submerge|rain": 2.0,
        r"closure|blocked|barricaded|divert|closed": 1.8,
        r"protest|strike|rally|procession|dharna": 1.6,
        r"accident|collision|crash|injury|fatal": 1.5,
        r"vip|convoy|minister|governor": 1.5,
        r"severe|heavy|critical|gridlock|choke": 1.4,
        r"breakdown|stalled|puncture|bus.*broken": 1.2
    }
    
    max_mult = 1.0
    for pattern, multiplier in keywords.items():
        if re.search(pattern, text):
            if multiplier > max_mult:
                max_mult = multiplier
                
    return max_mult

def load_and_prepare_data(file_path):
    print(f"Loading dataset from: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")
        
    df = pd.read_csv(file_path)
    
    # 1. Datetime conversion and Actual_Duration_Minutes calculation
    df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
    df['closed_datetime'] = pd.to_datetime(df['closed_datetime'], errors='coerce')
    
    # Remove rows where start_datetime is missing (essential for training features)
    df = df.dropna(subset=['start_datetime']).copy()
    
    # Calculate duration in minutes
    df['Actual_Duration_Minutes'] = (df['closed_datetime'] - df['start_datetime']).dt.total_seconds() / 60.0
    
    # Clean up duration: handle NaNs, negative, or zero durations
    median_duration = df['Actual_Duration_Minutes'].loc[df['Actual_Duration_Minutes'] > 0].median()
    if pd.isna(median_duration) or median_duration <= 0:
        median_duration = 60.0 # Default fallback
    
    df['Actual_Duration_Minutes'] = df['Actual_Duration_Minutes'].fillna(median_duration)
    df.loc[df['Actual_Duration_Minutes'] <= 0, 'Actual_Duration_Minutes'] = median_duration
    
    # 2. Engineer temporal features
    df['hour_of_day'] = df['start_datetime'].dt.hour
    df['day_of_week'] = df['start_datetime'].dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    # Peak hours: 8:00-11:00 (8,9,10) and 17:00-20:00 (17,18,19)
    df['is_peak_hour'] = df['hour_of_day'].isin([8, 9, 10, 17, 18, 19]).astype(int)
    
    # 3. Handle spatial coordinates missing values
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude'] = df['latitude'].fillna(df['latitude'].median() if not df['latitude'].isna().all() else 12.9716)
    df['longitude'] = df['longitude'].fillna(df['longitude'].median() if not df['longitude'].isna().all() else 77.5946)
    
    # 4. Fill missing values for categorical columns
    df['event_type'] = df['event_type'].fillna('unplanned')
    df['event_cause'] = df['event_cause'].fillna('unknown')
    df['priority'] = df['priority'].fillna('low')
    df['requires_road_closure'] = df['requires_road_closure'].fillna(False).astype(bool)
    df['zone'] = df['zone'].fillna('Unknown')
    df['junction'] = df['junction'].fillna('Unknown')
    
    # 5. Extract NLP-based severity multiplier from descriptions
    print("Extracting NLP severity multipliers from event descriptions...")
    df['severity_multiplier'] = df['description'].apply(extract_severity_multiplier)
    
    # 6. Synthesize Target Variable: Actual_Impact_Radius_Meters
    print("Synthesizing target variable: Actual_Impact_Radius_Meters...")
    np.random.seed(42)  # For reproducibility
    
    base_radius = 100.0
    priority_add = df['priority'].str.lower().map({'high': 250.0, 'medium': 100.0, 'low': 0.0}).fillna(0.0)
    closure_add = df['requires_road_closure'].map({True: 400.0, False: 0.0})
    
    synthetic_radius = (base_radius + priority_add + closure_add) * df['severity_multiplier']
    
    # Inject Gaussian Noise (mean=0, std=35m)
    noise = np.random.normal(0, 35.0, size=len(df))
    synthetic_radius += noise
    
    # Cap impact radius between 50 meters and 1800 meters
    df['Actual_Impact_Radius_Meters'] = np.clip(synthetic_radius, 50.0, 1800.0)
    
    print(f"Data pipeline complete. Preprocessed {len(df)} records successfully.")
    return df

if __name__ == "__main__":
    # Test script execution
    file_path = "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
    try:
        processed_df = load_and_prepare_data(file_path)
        print("\nProcessed Data Preview:")
        print(processed_df[['id', 'Actual_Duration_Minutes', 'Actual_Impact_Radius_Meters', 'severity_multiplier', 'hour_of_day', 'is_peak_hour']].head())
    except Exception as e:
        print(f"Error during data pipeline execution: {e}")
