import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import joblib
import os
import datetime

# Page configuration
st.set_page_config(
    page_title="Bengaluru Gridlock: Event-Driven Congestion Control",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high-fidelity luxury enterprise look
st.markdown("""
<style>
    /* Custom background & typography */
    .main {
        background-color: #fcfbf9;
    }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 30px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    }
    .main-header h1 {
        color: #f1f5f9 !important;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.05em;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-top: 10px;
        margin-bottom: 0;
    }
    /* Metric Card Styling */
    .metric-box {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        border-left: 6px solid #e2e8f0;
    }
    .metric-box-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .metric-box-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-box-desc {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 5px;
    }
    /* Custom colored borders based on risk levels */
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
    /* Section Headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 15px;
        margin-top: 10px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. LOAD MODEL & HISTORICAL DATA
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
        return pd.read_csv(file_path)
    return pd.DataFrame()

model = load_model()
df_hist = load_historical_data()

# Clean up locations for plotting (focusing on Bengaluru center area)
if not df_hist.empty:
    df_hist_clean = df_hist[
        (df_hist['latitude'] >= 12.8) & (df_hist['latitude'] <= 13.2) &
        (df_hist['longitude'] >= 77.4) & (df_hist['longitude'] <= 77.8)
    ].copy()
else:
    df_hist_clean = pd.DataFrame()

# -------------------------------------------------------------
# 2. MAP CLICK BINDING STATE
# -------------------------------------------------------------
# Initialize session state for map clicks
if 'sim_lat' not in st.session_state:
    st.session_state['sim_lat'] = 12.9716
if 'sim_lng' not in st.session_state:
    st.session_state['sim_lng'] = 77.5946

# -------------------------------------------------------------
# 3. SIDEBAR: EVENT SIMULATION
# -------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/000000/traffic-jam.png", width=60)
st.sidebar.title("Event Simulator")
st.sidebar.markdown("Configure the parameters of the traffic event below.")

# Event type & cause
event_type = st.sidebar.selectbox(
    "Event Type",
    options=["unplanned", "planned"],
    index=0
)

cause_options = [
    "vehicle_breakdown", "others", "pot_holes", "construction", 
    "water_logging", "accident", "tree_fall", "road_conditions", 
    "congestion", "public_event", "procession", "protest"
]
event_cause = st.sidebar.selectbox(
    "Event Cause",
    options=cause_options,
    index=0
)

# Priority & Road Closure
priority = st.sidebar.selectbox(
    "Priority",
    options=["High", "Low"],
    index=0
)

requires_road_closure = st.sidebar.checkbox(
    "Requires Road Closure",
    value=False
)

# Temporal sliders
hour = st.sidebar.slider(
    "Hour of Day",
    min_value=0, max_value=23, value=9, step=1
)

day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_name = st.sidebar.select_slider(
    "Day of Week",
    options=day_labels,
    value="Monday"
)
day_of_week = day_labels.index(day_name)

duration_hours = st.sidebar.slider(
    "Event Duration (Hours)",
    min_value=0.1, max_value=24.0, value=1.5, step=0.1
)

# Spatial Dropdowns
zone_options = [
    'Central Zone 2', 'West Zone 1', 'North Zone 2', 'West Zone 2', 
    'South Zone 2', 'North Zone 1', 'Central Zone 1', 'East Zone 1', 
    'South Zone 1', 'Unknown'
]
zone = st.sidebar.selectbox(
    "Zone",
    options=zone_options,
    index=0
)

junction_options = [
    'SilkBoardJunc', 'HebbalFlyoverJunc', 'Peenya14thCrossJunc', 'UrvashiJunction', 
    'LalbaghMainGateJunc', 'RingRoad-UllalJunction', 'IbblurJunction', 'Sumanhalli', 'Unknown'
]
junction = st.sidebar.selectbox(
    "Junction",
    options=junction_options,
    index=0
)

# Coordinate simulation
st.sidebar.subheader("Coordinates")
st.sidebar.markdown("*Tip: Click on the interactive map to automatically capture new coordinates!*")

sim_lat = st.sidebar.number_input(
    "Latitude",
    value=st.session_state['sim_lat'],
    format="%.6f",
    step=0.001
)
sim_lng = st.sidebar.number_input(
    "Longitude",
    value=st.session_state['sim_lng'],
    format="%.6f",
    step=0.001
)

# Synchronize inputs back to session state
st.session_state['sim_lat'] = sim_lat
st.session_state['sim_lng'] = sim_lng

# -------------------------------------------------------------
# 4. PREDICTION RUNTIME
# -------------------------------------------------------------
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

# Execute prediction using preloaded model
prediction_class = "Medium"
pred_prob_low = 0.15
pred_prob_med = 0.70
pred_prob_high = 0.15

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
        st.sidebar.error(f"Prediction Error: {e}")

# -------------------------------------------------------------
# 5. DYNAMIC RESOURCE & LOGISTICS COMPUTATION
# -------------------------------------------------------------
# Calculate expected delay
if prediction_class == "High":
    expected_delay_min = max(30, int(duration_hours * 60 * 1.5))
    expected_delay_min = min(240, expected_delay_min)
    risk_style = "border-high"
    risk_color = "red"
elif prediction_class == "Medium":
    expected_delay_min = max(15, int(duration_hours * 60 * 0.75))
    expected_delay_min = min(120, expected_delay_min)
    risk_style = "border-medium"
    risk_color = "orange"
else:
    expected_delay_min = max(5, int(duration_hours * 60 * 0.25))
    expected_delay_min = min(45, expected_delay_min)
    risk_style = "border-low"
    risk_color = "green"

# Calculate police personnel required
police_base = {"Low": 2, "Medium": 4, "High": 8}
police_req = police_base[prediction_class]
if priority == "High":
    police_req += 2
if requires_road_closure:
    police_req += 4

# Calculate barricades required
barricade_base = {"Low": 1, "Medium": 5, "High": 12}
barricades_req = barricade_base[prediction_class]
if requires_road_closure:
    barricades_req += 8

# Generate diversion route description
diversion_routes = {
    'SilkBoardJunc': "Divert heavy vehicles to HSR Layout 27th Main or BTM Layout 16th Main. Utilize the Silk Board flyover underpass for light vehicles to bypass the intersection bottleneck.",
    'HebbalFlyoverJunc': "Divert inbound airport traffic via Hennur-Bagalur road or Thanisandra main road. Keep the central flyover lanes clear for emergency and public transit only.",
    'Peenya14thCrossJunc': "Divert heavy industrial cargo trucks to NICE Road. Re-route city passenger buses through Peenya 1st Stage collector streets to reduce peak hour local blockages.",
    'UrvashiJunction': "Re-route traffic through Lalbagh Road and JC Road. Strictly restrict roadside parking on parallel lanes to ensure two active lanes remain functional.",
    'LalbaghMainGateJunc': "Divert south-bound traffic via Double Road or KH Road. Re-route towards Richmond Circle to bypass the Lalbagh gate roadworks.",
    'RingRoad-UllalJunction': "Divert Outer Ring Road transit traffic to Sarjapur Road or Haralur Road. Leverage secondary link arterial streets to distribute volume.",
    'Sumanhalli': "Divert heavy multi-axle freight traffic via Magadi Road or Outer Ring Road. Re-route light commuter traffic via local housing board lanes.",
    'Unknown': f"Implement local loop diversions within 500 meters of the incident scene in the {zone}. Coordinate signal timers on adjacent corridors to clear spillover queues."
}
diversion_text = diversion_routes.get(junction, diversion_routes['Unknown'])

# -------------------------------------------------------------
# 6. DASHBOARD BODY LAYOUT
# -------------------------------------------------------------
# Title Banner
st.markdown("""
<div class="main-header">
    <h1>BENGALURU ROAD CONGESTION CONTROL CENTER</h1>
    <p>Predictive Event-Driven Gridlock Management | Flipkart Gridlock Hackathon Project</p>
</div>
""", unsafe_allow_html=True)

# Grid Layout: Row 1 - KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    prob_val = {"Low": pred_prob_low, "Medium": pred_prob_med, "High": pred_prob_high}[prediction_class]
    st.markdown(f"""
    <div class="metric-box {risk_style}">
        <div class="metric-box-title">Congestion Risk Level</div>
        <div class="metric-box-value" style="color:{risk_color};">{prediction_class}</div>
        <div class="metric-box-desc">Model Confidence: {prob_val:.1%}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-box border-info">
        <div class="metric-box-title">Expected Queue Delay</div>
        <div class="metric-box-value">{expected_delay_min} mins</div>
        <div class="metric-box-desc">Duration impact: {duration_hours} hrs</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-box border-info">
        <div class="metric-box-title">Required Police Officers</div>
        <div class="metric-box-value">{police_req} personnel</div>
        <div class="metric-box-desc">Priority multiplier: {priority}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-box border-info">
        <div class="metric-box-title">Barricades Needed</div>
        <div class="metric-box-value">{barricades_req} units</div>
        <div class="metric-box-desc">Road closure status: {requires_road_closure}</div>
    </div>
    """, unsafe_allow_html=True)

# Grid Layout: Row 2 - Map & Logistics Info
col_left, col_right = st.columns([7, 5])

with col_left:
    st.markdown('<div class="section-header">Interactive Spatial Map & Live Coordinates</div>', unsafe_allow_html=True)
    st.markdown("*Click anywhere on the map to place the simulated incident marker instantly.*")
    
    # 1. Initialize Folium Map centered on current simulated location
    m = folium.Map(
        location=[st.session_state['sim_lat'], st.session_state['sim_lng']], 
        zoom_start=13,
        tiles="cartodbpositron"
    )
    
    # 2. Add historical points for spatial context (sampled to avoid map lag)
    if not df_hist_clean.empty:
        hist_sample = df_hist_clean.sample(min(250, len(df_hist_clean)), random_state=42)
        color_map = {'Low': '#10b981', 'Medium': '#f59e0b', 'High': '#ef4444'}
        for _, row in hist_sample.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=4,
                color=color_map.get(row['congestion_proxy_label'], '#3b82f6'),
                fill=True,
                fill_color=color_map.get(row['congestion_proxy_label'], '#3b82f6'),
                fill_opacity=0.4,
                weight=1,
                popup=f"Cause: {row['event_cause']}<br>Congestion: {row['congestion_proxy_label']}"
            ).add_to(m)
            
    # 3. Add simulated marker
    folium.Marker(
        location=[st.session_state['sim_lat'], st.session_state['sim_lng']],
        popup="Simulated Incident Location",
        tooltip="Simulated Location",
        icon=folium.Icon(color=risk_color, icon="info-sign")
    ).add_to(m)
    
    # 4. Render map
    map_data = st_folium(m, width="100%", height=450)
    
    # 5. Capture map click and re-render
    if map_data and map_data.get("last_clicked"):
        click_lat = map_data["last_clicked"]["lat"]
        click_lng = map_data["last_clicked"]["lng"]
        
        # If coordinates changed, update state and trigger rerun
        if click_lat != st.session_state['sim_lat'] or click_lng != st.session_state['sim_lng']:
            st.session_state['sim_lat'] = click_lat
            st.session_state['sim_lng'] = click_lng
            st.rerun()

with col_right:
    st.markdown('<div class="section-header">Operational Routing & Diversion Details</div>', unsafe_allow_html=True)
    
    st.info(f"**Target Corridor Zone:** {zone} \n\n**Nearest Key Junction:** {junction}")
    
    st.warning(f"**Suggested Diversion Route:**\n\n{diversion_text}")
    
    st.markdown('<div class="section-header">Congestion Probability Spectrum</div>', unsafe_allow_html=True)
    
    st.markdown(f"**Low Risk Probability** ({pred_prob_low:.1%})")
    st.progress(float(pred_prob_low))
    
    st.markdown(f"**Medium Risk Probability** ({pred_prob_med:.1%})")
    st.progress(float(pred_prob_med))
    
    st.markdown(f"**High Risk Probability** ({pred_prob_high:.1%})")
    st.progress(float(pred_prob_high))

# -------------------------------------------------------------
# 7. CLOSED-LOOP FEEDBACK PANEL
# -------------------------------------------------------------
st.markdown('<div class="section-header">Closed-Loop Delay Feedback Portal</div>', unsafe_allow_html=True)
st.markdown("Help us refine our predictive delays by submitting real-world queue times on the ground.")

# Feedback Form
with st.form("feedback_form", clear_on_submit=True):
    f_col1, f_col2, f_col3 = st.columns([4, 4, 4])
    
    with f_col1:
        pred_delay_display = st.number_input(
            "System Predicted Delay (Minutes)",
            value=expected_delay_min,
            disabled=True
        )
    with f_col2:
        actual_delay = st.number_input(
            "Actual Experienced Delay (Minutes)",
            min_value=0,
            value=expected_delay_min,
            step=1
        )
    with f_col3:
        user_comments = st.text_input(
            "Driver/Officer Comments",
            placeholder="E.g., Breakdown cleared, but backup remained heavy."
        )
        
    submit_btn = st.form_submit_button("Submit Traffic Feedback")
    
    if submit_btn:
        feedback_file = "user_feedback.csv"
        
        # Create feedback record
        feedback_record = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'event_type': event_type,
            'event_cause': event_cause,
            'requires_road_closure': requires_road_closure,
            'junction': junction,
            'predicted_delay_min': expected_delay_min,
            'actual_delay_min': actual_delay,
            'comments': user_comments
        }
        
        new_feedback_df = pd.DataFrame([feedback_record])
        
        # Append to CSV
        if os.path.exists(feedback_file):
            new_feedback_df.to_csv(feedback_file, mode='a', header=False, index=False)
        else:
            new_feedback_df.to_csv(feedback_file, mode='w', header=True, index=False)
            
        st.success("🎉 Feedback submitted successfully! The routing engine logs have been updated for batch calibration.")
