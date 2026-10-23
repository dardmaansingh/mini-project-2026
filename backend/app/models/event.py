"""NetSentinel ORM Models — Normalized Network Events."""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, BigInteger, Integer, Text, JSON, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database import Base


class NetworkEvent(Base):
    __tablename__ = "network_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # dns_query | connection | auth_failure | auth_success | dhcp | flow | syslog | ap_event | switch_event

    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # synthetic | syslog | zeek | json_file | csv_file | manual

    # Network identifiers
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    source_port: Mapped[int] = mapped_column(Integer, nullable=True)
    destination_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    destination_port: Mapped[int] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str] = mapped_column(String(16), nullable=True)

    # Device identifiers (only when available/authorized)
    client_mac: Mapped[str] = mapped_column(String(17), nullable=True, index=True)
    ap_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    switch_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    switch_port: Mapped[str] = mapped_column(String(32), nullable=True)
    vlan_id: Mapped[str] = mapped_column(String(16), nullable=True)

    # DNS fields
    domain: Mapped[str] = mapped_column(String(512), nullable=True)
    dns_record_type: Mapped[str] = mapped_column(String(16), nullable=True)
    dns_response_code: Mapped[str] = mapped_column(String(32), nullable=True)

    # Flow/bandwidth
    bytes_sent: Mapped[int] = mapped_column(BigInteger, nullable=True)
    bytes_received: Mapped[int] = mapped_column(BigInteger, nullable=True)
    packets: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=True)

    # Authentication
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    authentication_result: Mapped[str] = mapped_column(String(32), nullable=True)

    # Metadata
    simulated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    raw_event_reference: Mapped[str] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Ingestion source ref
    ingestion_source_id: Mapped[str] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        Index("ix_events_source_ip_ts", "source_ip", "timestamp_utc"),
        Index("ix_events_type_ts", "event_type", "timestamp_utc"),
        Index("ix_events_ap_ts", "ap_id", "timestamp_utc"),
    )
