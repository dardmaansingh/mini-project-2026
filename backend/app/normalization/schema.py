"""
NetSentinel — Normalized Event Schema (Pydantic).

This is the canonical event representation used throughout the pipeline.
All ingestion adapters must produce a NormalizedEvent.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class NormalizedEvent(BaseModel):
    """Canonical network event representation."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: datetime
    event_type: str  # dns_query | connection | auth_failure | auth_success | dhcp | flow | ap_event | switch_event
    source_type: str  # synthetic | syslog | zeek | json_file | csv_file

    # Network
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None

    # Device (only when available and authorized)
    client_mac: Optional[str] = None
    ap_id: Optional[str] = None
    switch_id: Optional[str] = None
    switch_port: Optional[str] = None
    vlan_id: Optional[str] = None

    # DNS
    domain: Optional[str] = None
    dns_record_type: Optional[str] = None
    dns_response_code: Optional[str] = None

    # Flow/bandwidth
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    packets: Optional[int] = None
    duration_ms: Optional[float] = None

    # Authentication
    username: Optional[str] = None
    authentication_result: Optional[str] = None  # success | failure | timeout

    # Metadata
    simulated: bool = False
    raw_event_reference: Optional[str] = None
    ingestion_source_id: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
