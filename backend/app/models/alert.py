"""NetSentinel ORM Models — Security Alerts."""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Integer, Text, JSON, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # informational | low | medium | high | critical
    confidence: Mapped[str] = mapped_column(String(16), nullable=True)
    # low | medium | high

    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Source details
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    destination_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    source_port: Mapped[int] = mapped_column(Integer, nullable=True)
    destination_port: Mapped[int] = mapped_column(Integer, nullable=True)
    ap_id: Mapped[str] = mapped_column(String(64), nullable=True)
    switch_id: Mapped[str] = mapped_column(String(64), nullable=True)
    switch_port: Mapped[str] = mapped_column(String(32), nullable=True)
    vlan_id: Mapped[str] = mapped_column(String(16), nullable=True)

    # Alert lifecycle
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    # new | acknowledged | investigating | resolved | false_positive
    event_count: Mapped[int] = mapped_column(Integer, default=1)
    assigned_to: Mapped[str] = mapped_column(String(64), nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Evidence
    evidence: Mapped[dict] = mapped_column(JSON, nullable=True)
    recommended_steps: Mapped[str] = mapped_column(Text, nullable=True)

    # Dedup key — used to match existing open alerts for the same incident
    dedup_key: Mapped[str] = mapped_column(String(255), nullable=True, index=True)

    simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    notes: Mapped[list["AlertNote"]] = relationship("AlertNote", back_populates="alert", lazy="selectin")

    __table_args__ = (
        Index("ix_alerts_severity_status", "severity", "status"),
        Index("ix_alerts_rule_first_seen", "rule_id", "first_seen"),
    )


class AlertNote(Base):
    __tablename__ = "alert_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id: Mapped[str] = mapped_column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alert: Mapped["Alert"] = relationship("Alert", back_populates="notes")
