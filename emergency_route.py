import networkx as nx
import numpy as np

class EmergencyCorridorEngine:
    """
    Transportation AI routing engine.
    Calculates clear emergency corridors bypassing congested or blocked road segments
    using Dijkstra and A* search algorithms.
    """
    def __init__(self, route_graph):
        self.route_graph = route_graph
        self.G = route_graph.get_graph()

    @staticmethod
    def calculate_haversine(lat1, lon1, lat2, lon2):
        """
        Computes the great-circle distance (in km) between two points on the Earth.
        """
        R = 6371.0 # Earth radius in km
        
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c

    def astar_heuristic(self, u, v):
        """
        Admissible A* heuristic: calculates straight-line travel time (in minutes)
        assuming free-flow speed of 50 km/h.
        """
        lat1, lon1 = self.G.nodes[u]['lat'], self.G.nodes[u]['lon']
        lat2, lon2 = self.G.nodes[v]['lat'], self.G.nodes[v]['lon']
        
        dist_km = self.calculate_haversine(lat1, lon1, lat2, lon2)
        # Time = (distance / speed) * 60 minutes
        estimated_time_min = (dist_km / 50.0) * 60.0
        return estimated_time_min

    def get_path_weight(self, graph, path):
        """Calculates total travel time weight for a given node sequence path."""
        total_weight = 0
        for i in range(len(path) - 1):
            total_weight += graph[path[i]][path[i+1]]['weight']
        return total_weight

    def find_emergency_corridor(self, source, target, blocked_roads, congestion_multiplier=10.0, algorithm="astar"):
        """
        Simulates congestion on blocked roads and calculates:
        - Normal Route under congestion
        - Emergency Route under congestion
        - Travel time saved
        """
        # 1. Create a copy of the graph to simulate congestion
        congested_G = self.G.copy()
        
        # 2. Apply congestion multiplier to blocked edges
        # blocked_roads is a list of tuples: [('SilkBoardJunc', 'HSRLayout14thMain'), ...]
        for u, v in blocked_roads:
            if congested_G.has_edge(u, v):
                congested_G[u][v]['weight'] = congested_G[u][v]['base_weight'] * congestion_multiplier

        # 3. Find baseline route under free-flow conditions (Normal Route)
        try:
            normal_route = nx.dijkstra_path(self.G, source, target, weight='weight')
            # Calculate the travel time on this original path under the NEW congestion state
            congested_normal_time = self.get_path_weight(congested_G, normal_route)
            base_normal_time = self.get_path_weight(self.G, normal_route)
        except nx.NetworkXNoPath:
            return {"error": f"No path exists between {source} and {target}."}

        # 4. Find the optimal alternative path (Emergency Route)
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
            return {"error": f"No alternative emergency path could be resolved."}

        time_saved = congested_normal_time - congested_emergency_time

        return {
            "normal_route": normal_route,
            "normal_time_free_flow": base_normal_time,
            "normal_time_congested": congested_normal_time,
            "emergency_route": emergency_route,
            "emergency_time_congested": congested_emergency_time,
            "time_saved_minutes": max(0.0, time_saved),
            "algorithm_used": "A* Search" if algorithm.lower() == 'astar' else "Dijkstra's Algorithm"
        }

if __name__ == "__main__":
    from route_graph import BengaluruRouteGraph
    
    graph = BengaluruRouteGraph()
    engine = EmergencyCorridorEngine(graph)
    
    blocks = [('HSRLayout14thMain', 'AgaraJunction')]
    res = engine.find_emergency_corridor('SilkBoardJunc', 'IbblurJunction', blocks, 10.0, 'astar')
    
    print("Test routing results:")
    for k, v in res.items():
        print(f"  {k}: {v}")
