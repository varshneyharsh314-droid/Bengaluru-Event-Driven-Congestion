import networkx as nx

class BengaluruRouteGraph:
    """
    Transportation AI Graph representation of Bengaluru key junctions and corridors.
    Provides node coordinate metadata and edge attributes for routing algorithms.
    """
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
        """Constructs the NetworkX directed graph."""
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

    def get_graph(self):
        """Returns the built NetworkX graph."""
        return self.G

    def get_junction_names(self):
        """Returns the list of all junctions."""
        return list(self.junction_coords.keys())
        
    def get_all_edges(self):
        """Returns all directed edges in the network."""
        return list(self.G.edges())
