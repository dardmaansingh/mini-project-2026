"""
Alert Manager and Dispatch Engine.

Central hub for collecting, deduplicating, scoring, storing, and dispatching alerts
originating from the detection layers (Rules, KMP, Regex, Decision Tree).
"""

import time
import uuid
from typing import Dict, List, Any, Optional
from alerting.webhook import WebhookDispatcher
from alerting.severity import AlertSeverity


class AlertManager:
    """
    Manages security alert lifecycle, deduplication, and notification dispatch.
    """

    def __init__(
        self,
        webhook_dispatcher: Optional[WebhookDispatcher] = None,
        dedup_window_seconds: float = 10.0,
        max_in_memory_alerts: int = 500,
    ):
        self.webhook = webhook_dispatcher or WebhookDispatcher(enabled=False)
        self.dedup_window_seconds = dedup_window_seconds
        self.max_in_memory_alerts = max_in_memory_alerts

        # In-memory storage for dashboard access before or alongside MySQL
        self.alerts: List[Dict[str, Any]] = []

        # Deduplication tracker: (source_ip, alert_type) -> last_alert_timestamp
        self._last_alerted: Dict[tuple, float] = {}

    def process_detection(
        self,
        alert_type: str,
        severity: str,
        source_ip: str,
        destination_ip: str,
        detection_method: str,
        description: str,
        evidence: Dict[str, Any],
        timestamp: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Deduplicates, persists, and dispatches a validated security finding.
        """
        ts = timestamp or time.time()
        dedup_key = (source_ip, alert_type)

        # Deduplication check
        last_ts = self._last_alerted.get(dedup_key, 0.0)
        if (ts - last_ts) < self.dedup_window_seconds:
            # Suppress flood of duplicate alerts for same IP + condition
            return None

        self._last_alerted[dedup_key] = ts

        alert_record = {
            "alert_id": f"ALT-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": ts,
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "alert_type": alert_type,
            "severity": AlertSeverity.from_string(severity).value,
            "detection_method": detection_method,
            "description": description,
            "evidence": evidence,
            "status": "OPEN",
        }

        # Store in circular in-memory buffer
        self.alerts.append(alert_record)
        if len(self.alerts) > self.max_in_memory_alerts:
            self.alerts.pop(0)

        # Trigger HTTP Webhook dispatch
        if self.webhook.enabled:
            self.webhook.dispatch(alert_record)

        return alert_record

    def get_recent_alerts(self, limit: int = 50, severity_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves recent alerts with optional severity filtering."""
        filtered = self.alerts
        if severity_filter:
            sev_upper = severity_filter.upper()
            filtered = [a for a in filtered if a["severity"] == sev_upper]

        return list(reversed(filtered[-limit:]))

    def get_severity_counts(self) -> Dict[str, int]:
        """Calculates breakdown of alerts across severity levels."""
        counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for a in self.alerts:
            sev = a.get("severity", "LOW")
            if sev in counts:
                counts[sev] += 1
        return counts
