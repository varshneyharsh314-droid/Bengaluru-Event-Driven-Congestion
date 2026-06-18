from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    role: str = "operator"
    officer_badge: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

# Event Schemas
class EventBase(BaseModel):
    event_type: str
    event_cause: str
    priority: str
    requires_road_closure: bool
    hour: int
    day_of_week: int
    duration_hours: float
    zone: str
    junction: str
    latitude: float
    longitude: float
    description: Optional[str] = ""

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    event_id: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Congestion Prediction Schemas
class PredictionBase(BaseModel):
    predicted_congestion: str
    prob_low: float
    prob_med: float
    prob_high: float
    predicted_delay_min: int

class PredictionResponse(PredictionBase):
    id: int
    event_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Resource Details Helper
class ResourceDetails(BaseModel):
    police_officers: int
    barricades: int
    vms_boards: Optional[int] = 0

# Full Incident Prediction Response
class IncidentPredictionResult(BaseModel):
    event_id: str
    predicted_congestion: str
    probabilities: Dict[str, float]
    predicted_delay_min: int
    resources: ResourceDetails
    predicted_duration_minutes: Optional[float] = None
    predicted_impact_radius_meters: Optional[float] = None

# Police Station Schemas
class PoliceStationBase(BaseModel):
    station_name: str
    latitude: float
    longitude: float
    phone: str
    available_officers: int

class PoliceStationResponse(PoliceStationBase):
    id: int

    class Config:
        from_attributes = True

# Alert Schemas
class AlertCreate(BaseModel):
    recipient_phone: str
    event_type: str
    priority: str
    congestion: str
    expected_delay: int
    police_needed: int
    barricades: int
    location_name: str
    latitude: float
    longitude: float

class AlertResponse(BaseModel):
    id: int
    event_id: str
    station_id: int
    recipient_phone: str
    status: str
    payload: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Crowd Analysis Schemas
class CrowdAnalysisResponse(BaseModel):
    id: int
    event_id: str
    crowd_count: int
    crowd_density: str
    video_path: Optional[str] = None
    updated_congestion: str
    police_recommended: int
    barricades_recommended: int
    timestamp: datetime
    annotated_image_base64: Optional[str] = None

    class Config:
        from_attributes = True

# Feedback Schemas
class FeedbackCreate(BaseModel):
    event_id: str
    officer_badge: str
    actual_delay_min: int
    actual_congestion: str
    event_outcome: str
    comments: Optional[str] = None

class FeedbackResponse(FeedbackCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Emergency Route Schemas
class EmergencyRouteRequest(BaseModel):
    source: str
    destination: str
    blocked_roads: List[Tuple[str, str]] = Field(default_factory=list)
    congestion_multiplier: float = 10.0
    algorithm: str = "astar"
    incident_lat: Optional[float] = None
    incident_lon: Optional[float] = None
    predicted_impact_radius_meters: Optional[float] = None

class EmergencyRouteResponse(BaseModel):
    normal_route: List[str]
    normal_time_free_flow: float
    normal_time_congested: float
    emergency_route: List[str]
    emergency_time_congested: float
    time_saved_minutes: float
    algorithm_used: str
    nearest_junction_node: Optional[str] = None
    resolved_blocked_roads: Optional[List[Tuple[str, str]]] = None

class TimelineEventsResponse(BaseModel):
    event_id: str
    junction: str
    latitude: float
    longitude: float
    start_hour: int
    end_hour: int
    congestion_level: str
    delay_min: int
    police_deployed: int

class RetrainingStats(BaseModel):
    dataset_size: int
    old_accuracy: float
    new_accuracy: float
    old_mae: float
    new_mae: float

class VideoAnalysisResponse(BaseModel):
    total_frames_processed: int
    peak_headcount: int
    average_headcount: int
    crowd_density: str
    per_frame_counts: List[int] = []
    updated_congestion: Optional[str] = None
    police_recommended: Optional[int] = None
    barricades_recommended: Optional[int] = None

# Dynamic Multi-Camera Simulator Routing Schemas
class CongestionInput(BaseModel):
    source: str
    target: str
    headcount: int

class DynamicRoutingRequest(BaseModel):
    source: str
    target: str
    algorithm: str = "astar"
    congestion_inputs: List[CongestionInput] = []

class DynamicRoutingResponse(BaseModel):
    optimal_route: List[str]
    estimated_travel_time: float
    baseline_travel_time: float
    edges_state: List[Dict[str, Any]]
    status: str
