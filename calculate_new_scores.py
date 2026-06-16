import pandas as pd
import numpy as np

# Load the dataset
file_path = r"u:\Theme2\Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
df = pd.read_csv(file_path)

# Prepare timestamps and duration
df['start_dt'] = pd.to_datetime(df['start_datetime'], errors='coerce')
df['end_dt'] = pd.to_datetime(df['end_datetime'], errors='coerce')
df['closed_dt'] = pd.to_datetime(df['closed_datetime'], errors='coerce')
df['resolved_dt'] = pd.to_datetime(df['resolved_datetime'], errors='coerce')

df['effective_end_dt'] = df['end_dt'].fillna(df['closed_dt']).fillna(df['resolved_dt'])
df['duration_min'] = (df['effective_end_dt'] - df['start_dt']).dt.total_seconds() / 60.0

# Impute missing durations with cause-specific medians
median_durations = df.groupby('event_cause')['duration_min'].median()
global_median = df['duration_min'].median()
df['duration_minutes'] = df['duration_min']

for cause in df['event_cause'].unique():
    cause_median = median_durations.get(cause, global_median)
    if np.isnan(cause_median):
        cause_median = global_median
    mask = (df['event_cause'] == cause) & (df['duration_minutes'].isnull())
    df.loc[mask, 'duration_minutes'] = cause_median

df['duration_hours'] = df['duration_minutes'] / 60.0

# -------------------------------------------------------------
# DOMAIN-DRIVEN SCORING FUNCTION
# -------------------------------------------------------------
def get_domain_congestion_score(row):
    # 1. Event Type Impact (unplanned causes sudden shock, planned has pre-warnings)
    s_type = 6 if str(row['event_type']).lower() == 'unplanned' else 4
    
    # 2. Priority Impact
    s_priority = 3 if str(row['priority']).lower() == 'high' else 1
    
    # 3. Road Closure Impact
    s_closure = 6 if str(row['requires_road_closure']).upper() == 'TRUE' else 0
    
    # 4. Peak Hour Impact (commuter hours)
    start_hour = row['start_dt'].hour if pd.notnull(row['start_dt']) else 9
    if (8 <= start_hour < 11) or (17 <= start_hour < 20):
        s_peak = 4  # Commute Peak
    elif (11 <= start_hour < 17) or (20 <= start_hour < 22):
        s_peak = 2  # Off-Peak Active
    else:
        s_peak = 0  # Late Night / Early Morning
        
    # 5. Duration Impact (linear queue buildup over time)
    dur_h = row['duration_hours']
    if dur_h <= 0.5:
        s_duration = 1
    elif dur_h <= 2.0:
        s_duration = 3
    elif dur_h <= 6.0:
        s_duration = 5
    else:
        s_duration = 7
        
    # 6. Zone Vulnerability (IT corridors & high density areas have higher load)
    zone_str = str(row['zone']).lower()
    if any(z in zone_str for z in ['central', 'east', 'south']):
        s_zone = 3  # High density
    elif any(z in zone_str for z in ['west', 'north']):
        s_zone = 1.5  # Moderate density
    else:
        s_zone = 0  # Low density / Unknown
        
    # Total Score
    total_score = s_type + s_priority + s_closure + s_peak + s_duration + s_zone
    return total_score

df['congestion_score'] = df.apply(get_domain_congestion_score, axis=1)

# Categorize into Low, Medium, High
def get_congestion_level(score):
    if score < 12:
        return 'Low'
    elif score < 19:
        return 'Medium'
    else:
        return 'High'

df['congestion_level'] = df['congestion_score'].apply(get_congestion_level)

# Select sample rows to print
sample_cols = ['event_type', 'priority', 'requires_road_closure', 'zone', 'start_datetime', 'duration_hours', 'congestion_score', 'congestion_level']
samples = df[sample_cols].head(10)
print(samples.to_string())

print("\nValue counts:")
print(df['congestion_level'].value_counts())
