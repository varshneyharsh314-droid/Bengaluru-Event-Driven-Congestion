import networkx as nx
import numpy as np
import json

class BengaluruRouteRecommender:
    def __init__(self):
        # 1. Initialize empty graph (directed, since traffic flow has one-way lanes)
        self.G = nx.DiGraph()
        
        # 2. Add key Bengaluru junctions with GPS coordinates (lat, lon)
        # Coordinates are necessary for A* heuristic distance calculations
        junction_coords = {
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
        
        for junc, coords in junction_coords.items():
            self.G.add_node(junc, lat=coords[0], lon=coords[1])
            
        # 3. Add road edges with base attributes
        # 'weight' represents travel time in minutes under free-flow conditions
        # 'length' represents distance in kilometers
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
    def calculate_haversine(lat1, lon1, lat2, lon2):
        """
        Computes the great-circle distance (in km) between two points on the Earth.
        """
        # Earth radius in kilometers
        R = 6371.0
        
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c

    def astar_heuristic(self, u, v):
        """
        Admissible A* heuristic: calculates straight-line travel time.
        Assumes free-flow speed of 50 km/h.
        """
        lat1, lon1 = self.G.nodes[u]['lat'], self.G.nodes[u]['lon']
        lat2, lon2 = self.G.nodes[v]['lat'], self.G.nodes[v]['lon']
        
        dist_km = self.calculate_haversine(lat1, lon1, lat2, lon2)
        
        # Time (minutes) = (distance / speed) * 60 minutes
        # Free flow speed = 50 km/h
        estimated_time_min = (dist_km / 50.0) * 60.0
        return estimated_time_min

    def get_path_weight(self, graph, path):
        """
        Sums the weights of all edges along a path.
        """
        total_weight = 0
        for i in range(len(path) - 1):
            total_weight += graph[path[i]][path[i+1]]['weight']
        return total_weight

    def recommend_alternative_route(self, source, target, congested_edges, multiplier=10.0, algorithm='dijkstra'):
        """
        Simulates congestion on specific edges and returns the alternative route.
        
        Parameters:
        - source: Start node (junction)
        - target: Destination node (junction)
        - congested_edges: List of tuples representing directed edges with congestion (e.g. [('HSRLayout14thMain', 'AgaraJunction')])
        - multiplier: The factor by which weight (travel time) increases under congestion (default 10x)
        - algorithm: 'dijkstra' or 'astar'
        """
        # 1. Create a copy of the graph to simulate congestion without mutating base network
        congested_G = self.G.copy()
        
        # 2. Simulate congestion by scaling weights of target edges
        for u, v in congested_edges:
            if congested_G.has_edge(u, v):
                congested_G[u][v]['weight'] = congested_G[u][v]['base_weight'] * multiplier
                
        # 3. Find baseline route under free-flow conditions
        try:
            baseline_route = nx.dijkstra_path(self.G, source, target, weight='weight')
            # Calculate what the travel time on this original route would be *under the new congestion*
            congested_baseline_time = self.get_path_weight(congested_G, baseline_route)
        except nx.NetworkXNoPath:
            return {"error": f"No path exists between {source} and {target}."}

        # 4. Find the optimal alternative route in the congested graph
        try:
            if algorithm.lower() == 'astar':
                # Run A* shortest path search using coordinates
                alternative_route = nx.astar_path(
                    congested_G, 
                    source, 
                    target, 
                    heuristic=self.astar_heuristic, 
                    weight='weight'
                )
            else:
                # Run standard Dijkstra shortest path search
                alternative_route = nx.dijkstra_path(congested_G, source, target, weight='weight')
                
            alternative_time = self.get_path_weight(congested_G, alternative_route)
        except nx.NetworkXNoPath:
            return {"error": f"No alternative route could be found after applying congestion."}

        # 5. Calculate travel time saved by taking the alternative path
        time_saved = congested_baseline_time - alternative_time
        
        # Format the return payload matching the user's JSON specs
        result = {
            "avoid": [f"{u} -> {v}" for u, v in congested_edges],
            "recommended_route": alternative_route,
            "travel_time_saved": f"{max(0.0, time_saved):.1f} minutes"
        }
        
        return result

# -------------------------------------------------------------
# RUN DEMO SCRIPT
# -------------------------------------------------------------
if __name__ == "__main__":
    recommender = BengaluruRouteRecommender()
    
    # Define route: Silk Board to Ibblur Junction
    src = "SilkBoardJunc"
    tgt = "IbblurJunction"
    
    # Scenario: High congestion on the main Outer Ring Road link between HSR 14th Main and Agara Junction
    blockage = [('HSRLayout14thMain', 'AgaraJunction')]
    
    print("==================================================")
    print("BENGALURU ROUTING ENGINE: ALTERNATIVE ROUTE SEARCH")
    print(f"Source: {src} | Destination: {tgt}")
    print(f"Congestion Blockage simulated on: {blockage[0][0]} -> {blockage[0][1]} (10x delay multiplier)")
    print("==================================================")
    
    # Run Dijkstra Alternative Search
    dijkstra_res = recommender.recommend_alternative_route(src, tgt, blockage, algorithm='dijkstra')
    print("\n--- [Dijkstra Algorithm Result] ---")
    print(json.dumps(dijkstra_res, indent=4))
    
    # Run A* Alternative Search
    astar_res = recommender.recommend_alternative_route(src, tgt, blockage, algorithm='astar')
    print("\n--- [A* (A-Star) Algorithm Result] ---")
    print(json.dumps(astar_res, indent=4))
