import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import joblib
import os

# Page configuration
st.set_page_config(
    page_title="Bengaluru Congestion Heatmap & Resource Dashboard",
    page_icon="🗺️",
    layout="wide"
)

# Custom styling for high-fidelity look
st.markdown("""
<style>
    .header-style {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 25px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header-style h1 {
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        margin: 0;
    }
    .header-style p {
        color: #cbd5e1;
        font-size: 1rem;
        margin-top: 5px;
        margin-bottom: 0;
    }
    .card-metric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. LOAD DATA & MODEL
# -------------------------------------------------------------
@st.cache_data
def load_data():
    file_path = "processed_congestion_data.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # Filter for valid Bengaluru coordinates
        df = df[
            (df['latitude'] >= 12.8) & (df['latitude'] <= 13.2) &
            (df['longitude'] >= 77.4) & (df['longitude'] <= 77.8)
        ].copy()
        return df
    return pd.DataFrame()

@st.cache_resource
def load_model():
    model_path = "congestion_model.joblib"
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

df_raw = load_data()
model = load_model()

# -------------------------------------------------------------
# 2. RUN VECTORIZED LOGISTICS PREDICTIONS
# -------------------------------------------------------------
def enrich_dataset(df):
    if df.empty:
        return df
        
    # Map raw CSV columns to expected model pipeline features
    df['day_of_week'] = df['weekday']
    df['duration_hours'] = df['duration_minutes'] / 60.0
        
    # Predict congestion level if model is loaded
    if model is not None:
        try:
            # Map features expected by model pipeline
            feature_cols = ['event_type', 'event_cause', 'priority', 'requires_road_closure', 
                            'hour', 'day_of_week', 'duration_hours', 'zone', 'junction']
            # Fill NaNs for safety
            df_features = df[feature_cols].copy()
            class_names = ["Low", "Medium", "High"]
            preds = model.predict(df_features)
            df['congestion_level'] = [class_names[p] for p in preds]
        except Exception as e:
            st.sidebar.warning(f"Model prediction failed, falling back to proxy labels. Error: {e}")
            df['congestion_level'] = df['congestion_proxy_label']
    else:
        df['congestion_level'] = df['congestion_proxy_label']
        
    # Vectorized calculations for expected delay
    df['expected_delay_min'] = 0
    df.loc[df['congestion_level'] == 'Low', 'expected_delay_min'] = (df['duration_hours'] * 60 * 0.25).clip(5, 45)
    df.loc[df['congestion_level'] == 'Medium', 'expected_delay_min'] = (df['duration_hours'] * 60 * 0.75).clip(15, 120)
    df.loc[df['congestion_level'] == 'High', 'expected_delay_min'] = (df['duration_hours'] * 60 * 1.5).clip(30, 240)
    df['expected_delay_min'] = df['expected_delay_min'].astype(int)

    # Vectorized calculations for police personnel needed
    df['police_needed'] = 2
    df.loc[df['congestion_level'] == 'Medium', 'police_needed'] = 4
    df.loc[df['congestion_level'] == 'High', 'police_needed'] = 8
    
    # Priority & Closure modifiers
    df.loc[df['priority'].str.lower() == 'high', 'police_needed'] += 2
    df.loc[df['requires_road_closure'] == True, 'police_needed'] += 4
    df['police_needed'] = df['police_needed'].clip(upper=20)

    # Vectorized calculations for barricades needed
    df['barricades_needed'] = 2
    df.loc[df['congestion_level'] == 'Medium', 'barricades_needed'] = 6
    df.loc[df['congestion_level'] == 'High', 'barricades_needed'] = 12
    
    # Closure modifier
    df.loc[df['requires_road_closure'] == True, 'barricades_needed'] += 8
    df['barricades_needed'] = df['barricades_needed'].clip(upper=30)
    
    return df

df_enriched = enrich_dataset(df_raw.copy())

# -------------------------------------------------------------
# 3. SIDEBAR FILTERS
# -------------------------------------------------------------
st.sidebar.title("Dashboard Control Panel")

if not df_enriched.empty:
    # Filter by Event Type
    event_types = st.sidebar.multiselect(
        "Event Type",
        options=list(df_enriched['event_type'].unique()),
        default=list(df_enriched['event_type'].unique())
    )
    
    # Filter by Congestion Level
    congestion_levels = st.sidebar.multiselect(
        "Congestion Severity",
        options=["Low", "Medium", "High"],
        default=["Low", "Medium", "High"]
    )
    
    # Filter by Zone
    zones = st.sidebar.multiselect(
        "Administrative Zone",
        options=list(df_enriched['zone'].unique()),
        default=list(df_enriched['zone'].unique())
    )
    
    # Map marker rendering cap
    map_cap = st.sidebar.slider(
        "Max Event Pins to Plot",
        min_value=10,
        max_value=1000,
        value=200,
        step=10,
        help="Capping markers prevents browser lag while rendering Folium maps."
    )
    
    # Apply filters
    df_filtered = df_enriched[
        df_enriched['event_type'].isin(event_types) &
        df_enriched['congestion_level'].isin(congestion_levels) &
        df_enriched['zone'].isin(zones)
    ].copy()
    
else:
    df_filtered = pd.DataFrame()

# -------------------------------------------------------------
# 4. MAIN LAYOUT
# -------------------------------------------------------------
st.markdown("""
<div class="header-style">
    <h1>BENGALURU EVENT-DRIVEN CONGESTION CONTROL CENTER</h1>
    <p>Live Spatial Hotspot Mapping & Police Resource Optimizations</p>
</div>
""", unsafe_allow_html=True)

if df_filtered.empty:
    st.warning("⚠️ No data matches the selected filters. Please expand your sidebar criteria.")
else:
    # Metrics Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f"""
        <div class="card-metric" style="border-top-color: #3b82f6;">
            <div style="font-size: 0.85rem; color:#64748b; text-transform:uppercase; font-weight:600;">Total Logged Events</div>
            <div style="font-size: 1.8rem; font-weight:700; color:#0f172a;">{len(df_filtered)}</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        high_pct = (len(df_filtered[df_filtered['congestion_level']=='High']) / len(df_filtered)) * 100
        st.markdown(f"""
        <div class="card-metric" style="border-top-color: #ef4444;">
            <div style="font-size: 0.85rem; color:#64748b; text-transform:uppercase; font-weight:600;">High Severity Ratio</div>
            <div style="font-size: 1.8rem; font-weight:700; color:#0f172a;">{high_pct:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        avg_delay = df_filtered['expected_delay_min'].mean()
        st.markdown(f"""
        <div class="card-metric" style="border-top-color: #f59e0b;">
            <div style="font-size: 0.85rem; color:#64748b; text-transform:uppercase; font-weight:600;">Average Queue Delay</div>
            <div style="font-size: 1.8rem; font-weight:700; color:#0f172a;">{avg_delay:.1f} mins</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col4:
        total_police = df_filtered['police_needed'].sum()
        st.markdown(f"""
        <div class="card-metric" style="border-top-color: #10b981;">
            <div style="font-size: 0.85rem; color:#64748b; text-transform:uppercase; font-weight:600;">Total Police Mobilized</div>
            <div style="font-size: 1.8rem; font-weight:700; color:#0f172a;">{total_police:,}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------
    # 5. FOLIUM MAP GENERATION
    # -------------------------------------------------------------
    # Center map on average coordinate of filtered events
    center_lat = df_filtered['latitude'].mean()
    center_lng = df_filtered['longitude'].mean()
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12,
        tiles="cartodbpositron"
    )
    
    # Create Feature Groups
    marker_group = folium.FeatureGroup(name="Incident Pin Markers")
    heatmap_group = folium.FeatureGroup(name="Density Heatmap")
    
    # A. Add Heatmap Layer
    heat_data = df_filtered[['latitude', 'longitude']].values.tolist()
    HeatMap(heat_data, radius=15, blur=10, min_opacity=0.4).add_to(heatmap_group)
    
    # B. Add Pin Markers (Sampled up to map_cap to prevent browser lock)
    df_pins = df_filtered.sample(min(map_cap, len(df_filtered)), random_state=42)
    color_map = {'Low': 'green', 'Medium': 'orange', 'High': 'red'}
    
    for _, row in df_pins.iterrows():
        # Setup popup text
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; width: 200px;">
            <h4 style="margin: 0 0 8px 0; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">Incident Logistics</h4>
            <b>Event Type:</b> {row['event_type']}<br>
            <b>Priority:</b> {row['priority']}<br>
            <b>Congestion:</b> <span style="color:{color_map.get(row['congestion_level'], 'blue')}; font-weight:bold;">{row['congestion_level']}</span><br>
            <b>Predicted Delay:</b> {row['expected_delay_min']} mins<br>
            <b>Police Needed:</b> {row['police_needed']} officers<br>
            <b>Barricades:</b> {row['barricades_needed']} units
        </div>
        """
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=color_map.get(row['congestion_level'], 'blue'), icon='warning-sign', prefix='glyphicon')
        ).add_to(marker_group)
        
    # Add groups to map
    heatmap_group.add_to(m)
    marker_group.add_to(m)
    
    # Add Layer Control so user can turn on/off Heatmap or Pins
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Render Map
    st_folium(m, width="100%", height=600)
    
    # Data table preview
    st.subheader("Filtered Event Logs Detail")
    display_cols = ['event_type', 'event_cause', 'priority', 'zone', 'junction', 
                    'congestion_level', 'expected_delay_min', 'police_needed', 'barricades_needed']
    st.dataframe(df_filtered[display_cols], use_container_width=True)
