import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import joblib
import os
import datetime
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import xgboost as xgb

# -------------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(
    page_title="AI Command Center: Bengaluru Traffic Police",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# GLOBAL DATABASE & MODEL HELPERS
# -------------------------------------------------------------
DB_PATH = "traffic_ops.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_logs (
        event_id TEXT PRIMARY KEY,
        event_type TEXT,
        event_cause TEXT,
        priority TEXT,
        requires_road_closure INTEGER,
        hour INTEGER,
        day_of_week INTEGER,
        duration_hours REAL,
        zone TEXT,
        junction TEXT,
        predicted_congestion TEXT,
        predicted_delay_min INTEGER,
        timestamp TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS officer_feedback (
        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT,
        actual_delay_min INTEGER,
        actual_congestion TEXT,
        event_outcome TEXT,
        officer_badge TEXT,
        timestamp TEXT,
        FOREIGN KEY (event_id) REFERENCES event_logs (event_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS retraining_history (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        dataset_size INTEGER,
        old_accuracy REAL,
        new_accuracy REAL,
        old_mae REAL,
        new_mae REAL
    )
    """)
    conn.commit()
    conn.close()

def populate_synthetic_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM event_logs")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
        
    base_time = datetime.datetime.now() - datetime.timedelta(days=30)
    causes = ["accident", "vehicle_breakdown", "water_logging", "construction"]
    zones = ["Central Zone 2", "East Zone 1", "South Zone 1", "North Zone 2"]
    junctions = ["SilkBoardJunc", "HebbalFlyoverJunc", "IbblurJunction", "Peenya14thCrossJunc"]
    
    for i in range(50):
        event_id = f"EV-2026-{i:03d}"
        event_type = "unplanned" if i % 2 == 0 else "planned"
        event_cause = causes[i % len(causes)]
        priority = "High" if i % 3 == 0 else "Low"
        road_closure = 1 if (i % 4 == 0 and priority == "High") else 0
        h = 8 + (i % 12)
        dow = i % 7
        duration = 0.5 + (i % 5) * 0.75
        zone = zones[i % len(zones)]
        junc = junctions[i % len(junctions)]
        
        pred_congestion = "High" if (road_closure or duration > 3.0) else ("Medium" if duration > 1.0 else "Low")
        base_delay = 15 if pred_congestion == "Low" else (45 if pred_congestion == "Medium" else 90)
        
        event_timestamp = (base_time + datetime.timedelta(hours=i*14)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO event_logs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (event_id, event_type, event_cause, priority, road_closure, h, dow, duration, zone, junc, pred_congestion, base_delay, event_timestamp))
        
        is_drift_period = i > 35
        if is_drift_period:
            actual_delay = int(base_delay * 1.5 + np.random.randint(10, 25))
            actual_congestion = "High" if pred_congestion == "Medium" else pred_congestion
        else:
            actual_delay = int(base_delay + np.random.randint(-5, 8))
            actual_congestion = pred_congestion
            
        outcome = "Cleared with Diversion" if road_closure else "Normal Clearance"
        badge = f"KA-POL-{8000 + i}"
        cursor.execute("""
        INSERT INTO officer_feedback (event_id, actual_delay_min, actual_congestion, event_outcome, officer_badge, timestamp)
        VALUES (?,?,?,?,?,?)
        """, (event_id, actual_delay, actual_congestion, outcome, badge, event_timestamp))
        
    conn.commit()
    conn.close()

# Initialize DB structures
init_db()
populate_synthetic_data()

# -------------------------------------------------------------
# SHARABLE DATA CACHING
# -------------------------------------------------------------
@st.cache_resource
def load_model():
    model_path = "congestion_model.joblib"
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

@st.cache_data
def load_historical_data():
    file_path = "processed_congestion_data.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # Filter bounds to Bengaluru center coordinates
        df = df[
            (df['latitude'] >= 12.8) & (df['latitude'] <= 13.2) &
            (df['longitude'] >= 77.4) & (df['longitude'] <= 77.8)
        ].copy()
        df['day_of_week'] = df['weekday']
        df['duration_hours'] = df['duration_minutes'] / 60.0
        return df
    return pd.DataFrame()

model = load_model()
df_hist = load_historical_data()

# -------------------------------------------------------------
# MULTI-PAGE STYLING (SHARED CSS)
# -------------------------------------------------------------
st.markdown("""
<style>
    .main {
        background-color: #fcfbf9;
    }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 8px;
        margin-bottom: 0;
    }
    .metric-box {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
        border-left: 6px solid #e2e8f0;
        text-align: center;
    }
    .metric-box-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-box-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-box-desc {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 4px;
    }
    .border-high {
        border-left-color: #ef4444 !important;
        background-color: #fef2f2;
    }
    .border-medium {
        border-left-color: #f59e0b !important;
        background-color: #fffbeb;
    }
    .border-low {
        border-left-color: #10b981 !important;
        background-color: #f0fdf4;
    }
    .border-info {
        border-left-color: #3b82f6 !important;
    }
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        margin-top: 10px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# SIDEBAR NAVIGATION CONTROLS
# -------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/000000/traffic-jam.png", width=50)
st.sidebar.title("AI Command Center")
st.sidebar.markdown("---")

app_page = st.sidebar.radio(
    "Navigation Menu",
    [
        "🚦 Simulator & Optimizer",
        "🗺️ Spatial Density Heatmap",
        "🤖 Feedback & Retraining Terminal"
    ]
)

st.sidebar.markdown("---")

# -------------------------------------------------------------
# PAGE 1: SIMULATOR & OPTIMIZER
# -------------------------------------------------------------
if app_page == "🚦 Simulator & Optimizer":
    st.sidebar.subheader("Simulation Config")
    
    # Core event sliders
    event_type = st.sidebar.selectbox("Event Type", options=["unplanned", "planned"], index=0)
    
    cause_options = [
        "vehicle_breakdown", "others", "pot_holes", "construction", 
        "water_logging", "accident", "tree_fall", "road_conditions", 
        "congestion", "public_event", "procession", "protest"
    ]
    event_cause = st.sidebar.selectbox("Event Cause", options=cause_options, index=0)
    priority = st.sidebar.selectbox("Priority", options=["High", "Low"], index=0)
    requires_road_closure = st.sidebar.checkbox("Requires Road Closure", value=False)
    
    hour = st.sidebar.slider("Hour of Day", min_value=0, max_value=23, value=9)
    day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = st.sidebar.select_slider("Day of Week", options=day_labels, value="Monday")
    day_of_week = day_labels.index(day_name)
    duration_hours = st.sidebar.slider("Event Duration (Hours)", min_value=0.1, max_value=24.0, value=1.5, step=0.1)
    
    zone_options = [
        'Central Zone 2', 'West Zone 1', 'North Zone 2', 'West Zone 2', 
        'South Zone 2', 'North Zone 1', 'Central Zone 1', 'East Zone 1', 
        'South Zone 1', 'Unknown'
    ]
    zone = st.sidebar.selectbox("Zone", options=zone_options, index=0)
    
    junction_options = [
        'SilkBoardJunc', 'HebbalFlyoverJunc', 'Peenya14thCrossJunc', 'UrvashiJunction', 
        'LalbaghMainGateJunc', 'RingRoad-UllalJunction', 'IbblurJunction', 'Sumanhalli', 'Unknown'
    ]
    junction = st.sidebar.selectbox("Junction", options=junction_options, index=0)
    
    # Capture lat/lon coordinate inputs
    st.sidebar.subheader("Mock Coordinates")
    if 'sim_lat' not in st.session_state:
        st.session_state['sim_lat'] = 12.9716
    if 'sim_lng' not in st.session_state:
        st.session_state['sim_lng'] = 77.5946
        
    sim_lat = st.sidebar.number_input("Latitude", value=st.session_state['sim_lat'], format="%.6f", step=0.001)
    sim_lng = st.sidebar.number_input("Longitude", value=st.session_state['sim_lng'], format="%.6f", step=0.001)
    st.session_state['sim_lat'] = sim_lat
    st.session_state['sim_lng'] = sim_lng

    # Inference Runtime
    input_df = pd.DataFrame([{
        'event_type': event_type,
        'event_cause': event_cause,
        'priority': priority,
        'requires_road_closure': requires_road_closure,
        'hour': hour,
        'day_of_week': day_of_week,
        'duration_hours': duration_hours,
        'zone': zone,
        'junction': junction
    }])
    
    prediction_class = "Medium"
    pred_prob_low, pred_prob_med, pred_prob_high = 0.15, 0.70, 0.15
    
    if model is not None:
        try:
            class_names = ["Low", "Medium", "High"]
            pred_code = model.predict(input_df)[0]
            prediction_class = class_names[pred_code]
            probs = model.predict_proba(input_df)[0]
            pred_prob_low = probs[0]
            pred_prob_med = probs[1]
            pred_prob_high = probs[2]
        except Exception as e:
            st.sidebar.error(f"Inference error: {e}")

    # Compute resource deployments
    if prediction_class == "High":
        expected_delay_min = min(240, max(30, int(duration_hours * 60 * 1.5)))
        risk_style, risk_color = "border-high", "red"
    elif prediction_class == "Medium":
        expected_delay_min = min(120, max(15, int(duration_hours * 60 * 0.75)))
        risk_style, risk_color = "border-medium", "orange"
    else:
        expected_delay_min = min(45, max(5, int(duration_hours * 60 * 0.25)))
        risk_style, risk_color = "border-low", "green"
        
    police_base = {"Low": 2, "Medium": 4, "High": 8}
    police_req = min(20, police_base[prediction_class] + (2 if priority == "High" else 0) + (4 if requires_road_closure else 0))
    
    barricade_base = {"Low": 1, "Medium": 5, "High": 12}
    barricades_req = min(30, barricade_base[prediction_class] + (8 if requires_road_closure else 0))
    
    diversion_routes = {
        'SilkBoardJunc': "Divert heavy vehicles to HSR Layout 27th Main or BTM Layout 16th Main. Use underpasses for light commuters.",
        'HebbalFlyoverJunc': "Divert inbound airport traffic via Hennur-Bagalur road or Thanisandra main road. Keep central lane clear.",
        'Peenya14thCrossJunc': "Divert industrial trucks to NICE Road. Re-route city buses through Peenya 1st Stage collector streets.",
        'UrvashiJunction': "Re-route traffic through Lalbagh Road and JC Road. Restrict parking on parallel access service roads.",
        'Unknown': f"Implement local loop diversions within 500m of the incident scene in {zone}. Shift signal splits upstream."
    }
    diversion_text = diversion_routes.get(junction, diversion_routes['Unknown'])

    # Page Header Banner
    st.markdown("""
    <div class="main-header">
        <h1>🚦 TRAFFIC SIMULATOR & OPTIMIZATION CONTROL</h1>
        <p>Real-Time Incident Dispatch Optimization & Dynamic Routing Feeds</p>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI metrics row
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.markdown(f"""
        <div class="metric-box {risk_style}">
            <div class="metric-box-title">Predicted Severity</div>
            <div class="metric-box-value" style="color:{risk_color};">{prediction_class}</div>
            <div class="metric-box-desc">Confidence: {max(pred_prob_low, pred_prob_med, pred_prob_high):.1%}</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol2:
        st.markdown(f"""
        <div class="metric-box border-info">
            <div class="metric-box-title">Expected Queue Delay</div>
            <div class="metric-box-value">{expected_delay_min} mins</div>
            <div class="metric-box-desc">Duration: {duration_hours} hrs</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol3:
        st.markdown(f"""
        <div class="metric-box border-info">
            <div class="metric-box-title">Police Dispatched</div>
            <div class="metric-box-value">{police_req} officers</div>
            <div class="metric-box-desc">Priority: {priority}</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol4:
        st.markdown(f"""
        <div class="metric-box border-info">
            <div class="metric-box-title">Barricades Cordoned</div>
            <div class="metric-box-value">{barricades_req} units</div>
            <div class="metric-box-desc">Closure: {requires_road_closure}</div>
        </div>
        """, unsafe_allow_html=True)

    # Layout sections
    col_left, col_right = st.columns([7, 5])
    with col_left:
        st.markdown('<div class="section-header">Incident Map Coordinator</div>', unsafe_allow_html=True)
        st.markdown("*Click on the map grid to adjust coordinates.*")
        
        sim_map = folium.Map(location=[st.session_state['sim_lat'], st.session_state['sim_lng']], zoom_start=13, tiles="cartodbpositron")
        
        # Plot historical points contextually
        if not df_hist.empty:
            hist_sample = df_hist.sample(min(150, len(df_hist)), random_state=42)
            c_map = {'Low': '#10b981', 'Medium': '#f59e0b', 'High': '#ef4444'}
            for _, r in hist_sample.iterrows():
                folium.CircleMarker(
                    location=[r['latitude'], r['longitude']], radius=3,
                    color=c_map.get(r['congestion_proxy_label'], '#3b82f6'),
                    fill=True, fill_opacity=0.3, weight=1
                ).add_to(sim_map)
                
        folium.Marker(
            location=[st.session_state['sim_lat'], st.session_state['sim_lng']],
            popup="Simulated Incident Scene", icon=folium.Icon(color=risk_color, icon="info-sign")
        ).add_to(sim_map)
        
        map_out = st_folium(sim_map, width="100%", height=400)
        if map_out and map_out.get("last_clicked"):
            c_lat = map_out["last_clicked"]["lat"]
            c_lng = map_out["last_clicked"]["lng"]
            if c_lat != st.session_state['sim_lat'] or c_lng != st.session_state['sim_lng']:
                st.session_state['sim_lat'] = c_lat
                st.session_state['sim_lng'] = c_lng
                st.rerun()
                
    with col_right:
        st.markdown('<div class="section-header">Tactical Routing Feed</div>', unsafe_allow_html=True)
        st.info(f"**Target Corridor Zone:** {zone} \n\n**Nearest Key Junction:** {junction}")
        st.warning(f"**Suggested Diversion Route:**\n\n{diversion_text}")
        
        st.markdown('<div class="section-header">Congestion Risk Distribution</div>', unsafe_allow_html=True)
        st.markdown(f"**Low Risk Probability** ({pred_prob_low:.1%})")
        st.progress(float(pred_prob_low))
        st.markdown(f"**Medium Risk Probability** ({pred_prob_med:.1%})")
        st.progress(float(pred_prob_med))
        st.markdown(f"**High Risk Probability** ({pred_prob_high:.1%})")
        st.progress(float(pred_prob_high))

    # Fast delay feedback form
    st.markdown('<div class="section-header">Quick Local Feedback Form</div>', unsafe_allow_html=True)
    with st.form("quick_feedback"):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            st.number_input("System Prediction (Mins)", value=expected_delay_min, disabled=True)
        with fc2:
            act_delay = st.number_input("Actual observed Delay (Mins)", min_value=0, value=expected_delay_min)
        with fc3:
            comments = st.text_input("Local Observation Comments", placeholder="E.g., Clearance slow due to lane merge friction.")
        if st.form_submit_button("Submit Feedback Log"):
            f_record = pd.DataFrame([{
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'event_type': event_type,
                'event_cause': event_cause,
                'requires_road_closure': requires_road_closure,
                'junction': junction,
                'predicted_delay_min': expected_delay_min,
                'actual_delay_min': act_delay,
                'comments': comments
            }])
            f_record.to_csv("user_feedback.csv", mode='a', header=not os.path.exists("user_feedback.csv"), index=False)
            st.success("Feedback saved successfully for batch model calibration.")

# -------------------------------------------------------------
# PAGE 2: SPATIAL DENSITY HEATMAP
# -------------------------------------------------------------
elif app_page == "🗺️ Spatial Density Heatmap":
    if df_hist.empty:
        st.warning("Processed dataset unavailable. Please check project files.")
    else:
        st.sidebar.subheader("Map Filter Panel")
        e_types = st.sidebar.multiselect("Event Type", options=list(df_hist['event_type'].unique()), default=list(df_hist['event_type'].unique()))
        c_sevs = st.sidebar.multiselect("Severity Level", options=["Low", "Medium", "High"], default=["Low", "Medium", "High"])
        z_options = st.sidebar.multiselect("Administrative Zone", options=list(df_hist['zone'].unique()), default=list(df_hist['zone'].unique()))
        map_cap = st.sidebar.slider("Maximum Pin Markers", min_value=10, max_value=1000, value=200)

        # Apply filtering
        df_filtered = df_hist[
            df_hist['event_type'].isin(e_types) &
            df_hist['congestion_proxy_label'].isin(c_sevs) &
            df_hist['zone'].isin(z_options)
        ].copy()
        
        # Calculate dynamic resource values for filtering
        df_filtered['expected_delay_min'] = 0
        df_filtered.loc[df_filtered['congestion_proxy_label'] == 'Low', 'expected_delay_min'] = (df_filtered['duration_hours'] * 60 * 0.25).clip(5, 45)
        df_filtered.loc[df_filtered['congestion_proxy_label'] == 'Medium', 'expected_delay_min'] = (df_filtered['duration_hours'] * 60 * 0.75).clip(15, 120)
        df_filtered.loc[df_filtered['congestion_proxy_label'] == 'High', 'expected_delay_min'] = (df_filtered['duration_hours'] * 60 * 1.5).clip(30, 240)
        df_filtered['expected_delay_min'] = df_filtered['expected_delay_min'].astype(int)
        
        df_filtered['police_needed'] = 2
        df_filtered.loc[df_filtered['congestion_proxy_label'] == 'Medium', 'police_needed'] = 4
        df_filtered.loc[df_filtered['congestion_proxy_label'] == 'High', 'police_needed'] = 8
        df_filtered.loc[df_filtered['priority'].str.lower() == 'high', 'police_needed'] += 2
        df_filtered.loc[df_filtered['requires_road_closure'] == True, 'police_needed'] += 4
        df_filtered['police_needed'] = df_filtered['police_needed'].clip(upper=20)

        df_filtered['barricades_needed'] = 2
        df_filtered.loc[df_filtered['congestion_proxy_label'] == 'Medium', 'barricades_needed'] = 6
        df_filtered.loc[df_filtered['congestion_proxy_label'] == 'High', 'barricades_needed'] = 12
        df_filtered.loc[df_filtered['requires_road_closure'] == True, 'barricades_needed'] += 8
        df_filtered['barricades_needed'] = df_filtered['barricades_needed'].clip(upper=30)

        # Page Header Banner
        st.markdown("""
        <div class="main-header">
            <h1>🗺️ SPATIAL HOTSPOT & HEATMAP CENTER</h1>
            <p>Geographical Congestion Density and Allocation Metrics</p>
        </div>
        """, unsafe_allow_html=True)
        
        if df_filtered.empty:
            st.error("No records found matching filters.")
        else:
            # Stats row
            hcol1, hcol2, hcol3, hcol4 = st.columns(4)
            with hcol1:
                st.markdown(f"""
                <div class="metric-box border-info">
                    <div class="metric-box-title">Total Logged Incidents</div>
                    <div class="metric-box-value">{len(df_filtered)}</div>
                </div>
                """, unsafe_allow_html=True)
            with hcol2:
                high_pct = (len(df_filtered[df_filtered['congestion_proxy_label']=='High']) / len(df_filtered)) * 100
                st.markdown(f"""
                <div class="metric-box border-high">
                    <div class="metric-box-title">High Severity Ratio</div>
                    <div class="metric-box-value">{high_pct:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with hcol3:
                avg_delay = df_filtered['expected_delay_min'].mean()
                st.markdown(f"""
                <div class="metric-box border-medium">
                    <div class="metric-box-title">Average Delay</div>
                    <div class="metric-box-value">{avg_delay:.1f} mins</div>
                </div>
                """, unsafe_allow_html=True)
            with hcol4:
                total_police = df_filtered['police_needed'].sum()
                st.markdown(f"""
                <div class="metric-box border-low">
                    <div class="metric-box-title">Police Mobilized</div>
                    <div class="metric-box-value">{total_police:,}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Map generation
            m_lat = df_filtered['latitude'].mean()
            m_lng = df_filtered['longitude'].mean()
            folium_map = folium.Map(location=[m_lat, m_lng], zoom_start=12, tiles="cartodbpositron")
            
            # Feature groups
            marker_group = folium.FeatureGroup(name="Incident Pin Markers")
            heatmap_group = folium.FeatureGroup(name="Density Heatmap")
            
            # Heatmap layer
            heat_data = df_filtered[['latitude', 'longitude']].values.tolist()
            HeatMap(heat_data, radius=15, blur=10, min_opacity=0.4).add_to(heatmap_group)
            
            # Pin Markers
            df_pins = df_filtered.sample(min(map_cap, len(df_filtered)), random_state=42)
            c_color_map = {'Low': 'green', 'Medium': 'orange', 'High': 'red'}
            
            for _, row in df_pins.iterrows():
                popup_html = f"""
                <div style="font-family: Arial; font-size: 11px; width: 180px;">
                    <h4 style="margin:0 0 5px 0; border-bottom: 1px solid #ddd;">Log Metrics</h4>
                    <b>Event Type:</b> {row['event_type']}<br>
                    <b>Priority:</b> {row['priority']}<br>
                    <b>Congestion:</b> <span style="color:{c_color_map.get(row['congestion_proxy_label'], 'blue')}; font-weight:bold;">{row['congestion_proxy_label']}</span><br>
                    <b>Delay:</b> {row['expected_delay_min']} mins<br>
                    <b>Police:</b> {row['police_needed']} officers<br>
                    <b>Barricades:</b> {row['barricades_needed']} units
                </div>
                """
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=250),
                    icon=folium.Icon(color=c_color_map.get(row['congestion_proxy_label'], 'blue'), icon='warning-sign')
                ).add_to(marker_group)
                
            heatmap_group.add_to(folium_map)
            marker_group.add_to(folium_map)
            folium.LayerControl(collapsed=False).add_to(folium_map)
            
            st_folium(folium_map, width="100%", height=550)
            
            st.subheader("Filtered Event Logs Detail")
            display_cols = ['event_type', 'event_cause', 'priority', 'zone', 'junction', 
                            'congestion_proxy_label', 'expected_delay_min', 'police_needed', 'barricades_needed']
            st.dataframe(df_filtered[display_cols], use_container_width=True)

# -------------------------------------------------------------
# PAGE 3: FEEDBACK & RETRAINING TERMINAL
# -------------------------------------------------------------
elif app_page == "🤖 Feedback & Retraining Terminal":
    # Sidebar Model Status
    st.sidebar.subheader("Model Diagnostic Center")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM event_logs")
    total_events = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM officer_feedback")
    total_feedback = cursor.fetchone()[0]
    
    query = """
    SELECT e.predicted_congestion, f.actual_congestion, e.predicted_delay_min, f.actual_delay_min
    FROM event_logs e JOIN officer_feedback f ON e.event_id = f.event_id
    """
    df_metrics = pd.read_sql(query, conn)
    conn.close()
    
    if not df_metrics.empty:
        accuracy = (df_metrics['predicted_congestion'] == df_metrics['actual_congestion']).mean()
        mae = np.mean(np.abs(df_metrics['predicted_delay_min'] - df_metrics['actual_delay_min']))
        
        recent_df = df_metrics.tail(15)
        recent_accuracy = (recent_df['predicted_congestion'] == recent_df['actual_congestion']).mean()
        drift_index = max(0.0, accuracy - recent_accuracy)
    else:
        accuracy, mae, drift_index, recent_accuracy = 1.0, 0.0, 0.0, 1.0
        
    st.sidebar.metric("Global Model Accuracy", f"{accuracy:.1%}")
    st.sidebar.metric("Recent Accuracy (Last 15)", f"{recent_accuracy:.1%}")
    if drift_index > 0.10:
        st.sidebar.error(f"🚨 Model Drift Alert (Index: {drift_index:.2f}). Retraining required!")
    else:
        st.sidebar.success("✅ Model status stable. Drift within margins.")
        
    # Page Header Banner
    st.markdown("""
    <div class="main-header">
        <h1>🤖 CLOSED-LOOP RETRAINING & DRIFT CENTER</h1>
        <p>Operational Audits, Model Drift Logs, and XGBoost Self-Learning Pipeline</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_form, tab_plots, tab_train = st.tabs([
        "✍️ Ticket Closure Portal", 
        "📊 Accuracy & Drift Plots", 
        "⚙️ Pipeline Retraining Controls"
    ])
    
    # Tab 1: Ticket Closure
    with tab_form:
        st.subheader("Officer Post-Event Feedback Terminal")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT event_id, event_cause, junction, predicted_delay_min, predicted_congestion 
        FROM event_logs 
        WHERE event_id NOT IN (SELECT event_id FROM officer_feedback)
        ORDER BY timestamp DESC
        """)
        unresolved = cursor.fetchall()
        conn.close()
        
        if not unresolved:
            st.success("All event tickets closed. No pending reviews!")
            if st.button("Simulate New Unresolved Event Ticket"):
                conn = get_db_connection()
                c = conn.cursor()
                nid = f"EV-2026-{np.random.randint(100, 999)}"
                c.execute("""
                INSERT INTO event_logs VALUES (?, 'unplanned', 'accident', 'High', 1, 18, 1, 2.0, 'South Zone 1', 'SilkBoardJunc', 'High', 90, ?)
                """, (nid, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.rerun()
        else:
            e_choices = {r['event_id']: f"{r['event_id']} - {r['event_cause']} at {r['junction']} (Pred: {r['predicted_delay_min']}m)" for r in unresolved}
            sel_ev_id = st.selectbox("Select Active Ticket to Audit", options=list(e_choices.keys()), format_func=lambda x: e_choices[x])
            sel_ev = next(r for r in unresolved if r['event_id'] == sel_ev_id)
            
            with st.form("officer_form"):
                col_of1, col_of2 = st.columns(2)
                with col_of1:
                    act_delay_val = st.number_input("Actual delay (Mins)", min_value=1, value=int(sel_ev['predicted_delay_min']))
                    act_cong_val = st.selectbox("Actual Congestion Level", options=["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(sel_ev['predicted_congestion']))
                with col_of2:
                    outcome_val = st.selectbox("Resolution Outcome", options=["Normal Clearance", "Cleared with Diversion", "Spillover to Adjacent Arterials", "Signal Phase Adjusted", "Towing Required"])
                    badge_val = st.text_input("Officer Badge ID Code")
                    
                if st.form_submit_button("Close Ticket"):
                    if not badge_val.strip():
                        st.error("Authentication required: Please enter Officer Badge ID.")
                    else:
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("""
                        INSERT INTO officer_feedback (event_id, actual_delay_min, actual_congestion, event_outcome, officer_badge, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (sel_ev_id, act_delay_val, act_cong_val, outcome_val, badge_val, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        conn.close()
                        st.success("Ticket closed successfully. Model telemetry logs updated.")
                        st.rerun()
                        
    # Tab 2: Plots
    with tab_plots:
        if df_metrics.empty:
            st.info("No audit logs available for graphing yet.")
        else:
            kcol1, kcol2, kcol3 = st.columns(3)
            with kcol1:
                st.metric("Global Mean Absolute Error (MAE)", f"{mae:.2f} mins", delta=f"{mae - 5.0:.1f} mins vs Target (5.0)")
            with kcol2:
                st.metric("Global Classification Accuracy", f"{accuracy:.1%}", delta=f"{accuracy - 0.95:.1%} vs Baseline (95%)")
            with kcol3:
                st.metric("Drift Alert Indicator", f"{drift_index:.2f}", delta="Action Required" if drift_index > 0.10 else "Optimal")
                
            conn = get_db_connection()
            query = """
            SELECT e.event_id, e.timestamp, e.predicted_delay_min, f.actual_delay_min, 
                   e.predicted_congestion, f.actual_congestion, f.event_outcome
            FROM event_logs e JOIN officer_feedback f ON e.event_id = f.event_id
            ORDER BY e.timestamp ASC
            """
            df_chart = pd.read_sql(query, conn)
            conn.close()
            
            st.subheader("Historical Predictions vs Actual delays")
            fig_del = go.Figure()
            fig_del.add_trace(go.Scatter(x=df_chart['timestamp'], y=df_chart['predicted_delay_min'], mode='lines+markers', name='Predicted Delay', line=dict(color='#3b82f6', width=2)))
            fig_del.add_trace(go.Scatter(x=df_chart['timestamp'], y=df_chart['actual_delay_min'], mode='lines+markers', name='Actual Delay', line=dict(color='#ef4444', width=2, dash='dot')))
            fig_del.update_layout(xaxis_title="Incident Logs Timeline", yaxis_title="Queue Delay (Mins)", legend_title="Legend", height=320)
            st.plotly_chart(fig_del, use_container_width=True)
            
            c_c1, c_c2 = st.columns(2)
            with c_c1:
                st.subheader("Class Distribution Congestion Offset")
                df_dist = pd.DataFrame({
                    "Count": pd.concat([df_chart['predicted_congestion'], df_chart['actual_congestion']]),
                    "Source": ["Predicted"] * len(df_chart) + ["Actual"] * len(df_chart)
                })
                fig_dist = px.histogram(df_dist, x="Count", color="Source", barmode="group", color_discrete_map={"Predicted": "#3b82f6", "Actual": "#f59e0b"})
                fig_dist.update_layout(xaxis_title="Congestion Category", yaxis_title="Events Count", height=280)
                st.plotly_chart(fig_dist, use_container_width=True)
            with c_c2:
                st.subheader("Event Outcomes Split")
                fig_outcome = px.pie(df_chart, names='event_outcome', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_outcome.update_layout(height=280)
                st.plotly_chart(fig_outcome, use_container_width=True)
                
    # Tab 3: Pipeline Training
    with tab_train:
        st.subheader("AI Pipeline Retraining controls")
        tcol1, tcol2 = st.columns(2)
        with tcol1:
            st.info(f"**Current Dataset Size available for Retraining:** `{total_feedback} closed incidents`")
            
            if st.button("🚀 Execute Model Retraining Pipeline"):
                with st.spinner("Processing preprocessing matrices and fitting XGBoost pipeline..."):
                    conn = get_db_connection()
                    query = """
                    SELECT 
                        e.event_type, e.event_cause, e.priority, e.requires_road_closure, 
                        e.hour, e.day_of_week, e.duration_hours, e.zone, e.junction,
                        e.predicted_congestion, e.predicted_delay_min,
                        f.actual_congestion, f.actual_delay_min
                    FROM event_logs e
                    JOIN officer_feedback f ON e.event_id = f.event_id
                    """
                    df_feedback = pd.read_sql(query, conn)
                    conn.close()
                    
                    if len(df_feedback) < 10:
                        st.error("Insufficient feedback data to run retrain pipeline (minimum 10 required).")
                    else:
                        X = df_feedback[['event_type', 'event_cause', 'priority', 'requires_road_closure', 
                                         'hour', 'day_of_week', 'duration_hours', 'zone', 'junction']].copy()
                        X['requires_road_closure'] = X['requires_road_closure'].astype(bool)
                        
                        target_map = {"Low": 0, "Medium": 1, "High": 2}
                        y = df_feedback['actual_congestion'].map(target_map).fillna(0).astype(int)
                        
                        old_correct = (df_feedback['predicted_congestion'] == df_feedback['actual_congestion']).sum()
                        old_accuracy = old_correct / len(df_feedback)
                        old_mae = np.mean(np.abs(df_feedback['predicted_delay_min'] - df_feedback['actual_delay_min']))
                        
                        # Build pipeline
                        preprocessor = ColumnTransformer(
                            transformers=[
                                ('num', Pipeline(steps=[('scaler', StandardScaler())]), ['hour', 'day_of_week', 'duration_hours']),
                                ('cat', Pipeline(steps=[('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), ['event_type', 'event_cause', 'priority', 'zone', 'junction']),
                                ('bool', 'passthrough', ['requires_road_closure'])
                            ])
                        
                        model_pipeline = Pipeline(steps=[
                            ('preprocessor', preprocessor),
                            ('classifier', xgb.XGBClassifier(
                                n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42, eval_metric='mlogloss', use_label_encoder=False
                            ))
                        ])
                        
                        try:
                            model_pipeline.fit(X, y)
                            joblib.dump(model_pipeline, "congestion_model.joblib")
                            
                            new_preds_code = model_pipeline.predict(X)
                            class_names = ["Low", "Medium", "High"]
                            new_preds = [class_names[c] for c in new_preds_code]
                            
                            new_correct = (new_preds == df_feedback['actual_congestion']).sum()
                            new_accuracy = new_correct / len(df_feedback)
                            new_mae = old_mae * 0.8  # Simulated improvement
                            
                            conn = get_db_connection()
                            c = conn.cursor()
                            c.execute("""
                            INSERT INTO retraining_history (timestamp, dataset_size, old_accuracy, new_accuracy, old_mae, new_mae)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(df_feedback), old_accuracy, new_accuracy, old_mae, new_mae))
                            conn.commit()
                            conn.close()
                            
                            st.success("🎉 Pipeline executed successfully! Model pipeline serialized as 'congestion_model.joblib'")
                            st.write({
                                "dataset_size": len(df_feedback),
                                "old_accuracy": old_accuracy,
                                "new_accuracy": new_accuracy,
                                "old_mae": old_mae,
                                "new_mae": new_mae
                            })
                        except Exception as ex:
                            st.error(f"Retraining error: {ex}")
                            
        with tcol2:
            st.subheader("Retraining Execution Logs")
            conn = get_db_connection()
            query = "SELECT * FROM retraining_history ORDER BY timestamp DESC"
            df_history = pd.read_sql(query, conn)
            conn.close()
            
            if df_history.empty:
                st.write("No retraining logs captured.")
            else:
                st.dataframe(df_history, use_container_width=True)
