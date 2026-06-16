import pandas as pd
import numpy as np

# Load dataset
file_path = r"u:\Theme2\Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
df = pd.read_csv(file_path)

print("--- Basic Info ---")
print(df.info())

print("\n--- Missing Values ---")
cols_to_check = [
    'event_type', 'event_cause', 'priority', 'requires_road_closure', 
    'zone', 'junction', 'start_datetime', 'end_datetime', 'latitude', 'longitude',
    'closed_datetime', 'resolved_datetime'
]
for col in cols_to_check:
    if col in df.columns:
        missing = df[col].isnull().sum()
        pct = (missing / len(df)) * 100
        print(f"{col}: {missing} missing ({pct:.2f}%)")
    else:
        print(f"{col}: COLUMN NOT FOUND")

print("\n--- Value Counts for Categorical Columns ---")
for col in ['event_type', 'event_cause', 'priority', 'requires_road_closure', 'zone']:
    if col in df.columns:
        print(f"\n{col} unique values:")
        print(df[col].value_counts(dropna=False).head(10))

print("\n--- Timestamp Samples ---")
for col in ['start_datetime', 'end_datetime', 'closed_datetime', 'resolved_datetime']:
    if col in df.columns:
        print(f"\n{col} samples:")
        print(df[col].dropna().head(5))
