"""
NetSentinel Backend — Application Configuration.
All settings are loaded from environment variables (.env).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    app_name: str = "NetSentinel"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 480

    # Database
    database_url: str = "postgresql+asyncpg://netsentinel:netsentinel_dev@localhost:5432/netsentinel"
    database_sync_url: str = "postgresql://netsentinel:netsentinel_dev@localhost:5432/netsentinel"

    # Server
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",")]

    # Synthetic generator
    synthetic_enabled: bool = True
    synthetic_events_per_second: float = 2.0
    synthetic_anomaly_rate: float = 0.05

    # Detection
    detection_enabled: bool = True
    detection_window_seconds: int = 60
    dns_query_rate_threshold: int = 50
    port_scan_port_threshold: int = 20
    auth_failure_threshold: int = 5
    bandwidth_anomaly_factor: float = 3.0

    # WebSocket
    ws_heartbeat_interval: int = 30

    # Logging
    log_level: str = "INFO"


settings = Settings()
