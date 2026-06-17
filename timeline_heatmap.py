import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import time

class TimelineHeatmapEngine:
    """
    Data Visualization Engine to model, filter, and animate historical traffic congestion
    events over a time timeline (4 PM - 8 PM) in Bengaluru.
    """
    def __init__(self):
        self.events_df = self.generate_historical_data()

    def generate_historical_data(self):
        """Generates realistic Bengaluru spatial-temporal congestion event logs."""
        np.random.seed(42)
        
        # Junction locations in Bengaluru
        junctions = {
            'Silk Board': (12.9176, 77.6246),
            'HSR Layout': (12.9102, 77.6412),
            'Koramangala': (12.9332, 77.6245),
            'BTM Layout': (12.9154, 77.6052),
            'Jayanagar': (12.9282, 77.5891),
            'Hebbal': (13.0362, 77.5975),
            'Indiranagar': (12.9745, 77.6385),
            'Halasuru': (12.9778, 77.6248),
            'Shivajinagar': (12.9856, 77.6035)
        }
        
        data = []
        # Create 100 events distributed between 16:00 (4 PM) and 20:00 (8 PM)
        for i in range(150):
            # Select random base junction
            junc_name, coords = list(junctions.items())[np.random.randint(len(junctions))]
            
            # Add small random coordinate variation
            lat = coords[0] + np.random.normal(0, 0.005)
            lng = coords[1] + np.random.normal(0, 0.005)
            
            # Start/End hour (between 16 and 20)
            start_hour = np.random.randint(16, 21) # 16, 17, 18, 19, 20
            # Event lasts between 1 and 3 hours
            duration = np.random.randint(1, 3)
            end_hour = min(20, start_hour + duration)
            
            # Congestion levels
            # Congestion increases around 6 PM (18:00) peak rush hour
            if start_hour == 18 or start_hour == 19:
                cong_level = np.random.choice(["High", "Medium"], p=[0.7, 0.3])
                delay = np.random.randint(45, 95)
                police = np.random.randint(10, 20)
            elif start_hour == 17:
                cong_level = np.random.choice(["High", "Medium", "Low"], p=[0.3, 0.5, 0.2])
                delay = np.random.randint(30, 60)
                police = np.random.randint(6, 14)
            else:
                cong_level = np.random.choice(["Medium", "Low"], p=[0.4, 0.6])
                delay = np.random.randint(15, 40)
                police = np.random.randint(2, 8)
                
            data.append({
                'event_id': f"EVT-{1000+i}",
                'junction': junc_name,
                'latitude': lat,
                'longitude': lng,
                'start_hour': start_hour,
                'end_hour': end_hour,
                'congestion_level': cong_level,
                'delay_min': delay,
                'police_deployed': police
            })
            
        return pd.DataFrame(data)

    def filter_active_events(self, selected_hour):
        """Filters events that are active during the selected hour."""
        # Active if start_hour <= selected_hour <= end_hour
        mask = (self.events_df['start_hour'] <= selected_hour) & (self.events_df['end_hour'] >= selected_hour)
        return self.events_df[mask]

def render_timeline_heatmap_page():
    """Renders the Streamlit frontend interface for Timeline Replay Heatmap."""
    st.markdown("""
    <div class="main-header">
        <h1>⏰ TIMELINE REPLAY HEATMAP</h1>
        <p>Interactive Spatio-Temporal Congestion Replay & Resource Distribution Dynamics</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize Engine
    if 'timeline_engine' not in st.session_state:
        st.session_state['timeline_engine'] = TimelineHeatmapEngine()
    engine = st.session_state['timeline_engine']

    # Sidebar controls specifically for the playback
    st.sidebar.subheader("Replay Console")
    
    # Hours list mapping
    hours_map = {
        16: "16:00 (4 PM)",
        17: "17:00 (5 PM)",
        18: "18:00 (6 PM)",
        19: "19:00 (7 PM)",
        20: "20:00 (8 PM)"
    }
    reverse_hours_map = {v: k for k, v in hours_map.items()}

    # Active play state logic
    if 'play_active' not in st.session_state:
        st.session_state['play_active'] = False
    if 'current_time_idx' not in st.session_state:
        st.session_state['current_time_idx'] = 16 # Start at 4 PM

    # Action layout
    col_play, col_stop = st.sidebar.columns(2)
    with col_play:
        if st.button("▶ Play Replay"):
            st.session_state['play_active'] = True
    with col_stop:
        if st.button("⏸ Pause"):
            st.session_state['play_active'] = False

    # Slider input
    selected_label = st.select_slider(
        "Select Time Window",
        options=list(hours_map.values()),
        value=hours_map[st.session_state['current_time_idx']],
        key="time_slider"
    )
    
    selected_hour = reverse_hours_map[selected_label]
    st.session_state['current_time_idx'] = selected_hour

    # If playing, run the loop
    if st.session_state['play_active']:
        # Advance the index
        next_hour = selected_hour + 1
        if next_hour > 20:
            next_hour = 16 # Loop back
        st.session_state['current_time_idx'] = next_hour
        # Pause slightly to allow user to view
        time.sleep(1.0)
        st.rerun()

    # Get active events
    active_df = engine.filter_active_events(selected_hour)

    # Calculate metrics
    active_count = len(active_df)
    avg_delay = int(active_df['delay_min'].mean()) if active_count > 0 else 0
    total_police = int(active_df['police_deployed'].sum()) if active_count > 0 else 0

    # Draw summary KPIs
    st.markdown('<div class="section-header">Live Corridor Analytics</div>', unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-box border-info">
            <div class="metric-box-title">Current Time Window</div>
            <div class="metric-box-value">{hours_map[selected_hour]}</div>
            <div class="metric-box-desc">Spatio-temporal playback</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-box border-high" style="border-left: 6px solid #ef4444;">
            <div class="metric-box-title">Active Events</div>
            <div class="metric-box-value">{active_count}</div>
            <div class="metric-box-desc">Junction alerts logged</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-box border-medium">
            <div class="metric-box-title">Average Transit Delay</div>
            <div class="metric-box-value">{avg_delay} mins</div>
            <div class="metric-box-desc">Corridor average</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-box border-low">
            <div class="metric-box-title">Officers Deployed</div>
            <div class="metric-box-value">{total_police} Officers</div>
            <div class="metric-box-desc">Active station dispatch</div>
        </div>
        """, unsafe_allow_html=True)

    # Plot map
    st.markdown('<div class="section-header">Congestion Density Heatmap</div>', unsafe_allow_html=True)
    
    # Initialize Folium Map centered on Bengaluru
    heatmap_map = folium.Map(location=[12.9400, 77.6200], zoom_start=12.2, tiles="cartodbpositron")
    
    # Map congestion levels to heatmap weights
    # Low: 0.3, Medium: 0.6, High: 1.0
    cong_weight_map = {
        'Low': 0.3,
        'Medium': 0.6,
        'High': 1.0
    }
    
    # Build Heatmap coordinate list: [ [lat, lng, weight], ... ]
    heat_data = []
    for _, row in active_df.iterrows():
        weight = cong_weight_map.get(row['congestion_level'], 0.5)
        heat_data.append([row['latitude'], row['longitude'], weight])

    if len(heat_data) > 0:
        # Green (0.2), Yellow (0.5), Red (0.8) gradient scheme
        HeatMap(
            heat_data,
            min_opacity=0.35,
            max_val=1.0,
            radius=25,
            blur=18,
            gradient={0.2: 'green', 0.5: 'yellow', 0.8: 'red'}
        ).add_to(heatmap_map)
        
        # Add normal markers for High congestion nodes to click and inspect
        high_cong_df = active_df[active_df['congestion_level'] == 'High']
        for _, row in high_cong_df.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                color='red',
                fill=True,
                fill_color='darkred',
                fill_opacity=0.7,
                popup=f"🚨 <b>HIGH GRIDLOCK</b><br>Junction: {row['junction']}<br>Delay: {row['delay_min']} mins<br>Police Deployed: {row['police_deployed']}"
            ).add_to(heatmap_map)
            
    else:
        st.info("No active gridlock events in the selected window.")

    st_folium(heatmap_map, width="100%", height=450)

    # Display active event breakdown details
    st.markdown('<div class="section-header">Active Event Logs breakdown</div>', unsafe_allow_html=True)
    st.dataframe(
        active_df[['event_id', 'junction', 'congestion_level', 'delay_min', 'police_deployed']],
        use_container_width=True
    )
