"""
NetSentinel — Alert Manager.

Handles alert deduplication, lifecycle management,
and WebSocket notification push.
"""

from __future__ import annotations
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.models.alert import Alert, AlertNote
from backend.app.database import AsyncSessionLocal
from backend.app.core.websocket import ws_manager

logger = logging.getLogger(__name__)

# Severity order for comparison
_SEVERITY_ORDER = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _dedup_key(alert_data: dict) -> str:
    """Build a deduplication key from rule + source."""
    rule = alert_data.get("rule_id", "UNKNOWN")
    src = alert_data.get("source_ip", "")
    return f"{rule}:{src}"


class AlertManager:
    """
    Creates, deduplicates, and updates security alerts.
    Broadcasts new/updated alerts via WebSocket.
    """

    def __init__(self):
        # In-memory dedup cache: dedup_key -> alert_id
        self._open_alerts: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def handle_alert(self, alert_data: dict) -> None:
        """
        Called by the detection engine when a rule fires.
        Either creates a new alert or updates an existing open one.
        """
        dedup = _dedup_key(alert_data)
        async with self._lock:
            existing_id = self._open_alerts.get(dedup)

        if existing_id:
            await self._update_alert(existing_id, alert_data)
        else:
            alert_id = await self._create_alert(alert_data, dedup)
            if alert_id:
                async with self._lock:
                    self._open_alerts[dedup] = alert_id

    async def _create_alert(self, data: dict, dedup: str) -> Optional[str]:
        alert_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        alert = Alert(
            id=alert_id,
            rule_id=data["rule_id"],
            rule_name=data["rule_name"],
            title=data["title"],
            description=data.get("description"),
            severity=data.get("severity", "medium"),
            confidence=data.get("confidence", "medium"),
            first_seen=now,
            last_seen=now,
            source_ip=data.get("source_ip"),
            destination_ip=data.get("destination_ip"),
            source_port=data.get("source_port"),
            destination_port=data.get("destination_port"),
            ap_id=data.get("ap_id"),
            switch_id=data.get("switch_id"),
            switch_port=data.get("switch_port"),
            vlan_id=data.get("vlan_id"),
            status="new",
            event_count=1,
            evidence=data.get("evidence"),
            recommended_steps="\n".join(data.get("recommended_steps", [])),
            dedup_key=dedup,
            simulated=data.get("simulated", False),
        )
        try:
            async with AsyncSessionLocal() as session:
                session.add(alert)
                await session.commit()
            await self._broadcast("alert.new", alert)
            logger.info("Alert created [%s]: %s", data["rule_id"], data["title"])
            return alert_id
        except Exception as exc:
            logger.error("Failed to create alert: %s", exc, exc_info=True)
            return None

    async def _update_alert(self, alert_id: str, data: dict) -> None:
        now = datetime.now(timezone.utc)
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Alert).where(Alert.id == alert_id))
                alert = result.scalar_one_or_none()
                if not alert or alert.status in ("resolved", "false_positive"):
                    # Existing alert closed — remove from dedup cache
                    dedup = _dedup_key(data)
                    async with self._lock:
                        self._open_alerts.pop(dedup, None)
                    return
                alert.last_seen = now
                alert.event_count += 1
                # Escalate severity if new detection is higher
                if _SEVERITY_ORDER.get(data.get("severity", ""), 0) > _SEVERITY_ORDER.get(alert.severity, 0):
                    alert.severity = data["severity"]
                await session.commit()
            await self._broadcast("alert.updated", alert)
        except Exception as exc:
            logger.error("Failed to update alert %s: %s", alert_id, exc, exc_info=True)

    async def close_resolved_alerts(self) -> None:
        """Prune resolved/false-positive alerts from the in-memory dedup cache."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Alert.dedup_key).where(Alert.status.in_(["resolved", "false_positive"]))
                )
                closed_keys = {row[0] for row in result.all() if row[0]}
            async with self._lock:
                for k in closed_keys:
                    self._open_alerts.pop(k, None)
        except Exception as exc:
            logger.error("Error pruning resolved alerts: %s", exc, exc_info=True)

    async def _broadcast(self, event_type: str, alert: Alert) -> None:
        payload = {
            "type": event_type,
            "data": {
                "id": alert.id,
                "rule_id": alert.rule_id,
                "rule_name": alert.rule_name,
                "title": alert.title,
                "severity": alert.severity,
                "confidence": alert.confidence,
                "status": alert.status,
                "first_seen": alert.first_seen.isoformat() if alert.first_seen else None,
                "last_seen": alert.last_seen.isoformat() if alert.last_seen else None,
                "source_ip": alert.source_ip,
                "destination_ip": alert.destination_ip,
                "ap_id": alert.ap_id,
                "event_count": alert.event_count,
                "simulated": alert.simulated,
            },
        }
        await ws_manager.broadcast(payload)


# Singleton
alert_manager = AlertManager()
