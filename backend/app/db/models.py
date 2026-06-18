from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")  # administrator, operator, police_officer
    officer_badge = Column(String, unique=True, index=True, nullable=True)

class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    event_cause = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    requires_road_closure = Column(Boolean, default=False)
    hour = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    duration_hours = Column(Float, nullable=False)
    zone = Column(String, nullable=False)
    junction = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String, default="active")  # active, cleared, unresolved
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prediction = relationship("CongestionPrediction", back_populates="event", uselist=False)
    crowd_analyses = relationship("CrowdAnalysis", back_populates="event")
    feedback = relationship("Feedback", back_populates="event", uselist=False)
    alerts = relationship("Alert", back_populates="event")

class CongestionPrediction(Base):
    __tablename__ = "congestion_predictions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    predicted_congestion = Column(String, nullable=False)
    prob_low = Column(Float, nullable=False)
    prob_med = Column(Float, nullable=False)
    prob_high = Column(Float, nullable=False)
    predicted_delay_min = Column(Integer, nullable=False)
    predicted_duration_minutes = Column(Float, nullable=True)
    predicted_impact_radius_meters = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="prediction")

class PoliceStation(Base):
    __tablename__ = "police_stations"

    id = Column(Integer, primary_key=True, index=True)
    station_name = Column(String, unique=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String, nullable=False)
    available_officers = Column(Integer, default=0)

    # Relationships
    alerts = relationship("Alert", back_populates="station")

class CrowdAnalysis(Base):
    __tablename__ = "crowd_analysis"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    crowd_count = Column(Integer, nullable=False)
    crowd_density = Column(String, nullable=False)
    video_path = Column(String, nullable=True)
    updated_congestion = Column(String, nullable=False)
    police_recommended = Column(Integer, nullable=False)
    barricades_recommended = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="crowd_analyses")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    station_id = Column(Integer, ForeignKey("police_stations.id", ondelete="CASCADE"), nullable=False)
    recipient_phone = Column(String, nullable=False)
    status = Column(String, nullable=False)  # SENT, FAILED
    payload = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="alerts")
    station = relationship("PoliceStation", back_populates="alerts")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    officer_badge = Column(String, nullable=False)
    actual_delay_min = Column(Integer, nullable=False)
    actual_congestion = Column(String, nullable=False)
    event_outcome = Column(String, nullable=False)
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="feedback")

class EmergencyRoute(Base):
    __tablename__ = "emergency_routes"

    id = Column(Integer, primary_key=True, index=True)
    source_junction = Column(String, nullable=False)
    destination_junction = Column(String, nullable=False)
    algorithm = Column(String, nullable=False)
    normal_time_congested = Column(Float, nullable=False)
    emergency_time_congested = Column(Float, nullable=False)
    time_saved_minutes = Column(Float, nullable=False)
    path_json = Column(Text, nullable=False)  # JSON list of nodes representing path
    blocked_links_json = Column(Text, nullable=False)  # JSON list of blocked edges
    timestamp = Column(DateTime, default=datetime.utcnow)
