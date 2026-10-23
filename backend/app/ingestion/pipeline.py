"""
NetSentinel — Event Storage Service.

Persists normalized events to PostgreSQL and
broadcasts them via WebSocket for live dashboard updates.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone

from backend.app.normalization.schema import NormalizedEvent
from backend.app.models.event import NetworkEvent
from backend.app.database import AsyncSessionLocal
from backend.app.core.websocket import ws_manager
from backend.app.detection.engine import DetectionEngine
from backend.app.alerting.manager import alert_manager

logger = logging.getLogger(__name__)


class EventPipeline:
    """
    Full event processing pipeline:
    1. Persist normalized event to DB
    2. Broadcast via WebSocket
    3. Pass to detection engine
    """

    def __init__(self):
        self._engine = DetectionEngine(on_alert=alert_manager.handle_alert)

    @property
    def detection_engine(self) -> DetectionEngine:
        return self._engine

    async def ingest(self, event: NormalizedEvent) -> None:
        """Process a single normalized event through the full pipeline."""
        db_event = self._to_db(event)
        await self._persist(db_event)
        await self._broadcast(event)
        await self._engine.process_event(event)

    @staticmethod
    def _to_db(event: NormalizedEvent) -> NetworkEvent:
        return NetworkEvent(
            id=event.event_id,
            timestamp_utc=event.timestamp_utc,
            event_type=event.event_type,
            source_type=event.source_type,
            source_ip=event.source_ip,
            source_port=event.source_port,
            destination_ip=event.destination_ip,
            destination_port=event.destination_port,
            protocol=event.protocol,
            client_mac=event.client_mac,
            ap_id=event.ap_id,
            switch_id=event.switch_id,
            switch_port=event.switch_port,
            vlan_id=event.vlan_id,
            domain=event.domain,
            dns_record_type=event.dns_record_type,
            dns_response_code=event.dns_response_code,
            bytes_sent=event.bytes_sent,
            bytes_received=event.bytes_received,
            packets=event.packets,
            duration_ms=event.duration_ms,
            username=event.username,
            authentication_result=event.authentication_result,
            simulated=event.simulated,
            raw_event_reference=event.raw_event_reference,
            ingestion_source_id=event.ingestion_source_id,
            extra_metadata=event.extra_metadata,
        )

    @staticmethod
    async def _persist(db_event: NetworkEvent) -> None:
        try:
            async with AsyncSessionLocal() as session:
                session.add(db_event)
                await session.commit()
        except Exception as exc:
            logger.error("Failed to persist event %s: %s", db_event.id, exc, exc_info=True)

    @staticmethod
    async def _broadcast(event: NormalizedEvent) -> None:
        payload = {
            "type": "event.new",
            "data": {
                "id": event.event_id,
                "timestamp_utc": event.timestamp_utc.isoformat(),
                "event_type": event.event_type,
                "source_type": event.source_type,
                "source_ip": event.source_ip,
                "destination_ip": event.destination_ip,
                "destination_port": event.destination_port,
                "protocol": event.protocol,
                "domain": event.domain,
                "ap_id": event.ap_id,
                "simulated": event.simulated,
            },
        }
        await ws_manager.broadcast(payload)


# Singleton
pipeline = EventPipeline()
