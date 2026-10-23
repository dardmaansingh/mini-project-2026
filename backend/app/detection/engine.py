"""
NetSentinel — Detection Engine.

Continuously evaluates normalized events against all enabled detection rules.
Emits alerts via the AlertManager when conditions are met.
"""

from __future__ import annotations
import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Callable, Awaitable

from backend.app.normalization.schema import NormalizedEvent
from backend.app.config import settings

logger = logging.getLogger(__name__)

AlertCallback = Callable[[dict], Awaitable[None]]


# ── Sliding-window counter ─────────────────────────────────────────────────

class SlidingWindow:
    """Time-bucketed sliding window for counting events per key."""

    def __init__(self, window_seconds: int):
        self.window = window_seconds
        # key -> deque of timestamps
        self._buckets: Dict[str, deque] = defaultdict(deque)

    def add(self, key: str, ts: Optional[datetime] = None) -> int:
        ts = ts or datetime.now(timezone.utc)
        q = self._buckets[key]
        q.append(ts)
        cutoff = ts - timedelta(seconds=self.window)
        while q and q[0] < cutoff:
            q.popleft()
        return len(q)

    def count(self, key: str) -> int:
        ts = datetime.now(timezone.utc)
        cutoff = ts - timedelta(seconds=self.window)
        q = self._buckets[key]
        while q and q[0] < cutoff:
            q.popleft()
        return len(q)

    def unique_values(self, key: str) -> set:
        """Used for port scan — track distinct ports per source."""
        return set()  # overridden in subclass

    def clear_stale(self) -> None:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window)
        for q in self._buckets.values():
            while q and q[0] < cutoff:
                q.popleft()


class MultiValueWindow:
    """Sliding window that tracks a set of distinct values per key."""

    def __init__(self, window_seconds: int):
        self.window = window_seconds
        # key -> deque of (timestamp, value) tuples
        self._data: Dict[str, deque] = defaultdict(deque)

    def add(self, key: str, value, ts: Optional[datetime] = None) -> set:
        ts = ts or datetime.now(timezone.utc)
        q = self._data[key]
        q.append((ts, value))
        cutoff = ts - timedelta(seconds=self.window)
        while q and q[0][0] < cutoff:
            q.popleft()
        return {v for _, v in q}

    def values(self, key: str) -> set:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window)
        q = self._data[key]
        while q and q[0][0] < cutoff:
            q.popleft()
        return {v for _, v in q}


# ── Cooldown tracker ───────────────────────────────────────────────────────

class CooldownTracker:
    def __init__(self):
        self._last_fire: Dict[str, datetime] = {}

    def can_fire(self, key: str, cooldown_seconds: int) -> bool:
        last = self._last_fire.get(key)
        if last is None:
            return True
        return (datetime.now(timezone.utc) - last).total_seconds() >= cooldown_seconds

    def mark_fired(self, key: str) -> None:
        self._last_fire[key] = datetime.now(timezone.utc)


# ── Detection Engine ───────────────────────────────────────────────────────

class DetectionEngine:
    """
    Stateful rule evaluation engine.
    Feed events via process_event(); fire callback on detection.
    """

    def __init__(self, on_alert: AlertCallback, cfg=None):
        self._on_alert = on_alert
        self._cfg = cfg or settings
        self._cooldown = CooldownTracker()

        # Rule-specific state
        self._dns_window = SlidingWindow(self._cfg.detection_window_seconds)
        self._dns_domain_window = MultiValueWindow(self._cfg.detection_window_seconds)

        self._port_window = MultiValueWindow(self._cfg.detection_window_seconds)
        self._dst_ip_window = MultiValueWindow(self._cfg.detection_window_seconds)

        self._auth_fail_window = SlidingWindow(self._cfg.detection_window_seconds)
        self._auth_fail_multi = MultiValueWindow(self._cfg.detection_window_seconds)

        self._bytes_window: Dict[str, deque] = defaultdict(deque)  # src -> [(ts, bytes)]
        self._bytes_baseline: Dict[str, float] = {}

        # Rules enabled state (can be toggled at runtime)
        self._rules_enabled: Dict[str, bool] = {
            "RULE-001": True,
            "RULE-002": True,
            "RULE-003": True,
            "RULE-004": True,
            "RULE-005": True,
            "RULE-006": True,
            "RULE-007": True,
            "RULE-008": True,
            "RULE-009": True,
            "RULE-010": True,
        }

    def set_rule_enabled(self, rule_id: str, enabled: bool) -> None:
        self._rules_enabled[rule_id] = enabled

    async def process_event(self, event: NormalizedEvent) -> None:
        """Evaluate all enabled rules against this event."""
        tasks = []
        if self._rules_enabled.get("RULE-001"):
            tasks.append(self._rule_dns_anomaly(event))
        if self._rules_enabled.get("RULE-002"):
            tasks.append(self._rule_port_scan(event))
        if self._rules_enabled.get("RULE-003"):
            tasks.append(self._rule_auth_failure(event))
        if self._rules_enabled.get("RULE-004"):
            tasks.append(self._rule_bandwidth_anomaly(event))
        if self._rules_enabled.get("RULE-005"):
            tasks.append(self._rule_suspicious_outbound(event))
        if self._rules_enabled.get("RULE-007"):
            tasks.append(self._rule_dhcp_anomaly(event))
        if self._rules_enabled.get("RULE-009"):
            tasks.append(self._rule_infra_anomaly(event))

        await asyncio.gather(*tasks, return_exceptions=True)

    # ── Rule implementations ───────────────────────────────────────────────

    async def _rule_dns_anomaly(self, event: NormalizedEvent) -> None:
        if event.event_type != "dns_query" or not event.source_ip:
            return
        key = f"dns:{event.source_ip}"
        count = self._dns_window.add(event.source_ip, event.timestamp_utc)
        domains = self._dns_domain_window.add(event.source_ip, event.domain, event.timestamp_utc)

        if count >= self._cfg.dns_query_rate_threshold:
            cd_key = f"RULE-001:{event.source_ip}"
            if not self._cooldown.can_fire(cd_key, 300):
                return
            self._cooldown.mark_fired(cd_key)
            nxdomain = event.dns_response_code == "NXDOMAIN"
            await self._emit_alert({
                "rule_id": "RULE-001",
                "rule_name": "DNS Query Rate Anomaly",
                "title": f"High DNS query rate from {event.source_ip}",
                "description": (
                    f"Source {event.source_ip} sent {count} DNS queries in "
                    f"{self._cfg.detection_window_seconds}s (threshold: {self._cfg.dns_query_rate_threshold}). "
                    f"Unique domains: {len(domains)}."
                    + (" NXDOMAIN responses detected." if nxdomain else "")
                ),
                "severity": "high" if count > self._cfg.dns_query_rate_threshold * 2 else "medium",
                "confidence": "high",
                "source_ip": event.source_ip,
                "ap_id": event.ap_id,
                "vlan_id": event.vlan_id,
                "simulated": event.simulated,
                "evidence": {"query_count": count, "unique_domains": len(domains), "nxdomain": nxdomain},
                "recommended_steps": [
                    "Identify the device associated with this IP on the campus DHCP/asset inventory.",
                    "Review the queried domains for known-malicious patterns.",
                    "Check if the query burst coincides with software updates or legitimate bulk activity.",
                    "Consider blocking or rate-limiting if malicious domains are confirmed.",
                ],
            })

    async def _rule_port_scan(self, event: NormalizedEvent) -> None:
        if event.event_type not in ("connection",) or not event.source_ip or not event.destination_port:
            return
        ports = self._port_window.add(event.source_ip, event.destination_port, event.timestamp_utc)
        dsts = self._dst_ip_window.add(event.source_ip, event.destination_ip, event.timestamp_utc)

        if len(ports) >= self._cfg.port_scan_port_threshold:
            cd_key = f"RULE-002:{event.source_ip}"
            if not self._cooldown.can_fire(cd_key, 300):
                return
            self._cooldown.mark_fired(cd_key)
            await self._emit_alert({
                "rule_id": "RULE-002",
                "rule_name": "Port Scan Detected",
                "title": f"Possible port scan from {event.source_ip}",
                "description": (
                    f"Source {event.source_ip} contacted {len(ports)} distinct ports across "
                    f"{len(dsts)} destination IPs in {self._cfg.detection_window_seconds}s."
                ),
                "severity": "high",
                "confidence": "medium",
                "source_ip": event.source_ip,
                "simulated": event.simulated,
                "evidence": {"unique_ports": len(ports), "unique_destinations": len(dsts), "sample_ports": sorted(ports)[:20]},
                "recommended_steps": [
                    "Identify the source device and owner.",
                    "Check if an authorized vulnerability scan was scheduled.",
                    "If unauthorized, isolate the device and review for compromise.",
                ],
            })

    async def _rule_auth_failure(self, event: NormalizedEvent) -> None:
        if event.event_type != "auth_failure" or not event.source_ip:
            return
        src_key = event.source_ip
        count = self._auth_fail_window.add(src_key, event.timestamp_utc)
        accounts = self._auth_fail_multi.add(src_key, event.username, event.timestamp_utc)

        if count >= self._cfg.auth_failure_threshold:
            cd_key = f"RULE-003:{event.source_ip}"
            if not self._cooldown.can_fire(cd_key, 300):
                return
            self._cooldown.mark_fired(cd_key)
            is_spray = len(accounts) > 3
            await self._emit_alert({
                "rule_id": "RULE-003",
                "rule_name": "Repeated Authentication Failures",
                "title": f"{'Password spray' if is_spray else 'Brute force'} from {event.source_ip}",
                "description": (
                    f"Source {event.source_ip} had {count} authentication failures in "
                    f"{self._cfg.detection_window_seconds}s against {len(accounts)} account(s)."
                ),
                "severity": "high" if is_spray else "medium",
                "confidence": "high",
                "source_ip": event.source_ip,
                "simulated": event.simulated,
                "evidence": {"failure_count": count, "unique_accounts": len(accounts), "accounts": list(accounts)[:10]},
                "recommended_steps": [
                    "Lock the source IP at the firewall or access point temporarily.",
                    "Verify with the account owner whether the failures are expected.",
                    "Check authentication logs for a subsequent successful login.",
                ],
            })

    async def _rule_bandwidth_anomaly(self, event: NormalizedEvent) -> None:
        if event.event_type not in ("flow", "connection") or not event.source_ip:
            return
        if not event.bytes_sent:
            return
        src = event.source_ip
        now = event.timestamp_utc
        q = self._bytes_window[src]
        q.append((now, event.bytes_sent))
        cutoff = now - timedelta(seconds=self._cfg.detection_window_seconds)
        while q and q[0][0] < cutoff:
            q.popleft()
        total = sum(b for _, b in q)
        baseline = self._bytes_baseline.get(src, 0)

        # Update rolling baseline
        self._bytes_baseline[src] = (baseline * 0.9 + total * 0.1) if baseline > 0 else total

        threshold_bytes = 100_000_000  # 100 MB in window = anomaly
        if total > threshold_bytes and (baseline == 0 or total > baseline * self._cfg.bandwidth_anomaly_factor):
            cd_key = f"RULE-004:{src}"
            if not self._cooldown.can_fire(cd_key, 600):
                return
            self._cooldown.mark_fired(cd_key)
            await self._emit_alert({
                "rule_id": "RULE-004",
                "rule_name": "Bandwidth Anomaly",
                "title": f"Unusual data transfer from {src}",
                "description": (
                    f"Source {src} transferred {total / 1e6:.1f} MB in "
                    f"{self._cfg.detection_window_seconds}s "
                    f"(baseline: {baseline / 1e6:.1f} MB)."
                ),
                "severity": "medium",
                "confidence": "medium",
                "source_ip": src,
                "destination_ip": event.destination_ip,
                "simulated": event.simulated,
                "evidence": {"bytes_total": total, "baseline_bytes": baseline, "factor": self._cfg.bandwidth_anomaly_factor},
                "recommended_steps": [
                    "Identify whether this is a legitimate bulk transfer (backup, software update, media streaming).",
                    "Review destination IPs for data exfiltration indicators.",
                    "Correlate with user activity logs if available.",
                ],
            })

    async def _rule_suspicious_outbound(self, event: NormalizedEvent) -> None:
        if event.event_type not in ("connection", "dns_query"):
            return
        meta = event.extra_metadata or {}
        if meta.get("scenario") == "suspicious_outbound" or (
            event.domain and any(sus in (event.domain or "") for sus in ["malware", "botnet", "exfil", "c2", "dga"])
        ):
            cd_key = f"RULE-005:{event.source_ip}"
            if not self._cooldown.can_fire(cd_key, 600):
                return
            self._cooldown.mark_fired(cd_key)
            await self._emit_alert({
                "rule_id": "RULE-005",
                "rule_name": "Suspicious Outbound Communication",
                "title": f"Suspicious outbound from {event.source_ip}",
                "description": (
                    f"Source {event.source_ip} made a connection matching suspicious indicators. "
                    f"Destination: {event.destination_ip or event.domain}."
                ),
                "severity": "high",
                "confidence": "medium",
                "source_ip": event.source_ip,
                "destination_ip": event.destination_ip,
                "simulated": event.simulated,
                "evidence": {"domain": event.domain, "destination_ip": event.destination_ip, "port": event.destination_port},
                "recommended_steps": [
                    "Do not block automatically. Verify the connection context first.",
                    "Cross-reference destination with threat intelligence feeds.",
                    "Investigate the source device for signs of malware.",
                ],
            })

    async def _rule_dhcp_anomaly(self, event: NormalizedEvent) -> None:
        if event.event_type != "dhcp":
            return
        meta = event.extra_metadata or {}
        if meta.get("rogue_server") or meta.get("scenario") == "dhcp_anomaly":
            cd_key = f"RULE-007:{event.source_ip}"
            if not self._cooldown.can_fire(cd_key, 600):
                return
            self._cooldown.mark_fired(cd_key)
            await self._emit_alert({
                "rule_id": "RULE-007",
                "rule_name": "DHCP Anomaly",
                "title": f"Possible rogue DHCP activity from {event.source_ip}",
                "description": (
                    f"Unexpected DHCP server or anomalous lease activity detected from {event.source_ip}."
                ),
                "severity": "high",
                "confidence": "medium",
                "source_ip": event.source_ip,
                "vlan_id": event.vlan_id,
                "simulated": event.simulated,
                "evidence": {"mac": event.client_mac, "vlan": event.vlan_id},
                "recommended_steps": [
                    "Verify whether this is an authorized DHCP server.",
                    "Enable DHCP snooping on the relevant switch if not already configured.",
                    "Locate and disconnect the rogue device if unauthorized.",
                ],
            })

    async def _rule_infra_anomaly(self, event: NormalizedEvent) -> None:
        if event.event_type not in ("ap_event", "switch_event"):
            return
        meta = event.extra_metadata or {}
        scenario = meta.get("scenario", "")
        if scenario in ("ap_disconnect", "switch_port_flap"):
            device = event.ap_id or event.switch_id or event.source_ip
            cd_key = f"RULE-009:{device}"
            if not self._cooldown.can_fire(cd_key, 120):
                return
            self._cooldown.mark_fired(cd_key)
            await self._emit_alert({
                "rule_id": "RULE-009",
                "rule_name": "Network Infrastructure Anomaly",
                "title": f"Infrastructure event: {scenario.replace('_', ' ').title()} on {device}",
                "description": (
                    f"Network infrastructure anomaly detected: {scenario} on device {device}."
                ),
                "severity": "low" if scenario == "switch_port_flap" else "medium",
                "confidence": "high",
                "source_ip": event.source_ip,
                "ap_id": event.ap_id,
                "switch_id": event.switch_id,
                "switch_port": event.switch_port,
                "simulated": event.simulated,
                "evidence": {"scenario": scenario, "metadata": meta},
                "recommended_steps": [
                    "Check whether a physical layer issue (cable, SFP) is causing the event.",
                    "Review controller logs for the affected AP or switch.",
                    "Distinguish infrastructure failure from a security-related disconnection.",
                ],
            })

    # ── Helpers ────────────────────────────────────────────────────────────

    async def _emit_alert(self, alert_data: dict) -> None:
        alert_data.setdefault("first_seen", datetime.now(timezone.utc).isoformat())
        alert_data.setdefault("last_seen", datetime.now(timezone.utc).isoformat())
        try:
            await self._on_alert(alert_data)
        except Exception as exc:
            logger.error("Alert emission error: %s", exc, exc_info=True)
