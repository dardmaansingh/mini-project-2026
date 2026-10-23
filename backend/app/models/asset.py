"""NetSentinel ORM Models — Network Assets (switches, APs, servers, clients)."""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database import Base


class NetworkAsset(Base):
    __tablename__ = "network_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # asset_type: switch | access_point | router | server | client | unknown
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    mac_address: Mapped[str] = mapped_column(String(17), nullable=True, index=True)
    vendor: Mapped[str] = mapped_column(String(255), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # AP-specific
    ap_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    ssid: Mapped[str] = mapped_column(String(64), nullable=True)

    # Switch-specific
    switch_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    switch_port: Mapped[str] = mapped_column(String(32), nullable=True)
    vlan_id: Mapped[str] = mapped_column(String(16), nullable=True)

    # Status
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown")  # online | offline | unknown
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
