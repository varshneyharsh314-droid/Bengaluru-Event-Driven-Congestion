import networkx as nx
import numpy as np
import json
from typing import List, Tuple, Dict, Any

class RouteService:
    def __init__(self):
        self.G = nx.DiGraph()
        self.junction_coords = {
            'SilkBoardJunc': (12.9176, 77.6246),
            'HSRLayout14thMain': (12.9172, 77.6366),
            'AgaraJunction': (12.9261, 77.6508),
            'IbblurJunction': (12.9234, 77.6712),
            'BellandurJunction': (12.9366, 77.6830),
            'MadiwalaCheckpost': (12.9225, 77.6189),
            'KoramangalaWaterTank': (12.9348, 77.6210),
            'BTMLayout16thMain': (12.9142, 77.6080),
            'HSRLayout27thMain': (12.9110, 77.6475),
        }
        self.build_graph()

    def build_graph(self):
        # Add nodes with coordinates
        for junc, coords in self.junction_coords.items():
            self.G.add_node(junc, lat=coords[0], lon=coords[1])
            
        # Add edges (u, v, weight [minutes], length [km])
        roads = [
            ('SilkBoardJunc', 'HSRLayout14thMain', 4.0, 1.5),
            ('HSRLayout14thMain', 'SilkBoardJunc', 4.0, 1.5),
            ('HSRLayout14thMain', 'AgaraJunction', 3.5, 1.3),
            ('AgaraJunction', 'HSRLayout14thMain', 3.5, 1.3),
            ('AgaraJunction', 'IbblurJunction', 5.0, 2.1),
            ('IbblurJunction', 'AgaraJunction', 5.0, 2.1),
            ('SilkBoardJunc', 'MadiwalaCheckpost', 3.0, 1.1),
            ('MadiwalaCheckpost', 'SilkBoardJunc', 3.0, 1.1),
            ('MadiwalaCheckpost', 'KoramangalaWaterTank', 4.5, 1.8),
            ('KoramangalaWaterTank', 'MadiwalaCheckpost', 4.5, 1.8),
            ('KoramangalaWaterTank', 'AgaraJunction', 6.0, 2.4),
            ('AgaraJunction', 'KoramangalaWaterTank', 6.0, 2.4),
            ('SilkBoardJunc', 'BTMLayout16thMain', 3.5, 1.4),
            ('BTMLayout16thMain', 'SilkBoardJunc', 3.5, 1.4),
            ('BTMLayout16thMain', 'KoramangalaWaterTank', 5.5, 2.0),
            ('KoramangalaWaterTank', 'BTMLayout16thMain', 5.5, 2.0),
            ('IbblurJunction', 'BellandurJunction', 4.0, 1.6),
            ('BellandurJunction', 'IbblurJunction', 4.0, 1.6),
            ('AgaraJunction', 'HSRLayout27thMain', 3.0, 1.2),
            ('HSRLayout27thMain', 'AgaraJunction', 3.0, 1.2),
            ('HSRLayout27thMain', 'IbblurJunction', 3.0, 1.1),
            ('IbblurJunction', 'HSRLayout27thMain', 3.0, 1.1),
        ]
        
        for u, v, weight, length in roads:
            self.G.add_edge(u, v, weight=weight, length=length, base_weight=weight)

    @staticmethod
    def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0  # Earth radius in km
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c

    def astar_heuristic(self, u: str, v: str) -> float:
        lat1, lon1 = self.G.nodes[u]['lat'], self.G.nodes[u]['lon']
        lat2, lon2 = self.G.nodes[v]['lat'], self.G.nodes[v]['lon']
        dist_km = self.calculate_haversine(lat1, lon1, lat2, lon2)
        # Time = (distance / speed) * 60 minutes, assuming 50 km/h speed
        return (dist_km / 50.0) * 60.0

    def get_path_weight(self, graph: nx.DiGraph, path: List[str]) -> float:
        total_weight = 0
        for i in range(len(path) - 1):
            total_weight += graph[path[i]][path[i+1]]['weight']
        return total_weight

    def get_junctions(self) -> List[Dict[str, Any]]:
        return [{"name": name, "lat": coords[0], "lon": coords[1]} for name, coords in self.junction_coords.items()]

    def get_edges(self) -> List[Dict[str, Any]]:
        edges = []
        for u, v, data in self.G.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "weight": data["weight"],
                "length": data["length"],
                "base_weight": data["base_weight"]
            })
        return edges

    def find_emergency_corridor(
        self, 
        source: str, 
        target: str, 
        blocked_roads: List[Tuple[str, str]] = None, 
        congestion_multiplier: float = 10.0, 
        algorithm: str = "astar",
        incident_lat: float = None,
        incident_lon: float = None,
        predicted_impact_radius_meters: float = None
    ) -> Dict[str, Any]:
        """
        Calculates optimal emergency corridor by routing around high congested nodes.
        Supports coordinates and radial weight inflation.
        """
        if source not in self.G or target not in self.G:
            return {"error": f"Junction {source} or {target} not recognized in Bengaluru graph."}

        if blocked_roads is None:
            blocked_roads = []

        congested_G = self.G.copy()
        resolved_blocked_roads = list(blocked_roads)
        nearest_node = None

        # Determine blocked roads dynamically using coordinates and impact radius
        if (incident_lat is not None and 
            incident_lon is not None and 
            predicted_impact_radius_meters is not None):
            
            radius_km = predicted_impact_radius_meters / 1000.0
            
            # Find nearest node
            min_dist = float('inf')
            for node, data in self.G.nodes(data=True):
                dist = self.calculate_haversine(incident_lat, incident_lon, data['lat'], data['lon'])
                if dist < min_dist:
                    min_dist = dist
                    nearest_node = node
            
            # Identify edges within radius (u, v or midpoint)
            for u, v, data in self.G.edges(data=True):
                u_lat, u_lon = self.G.nodes[u]['lat'], self.G.nodes[u]['lon']
                v_lat, v_lon = self.G.nodes[v]['lat'], self.G.nodes[v]['lon']
                mid_lat = (u_lat + v_lat) / 2.0
                mid_lon = (u_lon + v_lon) / 2.0
                
                dist_u = self.calculate_haversine(incident_lat, incident_lon, u_lat, u_lon)
                dist_v = self.calculate_haversine(incident_lat, incident_lon, v_lat, v_lon)
                dist_mid = self.calculate_haversine(incident_lat, incident_lon, mid_lat, mid_lon)
                
                if dist_u <= radius_km or dist_v <= radius_km or dist_mid <= radius_km:
                    resolved_blocked_roads.append((u, v))

        # Apply congestion multipliers to blocked/congested roads
        for u, v in resolved_blocked_roads:
            if congested_G.has_edge(u, v):
                congested_G[u][v]['weight'] = congested_G[u][v]['base_weight'] * congestion_multiplier

        # Baseline path under standard conditions
        try:
            normal_route = nx.dijkstra_path(self.G, source, target, weight='weight')
            congested_normal_time = self.get_path_weight(congested_G, normal_route)
            base_normal_time = self.get_path_weight(self.G, normal_route)
        except nx.NetworkXNoPath:
            return {"error": f"No baseline path exists between {source} and {target}."}

        # Alternative route calculation under congested state
        try:
            if algorithm.lower() == 'astar':
                emergency_route = nx.astar_path(
                    congested_G, 
                    source, 
                    target, 
                    heuristic=self.astar_heuristic, 
                    weight='weight'
                )
            else:
                emergency_route = nx.dijkstra_path(congested_G, source, target, weight='weight')
                
            congested_emergency_time = self.get_path_weight(congested_G, emergency_route)
        except nx.NetworkXNoPath:
            return {"error": "No alternative emergency route could be resolved around cordoned blocks."}

        time_saved = congested_normal_time - congested_emergency_time

        return {
            "normal_route": normal_route,
            "normal_time_free_flow": float(base_normal_time),
            "normal_time_congested": float(congested_normal_time),
            "emergency_route": emergency_route,
            "emergency_time_congested": float(congested_emergency_time),
            "time_saved_minutes": float(max(0.0, time_saved)),
            "algorithm_used": "A* Search" if algorithm.lower() == 'astar' else "Dijkstra's Algorithm",
            "nearest_junction_node": nearest_node,
            "resolved_blocked_roads": resolved_blocked_roads
        }

    def find_dynamic_route(
        self,
        source: str,
        target: str,
        congestion_inputs: List[Dict[str, Any]],
        algorithm: str = "astar"
    ) -> Dict[str, Any]:
        """
        Dynamically computes the shortest path on the road graph, applying
        custom headcount-based edge weight multipliers for active camera simulations.
        """
        if source not in self.G or target not in self.G:
            return {"error": f"Junction {source} or {target} not recognized in Bengaluru graph."}

        # Clone graph to avoid polluting base weights
        congested_G = self.G.copy()

        # Build lookup for input headcounts
        headcounts_map = {}
        for item in congestion_inputs:
            src = item.get("source")
            dst = item.get("target")
            hc = item.get("headcount", 0)
            if src and dst:
                headcounts_map[(src, dst)] = hc

        # Apply multiplier to weights
        # - headcount <= 10: x1.0
        # - headcount <= 30: x2.0
        # - headcount <= 60: x4.0
        # - headcount > 60: x10.0 (Extreme/Blocked)
        for u, v, data in congested_G.edges(data=True):
            hc = headcounts_map.get((u, v), 0)
            
            # Double check undirected or bi-directional matches
            if (u, v) not in headcounts_map and (v, u) in headcounts_map:
                hc = headcounts_map[(v, u)]

            if hc <= 10:
                mult = 1.0
            elif hc <= 30:
                mult = 2.0
            elif hc <= 60:
                mult = 4.0
            else:
                mult = 10.0
                
            data['weight'] = data['base_weight'] * mult
            data['headcount'] = hc
            
            # Label density category
            if hc <= 10:
                data['congestion_level'] = 'Low'
            elif hc <= 30:
                data['congestion_level'] = 'Medium'
            elif hc <= 60:
                data['congestion_level'] = 'High'
            else:
                data['congestion_level'] = 'Extreme'

        # Baseline path under standard conditions (no congestion)
        try:
            normal_route = nx.dijkstra_path(self.G, source, target, weight='weight')
            base_normal_time = self.get_path_weight(self.G, normal_route)
        except nx.NetworkXNoPath:
            return {"error": f"No path exists between {source} and {target}."}

        # Calculate optimal path under dynamic congestion conditions
        try:
            if algorithm.lower() == 'astar':
                optimal_route = nx.astar_path(
                    congested_G, 
                    source, 
                    target, 
                    heuristic=self.astar_heuristic, 
                    weight='weight'
                )
            else:
                optimal_route = nx.dijkstra_path(congested_G, source, target, weight='weight')
                
            estimated_time = self.get_path_weight(congested_G, optimal_route)
        except nx.NetworkXNoPath:
            return {
                "optimal_route": [],
                "estimated_travel_time": 999.0,
                "baseline_travel_time": float(base_normal_time),
                "edges_state": self._get_edges_state(congested_G),
                "status": "gridlock"
            }

        # Determine status: Gridlock is triggered if travel time is >= 3x base travel time
        # or if all routes are heavily congested (estimated_time >= base_normal_time * 3.0)
        status = "optimal"
        if len(optimal_route) > 0:
            if estimated_time >= base_normal_time * 3.0:
                status = "gridlock"
            elif estimated_time > base_normal_time * 1.2:
                status = "congested"

        return {
            "optimal_route": optimal_route,
            "estimated_travel_time": float(estimated_time),
            "baseline_travel_time": float(base_normal_time),
            "edges_state": self._get_edges_state(congested_G),
            "status": status
        }

    def _get_edges_state(self, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        states = []
        for u, v, data in graph.edges(data=True):
            states.append({
                "source": u,
                "target": v,
                "weight": float(data["weight"]),
                "base_weight": float(data["base_weight"]),
                "headcount": int(data.get("headcount", 0)),
                "congestion_level": data.get("congestion_level", "Low")
            })
        return states

route_service = RouteService()
