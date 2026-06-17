import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from route_graph import BengaluruRouteGraph
from emergency_route import EmergencyCorridorEngine

def render_emergency_corridor_page():
    """
    Renders the Streamlit frontend interface for the Emergency Corridor Recommendation page.
    """
    st.markdown("""
    <div class="main-header">
        <h1>🚑 EMERGENCY CORRIDOR ROUTE RECOMENDER</h1>
        <p>Shortest Path Graph Traversal under Congestion, A* Haversine Heuristics, and Folium Plottings</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize Graph and Engine
    if 'route_graph' not in st.session_state:
        st.session_state['route_graph'] = BengaluruRouteGraph()
    graph = st.session_state['route_graph']
    
    if 'routing_engine' not in st.session_state:
        st.session_state['routing_engine'] = EmergencyCorridorEngine(graph)
    engine = st.session_state['routing_engine']

    # Two column layout
    col_inputs, col_map = st.columns([5, 7])

    # Get nodes and edges data
    junctions = graph.get_junction_names()
    edges = graph.get_all_edges()
    
    # Map edge tuples to printable string labels
    edge_labels = {edge: f"{edge[0]} ➔ {edge[1]}" for edge in edges}
    reverse_edge_labels = {v: k for k, v in edge_labels.items()}

    with col_inputs:
        st.markdown('<div class="section-header">Route Query Configuration</div>', unsafe_allow_html=True)
        
        col_s, col_d = st.columns(2)
        with col_s:
            source = st.selectbox(
                "Source Junction (Start)",
                options=junctions,
                index=0
            )
        with col_d:
            # Set target default to IbblurJunction
            tgt_idx = junctions.index('IbblurJunction') if 'IbblurJunction' in junctions else 0
            destination = st.selectbox(
                "Destination Junction (End)",
                options=junctions,
                index=tgt_idx
            )
            
        if source == destination:
            st.warning("⚠️ Source and Destination must be distinct junctions.")

        # Blocked roads selection
        blocked_str_list = st.multiselect(
            "Congested / Blocked Corridor Links",
            options=list(edge_labels.values()),
            default=[edge_labels[('HSRLayout14thMain', 'AgaraJunction')]] if ('HSRLayout14thMain', 'AgaraJunction') in edges else []
        )
        
        blocked_roads = [reverse_edge_labels[label] for label in blocked_str_list]
        
        # Congestion multiplier
        congestion_multiplier = st.slider(
            "Congestion Penalty Multiplier",
            min_value=2.0,
            max_value=25.0,
            value=10.0,
            step=1.0,
            help="Simulates travel delay penalty by scaling edge travel time on congested links."
        )
        
        # Routing Algorithm selection
        algorithm = st.radio(
            "Pathfinding Algorithm",
            ["A* Search (with Haversine Heuristic)", "Dijkstra's Shortest Path"],
            index=0
        )
        algo_code = "astar" if "A*" in algorithm else "dijkstra"

    with col_map:
        st.markdown('<div class="section-header">Corridor Optimization Engine</div>', unsafe_allow_html=True)
        
        if source != destination:
            # Run Routing Engine
            result = engine.find_emergency_corridor(
                source, 
                destination, 
                blocked_roads, 
                congestion_multiplier, 
                algo_code
            )
            
            if "error" in result:
                st.error(result["error"])
            else:
                normal_time_cong = result["normal_time_congested"]
                emerg_time_cong = result["emergency_time_congested"]
                saved_time = result["time_saved_minutes"]
                
                # Metric Cards
                mcol1, mcol2, mcol3 = st.columns(3)
                with mcol1:
                    st.markdown(f"""
                    <div class="metric-box border-high">
                        <div class="metric-box-title">Normal Route Time</div>
                        <div class="metric-box-value">{normal_time_cong:.1f}m</div>
                        <div class="metric-box-desc">Free-flow base: {result['normal_time_free_flow']:.1f}m</div>
                    </div>
                    """, unsafe_allow_html=True)
                with mcol2:
                    st.markdown(f"""
                    <div class="metric-box border-low">
                        <div class="metric-box-title">Emergency Route Time</div>
                        <div class="metric-box-value" style="color: green;">{emerg_time_cong:.1f}m</div>
                        <div class="metric-box-desc">Optimized Corridor</div>
                    </div>
                    """, unsafe_allow_html=True)
                with mcol3:
                    st.markdown(f"""
                    <div class="metric-box border-info">
                        <div class="metric-box-title">Travel Time Saved</div>
                        <div class="metric-box-value" style="color: #3b82f6;">{saved_time:.1f}m</div>
                        <div class="metric-box-desc">Saving: {(saved_time/max(0.1, normal_time_cong))*100:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Node list sequences
                st.info(f"**Emergency Dispatch Route:** {' ➔ '.join(result['emergency_route'])}")
                
                # Plot Routing Map
                plot_routing_map(graph, result, blocked_roads)
        else:
            st.info("Please select distinct Source and Destination nodes.")

def plot_routing_map(graph, result, blocked_roads):
    """Plots the visual route comparison on a Folium Map."""
    G = graph.get_graph()
    
    # Calculate map center
    lats = [G.nodes[node]['lat'] for node in G.nodes()]
    lons = [G.nodes[node]['lon'] for node in G.nodes()]
    center_lat = np.mean(lats)
    center_lng = np.mean(lons)
    
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13, tiles="cartodbpositron")
    
    # Draw all base edges in thin gray
    for u, v, data in G.edges(data=True):
        u_coords = (G.nodes[u]['lat'], G.nodes[u]['lon'])
        v_coords = (G.nodes[v]['lat'], G.nodes[v]['lon'])
        folium.PolyLine(
            locations=[u_coords, v_coords],
            color="#cbd5e1",
            weight=2,
            opacity=0.6
        ).add_to(m)
        
    # Draw blocked roads in thick red
    for u, v in blocked_roads:
        if G.has_edge(u, v):
            u_coords = (G.nodes[u]['lat'], G.nodes[u]['lon'])
            v_coords = (G.nodes[v]['lat'], G.nodes[v]['lon'])
            folium.PolyLine(
                locations=[u_coords, v_coords],
                color="#ef4444",
                weight=6,
                opacity=0.9,
                tooltip=f"CONGESTED LINK: {u} -> {v}"
            ).add_to(m)
            
    # Draw Normal Route in dashed orange
    normal_route = result["normal_route"]
    normal_coords = [(G.nodes[node]['lat'], G.nodes[node]['lon']) for node in normal_route]
    folium.PolyLine(
        locations=normal_coords,
        color="#f97316",
        weight=4,
        opacity=0.7,
        dash_array="5, 8",
        tooltip="Normal Route (Gridlock Delayed)"
    ).add_to(m)
    
    # Draw Emergency Route in solid green
    emergency_route = result["emergency_route"]
    emergency_coords = [(G.nodes[node]['lat'], G.nodes[node]['lon']) for node in emergency_route]
    folium.PolyLine(
        locations=emergency_coords,
        color="#22c55e",
        weight=5,
        opacity=0.9,
        tooltip="Emergency Clearing Corridor (Active)"
    ).add_to(m)
    
    # Plot all junctions as circles
    for node in G.nodes():
        coords = (G.nodes[node]['lat'], G.nodes[node]['lon'])
        
        # Color start and end nodes specifically
        if node == normal_route[0]:
            marker_color = "darkgreen"
            popup_label = f"START: {node}"
            radius = 7
        elif node == normal_route[-1]:
            marker_color = "red"
            popup_label = f"END: {node}"
            radius = 7
        else:
            marker_color = "blue"
            popup_label = f"Junction: {node}"
            radius = 4
            
        folium.CircleMarker(
            location=coords,
            radius=radius,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.8,
            popup=popup_label
        ).add_to(m)
        
    st_folium(m, width="100%", height=360)
