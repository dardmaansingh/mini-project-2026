"""NetSentinel ORM Models — Detection Rules and Data Sources."""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Integer, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database import Base


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # e.g. "RULE-001"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=True)
    event_source_requirement: Mapped[str] = mapped_column(String(64), nullable=True)

    # Configuration
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    confidence: Mapped[str] = mapped_column(String(16), default="medium")
    detection_window_seconds: Mapped[int] = mapped_column(Integer, default=60)
    threshold: Mapped[float] = mapped_column(Float, nullable=True)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=300)
    extra_config: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Statistics
    alert_count: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    false_positive_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    # synthetic | syslog | zeek | json_file | csv_file | netflow | radius | dhcp | ids

    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    # healthy | degraded | offline | unknown

    host: Mapped[str] = mapped_column(String(255), nullable=True)
    port: Mapped[int] = mapped_column(Integer, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=True)

    last_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    events_total: Mapped[int] = mapped_column(Integer, default=0)
    events_last_minute: Mapped[int] = mapped_column(Integer, default=0)
    parse_failures: Mapped[int] = mapped_column(Integer, default=0)

    heartbeat_interval_seconds: Mapped[int] = mapped_column(Integer, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
