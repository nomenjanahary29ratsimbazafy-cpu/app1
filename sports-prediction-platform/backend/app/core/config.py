import os
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "Sports Prediction Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/sports_prediction"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_CACHE_TTL: int = 300  # 5 minutes default
    
    # Message Queue (RabbitMQ)
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", RABBITMQ_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", RABBITMQ_URL)
    
    # External APIs
    API_FOOTBALL_KEY: Optional[str] = os.getenv("API_FOOTBALL_KEY")
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"
    
    SPORT_RADAR_KEY: Optional[str] = os.getenv("SPORT_RADAR_KEY")
    ODDS_PORTAL_KEY: Optional[str] = os.getenv("ODDS_PORTAL_KEY")
    
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    
    # ML Configuration
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "/app/ml/models")
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    MODEL_CONFIDENCE_THRESHOLD: float = 0.65
    VALUE_BET_THRESHOLD: float = 0.05  # 5% minimum value
    
    # Monte Carlo Simulation
    MONTE_CARLO_ITERATIONS: int = 10000
    MONTE_CARLO_SEED: Optional[int] = None
    
    # Risk Management
    DEFAULT_BANKROLL: float = 10000.0
    MAX_STAKE_PERCENTAGE: float = 0.05  # 5% max stake
    KELLY_FRACTION: float = 0.25  # Fractional Kelly (25%)
    STOP_LOSS_PERCENTAGE: float = 0.20  # 20% drawdown stop
    MAX_DAILY_BETS: int = 20
    MAX_EXPOSURE_PER_MATCH: float = 0.10  # 10% max exposure per match
    
    # Agent Configuration
    AGENT_TIMEOUT_SECONDS: int = 30
    AGENT_RETRY_COUNT: int = 3
    AGENT_WEIGHT_DATA_COLLECTOR: float = 1.0
    AGENT_WEIGHT_STATISTICAL: float = 1.2
    AGENT_WEIGHT_ML: float = 1.3
    AGENT_WEIGHT_MARKET: float = 1.1
    AGENT_WEIGHT_PSYCHOLOGICAL: float = 0.8
    AGENT_WEIGHT_RISK: float = 1.0
    
    # Rate Limiting
    RATE_LIMIT_PER_SECOND: int = 10
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://localhost:3000",
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = "/var/log/sports-prediction/app.log"
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
