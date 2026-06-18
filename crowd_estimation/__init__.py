# Crowd Estimation Module for Bengaluru Traffic Police Command Center
# Lazy imports to avoid hard failures when optional dependencies (ultralytics, sahi) are missing
def _import_robust_counter():
    from .robust_counter import RobustCrowdCounter
    return RobustCrowdCounter

def _import_evaluator():
    from .evaluator import CrowdEvaluator
    return CrowdEvaluator

def _import_tracker():
    from .cctv_tracker import CCTVPedestrianTracker
    return CCTVPedestrianTracker

__all__ = [
    "RobustCrowdCounter",
    "CrowdEvaluator",
    "CCTVPedestrianTracker",
]

