import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Command Center API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bengaluru_traffic_police_secret_key_2026_top_secret")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # PostgreSQL Database Settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "traffic_ops")
    
    USE_SQLITE: bool = True

    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            return "sqlite:///./traffic_ops.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


    # Redis Queue Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    
    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # ML Model Configs
    MODEL_DIR: str = os.getenv("MODEL_DIR", "ml_models")
    CONGESTION_MODEL_PATH: str = os.path.join(MODEL_DIR, "congestion_model.joblib")
    YOLO_MODEL_PATH: str = os.path.join(MODEL_DIR, "yolov8n.pt")
    POLICE_STATION_CSV: str = os.path.join(MODEL_DIR, "police_station.csv")

    # Twilio SMS Configs
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "AC3c68d9f33472fe976a39c356fc1a8767")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "b48b39ca3f9a6c7e8886f14920f10f29")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "+19843676327")
    TWILIO_RECIPIENT: str = os.getenv("TWILIO_RECIPIENT", "+918709161536")

    class Config:
        case_sensitive = True

settings = Settings()
