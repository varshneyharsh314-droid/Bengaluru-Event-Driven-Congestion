import uvicorn
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.api.endpoints import auth, traffic
from app.core.websocket_manager import ws_manager
from app.db import models

# Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify ["http://localhost:5173"] or Vercel URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bind routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(traffic.router, prefix=f"{settings.API_V1_STR}/traffic", tags=["traffic"])

# WebSocket Alert Broacast Endpoint
@app.websocket("/api/traffic/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # We keep the connection alive by waiting for any dummy text/pings
            data = await websocket.receive_text()
            # Echo back a heartbeat ping
            await websocket.send_json({"event": "PONG", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.on_event("startup")
def startup_populate_data():
    """
    Initializes PostgreSQL tables and populates seed data if empty.
    """
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Seed Police Stations
        stations_count = db.query(models.PoliceStation).count()
        if stations_count == 0:
            print("Seeding initial police stations list...")
            stations_data = [
                ('Madiwala Traffic Police Station', 12.9225, 77.6215, '+91 94808-01824', 18),
                ('HSR Layout Traffic Police Station', 12.9102, 77.6412, '+91 94808-01826', 14),
                ('Koramangala Traffic Police Station', 12.9332, 77.6245, '+91 94808-01828', 22),
                ('BTM Layout Police Station', 12.9154, 77.6052, '+91 94808-01830', 11),
                ('Jayanagar Traffic Police Station', 12.9282, 77.5891, '+91 94808-01832', 15),
                ('Hebbal Traffic Police Station', 13.0362, 77.5975, '+91 94808-01834', 16),
                ('Peenya Traffic Police Station', 13.0289, 77.5358, '+91 94808-01836', 12),
                ('Indiranagar Traffic Police Station', 12.9745, 77.6385, '+91 94808-01838', 20),
                ('Halasuru Traffic Police Station', 12.9778, 77.6248, '+91 94808-01840', 15),
                ('Shivajinagar Traffic Police Station', 12.9856, 77.6035, '+91 94808-01842', 19),
            ]
            for name, lat, lng, phone, officers in stations_data:
                db_station = models.PoliceStation(
                    station_name=name,
                    latitude=lat,
                    longitude=lng,
                    phone=phone,
                    available_officers=officers
                )
                db.add(db_station)
            db.commit()

        # 2. Seed Default Operational User for quick testing
        user_count = db.query(models.User).count()
        if user_count == 0:
            print("Creating default operator account (admin@bengalurutraffic.gov.in / password)...")
            from app.core.security import get_password_hash
            db_user = models.User(
                email="admin@bengalurutraffic.gov.in",
                hashed_password=get_password_hash("password"),
                role="administrator",
                officer_badge="KA-POL-9999"
            )
            db.add(db_user)
            db.commit()

        # 3. Seed Synthetic events log (matches SQLite mockup)
        events_count = db.query(models.Event).count()
        if events_count == 0:
            print("Populating initial event log seed data...")
            base_time = datetime.datetime.utcnow() - datetime.timedelta(days=10)
            causes = ["accident", "vehicle_breakdown", "water_logging", "construction"]
            zones = ["Central Zone 2", "East Zone 1", "South Zone 1", "North Zone 2"]
            junctions = ["SilkBoardJunc", "HebbalFlyoverJunc", "IbblurJunction", "Peenya14thCrossJunc"]
            
            # Map mock coordinates
            junc_coords = {
                "SilkBoardJunc": (12.9176, 77.6246),
                "HebbalFlyoverJunc": (13.0362, 77.5975),
                "IbblurJunction": (12.9234, 77.6712),
                "Peenya14thCrossJunc": (13.0289, 77.5358)
            }
            
            for i in range(25):
                event_id = f"EV-2026-{i:03d}"
                event_type = "unplanned" if i % 2 == 0 else "planned"
                event_cause = causes[i % len(causes)]
                priority = "High" if i % 3 == 0 else "Low"
                road_closure = True if (i % 4 == 0 and priority == "High") else False
                h = 8 + (i % 12)
                dow = i % 7
                duration = 0.5 + (i % 5) * 0.75
                zone = zones[i % len(zones)]
                junc = junctions[i % len(junctions)]
                lat, lng = junc_coords.get(junc, (12.9716, 77.5946))
                
                pred_congestion = "High" if (road_closure or duration > 3.0) else ("Medium" if duration > 1.0 else "Low")
                base_delay = 15 if pred_congestion == "Low" else (45 if pred_congestion == "Medium" else 90)
                event_time = base_time + datetime.timedelta(hours=i*8)

                db_event = models.Event(
                    event_id=event_id,
                    event_type=event_type,
                    event_cause=event_cause,
                    priority=priority,
                    requires_road_closure=road_closure,
                    hour=h,
                    day_of_week=dow,
                    duration_hours=duration,
                    zone=zone,
                    junction=junc,
                    latitude=lat,
                    longitude=lng,
                    status="active" if i > 15 else "cleared",
                    timestamp=event_time
                )
                db.add(db_event)

                db_pred = models.CongestionPrediction(
                    event_id=event_id,
                    predicted_congestion=pred_congestion,
                    prob_low=0.7 if pred_congestion == "Low" else 0.15,
                    prob_med=0.7 if pred_congestion == "Medium" else 0.15,
                    prob_high=0.7 if pred_congestion == "High" else 0.15,
                    predicted_delay_min=base_delay,
                    timestamp=event_time
                )
                db.add(db_pred)
                
                # If cleared, add feedback logs
                if i <= 15:
                    db_feedback = models.Feedback(
                        event_id=event_id,
                        officer_badge=f"KA-POL-{8000 + i}",
                        actual_delay_min=int(base_delay + (i % 5)),
                        actual_congestion=pred_congestion,
                        event_outcome="Normal Clearance" if not road_closure else "Cleared with Diversion",
                        comments="Cleared under baseline conditions.",
                        timestamp=event_time + datetime.timedelta(hours=2)
                    )
                    db.add(db_feedback)

            db.commit()
            print("Database seeding completed.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
