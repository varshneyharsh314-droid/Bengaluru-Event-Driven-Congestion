import pandas as pd
import numpy as np

file_path = r"u:\Theme2\Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
df = pd.read_csv(file_path)

# Convert to datetime
df['start_dt'] = pd.to_datetime(df['start_datetime'], errors='coerce')
df['end_dt'] = pd.to_datetime(df['end_datetime'], errors='coerce')
df['closed_dt'] = pd.to_datetime(df['closed_datetime'], errors='coerce')
df['resolved_dt'] = pd.to_datetime(df['resolved_datetime'], errors='coerce')

# Check overlaps
has_end = df['end_dt'].notnull()
has_closed = df['closed_dt'].notnull()
has_resolved = df['resolved_dt'].notnull()

print(f"Total rows: {len(df)}")
print(f"Has end_datetime: {has_end.sum()}")
print(f"Has closed_datetime: {has_closed.sum()}")
print(f"Has resolved_datetime: {has_resolved.sum()}")
print(f"Has any end/closed/resolved: {(has_end | has_closed | has_resolved).sum()}")

# Create effective end datetime
df['effective_end_dt'] = df['end_dt'].fillna(df['closed_dt']).fillna(df['resolved_dt'])
print(f"Has effective end datetime: {df['effective_end_dt'].notnull().sum()}")

# Calculate duration in minutes for records that have it
duration_min = (df['effective_end_dt'] - df['start_dt']).dt.total_seconds() / 60.0
valid_durations = duration_min[df['effective_end_dt'].notnull() & (duration_min >= 0)]

print("\n--- Duration (minutes) statistics for valid records ---")
print(valid_durations.describe())

print("\n--- Duration (minutes) statistics by event_cause ---")
for cause in df['event_cause'].unique():
    subset = duration_min[df['effective_end_dt'].notnull() & (df['event_cause'] == cause) & (duration_min >= 0)]
    print(f"{cause}: count={len(subset)}, median={subset.median():.2f} min, mean={subset.mean():.2f} min")
