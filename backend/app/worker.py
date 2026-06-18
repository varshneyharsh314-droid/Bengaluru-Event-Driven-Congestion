import os
import time
from celery import Celery
from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)

@celery_app.task(name="tasks.retrain_congestion_model")
def retrain_congestion_model(feedback_data_list):
    """
    Background worker task to retrain the XGBoost congestion model.
    """
    print(f"Starting async model training with {len(feedback_data_list)} audit logs...")
    # Simulate retraining processing duration
    time.sleep(5.0)
    
    # Return simulated calibration results
    return {
        "status": "success",
        "dataset_size": len(feedback_data_list),
        "old_accuracy": 0.81,
        "new_accuracy": 0.88,
        "old_mae": 12.8,
        "new_mae": 9.4
    }

@celery_app.task(name="tasks.process_cctv_video")
def process_cctv_video(video_path: str):
    """
    Background worker task to run inference frame-by-frame on large video feeds.
    """
    print(f"Processing CCTV camera feed from: {video_path}...")
    time.sleep(3.0)
    return {
        "status": "completed",
        "frames_processed": 120,
        "peak_crowd_count": 280,
        "average_crowd_count": 140
    }
