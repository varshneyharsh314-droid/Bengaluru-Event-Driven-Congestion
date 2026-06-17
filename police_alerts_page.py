import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import time
from nearest_station import PoliceStationFinder
from alert_engine import IncidentAlertEngine

def render_police_alerts_page():
    """
    Renders the Streamlit frontend interface for the Nearest Police Station Alert System.
    """
    st.markdown("""
    <div class="main-header">
        <h1>🚨 NEAREST POLICE STATION ALERT CENTER</h1>
        <p>GPS-Based Dispatching, Haversine Proximity Calculations, and Simulated SMS Alerts</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize Backend Finder
    if 'station_finder' not in st.session_state:
        st.session_state['station_finder'] = PoliceStationFinder()
    finder = st.session_state['station_finder']

    # Two column layout
    col_config, col_alert = st.columns([5, 7])

    with col_config:
        st.markdown('<div class="section-header">Incident Coordinates & Detail</div>', unsafe_allow_html=True)
        
        # Link coordinates from Simulator Session State if available
        default_lat = st.session_state.get('sim_lat', 12.9176)
        default_lng = st.session_state.get('sim_lng', 77.6246)
        
        st.write("📍 *Pulling coordinates from incident scene coordinator (editable)*")
        event_lat = st.number_input("Event Latitude", value=default_lat, format="%.6f", step=0.001)
        event_lng = st.number_input("Event Longitude", value=default_lng, format="%.6f", step=0.001)
        
        # Sync back to session state to maintain sync across tabs
        st.session_state['sim_lat'] = event_lat
        st.session_state['sim_lng'] = event_lng

        # Incident attributes
        event_type = st.selectbox("Event Type", options=["unplanned", "planned"], index=0)
        priority = st.selectbox("Incident Priority Level", options=["High", "Low"], index=0)
        congestion = st.selectbox("Congestion Severity Level", options=["Low", "Medium", "High", "Extreme"], index=2)
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            expected_delay = st.number_input("Expected Queue Delay (Mins)", min_value=1, value=45)
        with col_res2:
            police_needed = st.number_input("Police Officers Needed", min_value=1, value=8)
            
        barricades = st.number_input("Barricades Cordon Needed", min_value=0, value=12)
        location_name = st.text_input("Location Landmark Descriptor", value="Silk Board Junction Loop")

    with col_alert:
        st.markdown('<div class="section-header">Nearest Responder Dispatch Panel</div>', unsafe_allow_html=True)
        
        # Run nearest police station search
        nearest_station = finder.find_nearest_station(event_lat, event_lng)
        
        # Determine station availability status
        avail_officers = nearest_station['available_officers']
        if avail_officers >= police_needed:
            status_text = "🟢 Sufficient Force Available"
            status_color = "green"
        elif avail_officers > 0:
            status_text = "🟡 Reinforcements Required"
            status_color = "orange"
        else:
            status_text = "🔴 Station Depleted (Out of Service)"
            status_color = "red"

        # KPI dashboard for nearest station
        st.subheader("Nearest Station Proximity Log")
        
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="metric-box border-info">
                <div class="metric-box-title">Nearest Station</div>
                <div class="metric-box-value" style="font-size: 1.15rem; line-height: 1.2;">{nearest_station['station_name']}</div>
                <div class="metric-box-desc">Phone: {nearest_station['phone']}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-box border-info">
                <div class="metric-box-title">Proximity Distance</div>
                <div class="metric-box-value">{nearest_station['distance_km']:.2f} km</div>
                <div class="metric-box-desc">Haversine Great-Circle</div>
            </div>
            """, unsafe_allow_html=True)

        m3, m4 = st.columns(2)
        with m3:
            st.markdown(f"""
            <div class="metric-box border-info">
                <div class="metric-box-title">Dispatch Status</div>
                <div class="metric-box-value" style="color: {status_color}; font-size: 1.1rem; font-weight: bold;">{status_text}</div>
                <div class="metric-box-desc">Available Officers: {avail_officers}</div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown(f"""
            <div class="metric-box border-info">
                <div class="metric-box-title">Estimated Response ETA</div>
                <div class="metric-box-value">{nearest_station['eta_minutes']} mins</div>
                <div class="metric-box-desc">At average speed of 25 km/h</div>
            </div>
            """, unsafe_allow_html=True)

        # Plot responder map
        st.markdown('<div class="section-header">Responder Dispatch Map</div>', unsafe_allow_html=True)
        
        dispatch_map = folium.Map(location=[event_lat, event_lng], zoom_start=13, tiles="cartodbpositron")
        
        # Plot incident
        folium.Marker(
            location=[event_lat, event_lng],
            popup="Incident Scene",
            icon=folium.Icon(color="red", icon="warning-sign")
        ).add_to(dispatch_map)
        
        # Plot nearest station
        folium.Marker(
            location=[nearest_station['latitude'], nearest_station['longitude']],
            popup=f"{nearest_station['station_name']}\n(Phone: {nearest_station['phone']})",
            icon=folium.Icon(color="blue", icon="home")
        ).add_to(dispatch_map)
        
        # Draw line between incident and station
        folium.PolyLine(
            locations=[[event_lat, event_lng], [nearest_station['latitude'], nearest_station['longitude']]],
            color="darkblue",
            weight=3,
            dash_array="5, 10"
        ).add_to(dispatch_map)
        
        st_folium(dispatch_map, width="100%", height=280)

        # SMS Dispatch Action
        st.markdown('<div class="section-header">SMS Dispatch Console</div>', unsafe_allow_html=True)
        
        alert_msg = IncidentAlertEngine.generate_alert_message(
            event_type, priority, congestion, expected_delay, police_needed, barricades, location_name, event_lat, event_lng
        )
        
        st.text_area("Generated SMS Alert Message", value=alert_msg, height=180, disabled=True)
        
        if st.button("🚀 TRIGGER SMS ALERT DISPATCH"):
            with st.spinner("Connecting to SMS Gateway..."):
                sms_log = IncidentAlertEngine.simulate_sms_dispatch(nearest_station['phone'], alert_msg)
                
            st.success(f"✅ Alert dispatched successfully to {nearest_station['station_name']}!")
            
            # Show simulated phone console receipt
            st.markdown("""
            <div style="background-color: #0f172a; padding: 20px; border-radius: 12px; border: 4px solid #475569; font-family: 'Courier New', Courier, monospace; color: #38bdf8;">
                <div style="border-bottom: 2px solid #475569; padding-bottom: 8px; margin-bottom: 12px; font-weight: bold; text-align: center; color: #94a3b8;">
                    📱 SMS GATEWAY LOG RECEIPT
                </div>
                <b>[Gateway Message ID]:</b> %s <br>
                <b>[Timestamp]:</b> %s <br>
                <b>[Recipient Phone]:</b> %s <br>
                <b>[Transmission Status]:</b> <span style="color: #4ade80;">%s</span> <br>
                <b>[Payload Length]:</b> %d characters <br>
                <hr style="border-color: #475569;">
                <div style="background-color: #1e293b; padding: 12px; border-radius: 6px; color: #f8fafc; font-size: 0.9rem; white-space: pre-wrap;">%s</div>
            </div>
            """ % (
                sms_log['gateway_message_id'], 
                sms_log['timestamp'], 
                sms_log['recipient_phone'], 
                sms_log['status'], 
                sms_log['characters_sent'], 
                sms_log['payload']
            ), unsafe_allow_html=True)

if __name__ == "__main__":
    # Test render shell
    pass
