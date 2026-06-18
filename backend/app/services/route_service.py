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
        blocked_roads: List[Tuple[str, str]], 
        congestion_multiplier: float = 10.0, 
        algorithm: str = "astar"
    ) -> Dict[str, Any]:
        """
        Calculates optimal emergency corridor by routing around high congested nodes.
        """
        if source not in self.G or target not in self.G:
            return {"error": f"Junction {source} or {target} not recognized in Bengaluru graph."}

        congested_G = self.G.copy()
        
        # Apply congestion multipliers to blocked roads
        for u, v in blocked_roads:
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
            "algorithm_used": "A* Search" if algorithm.lower() == 'astar' else "Dijkstra's Algorithm"
        }

route_service = RouteService()
