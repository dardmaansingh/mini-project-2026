"""
Rule Engine and Stateful Anomaly Detection.

Academic Context (Detection Systems & Stateful Automata):
- Maintains sliding-window state per source IP to detect distributed and multi-stage behaviors
  such as vertical port scans and SYN flood brute-forcing.
- Configurable deterministic thresholds without hardcoded magic numbers.
- KMP string search integration for targeted signature matching.
"""

import time
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple
from processor.dsa.kmp import kmp_search


class SuspiciousEvent:
    """Represents a validated detection finding with full evidence payload."""

    def __init__(
        self,
        alert_type: str,
        severity: str,
        source_ip: str,
        destination_ip: str,
        detection_method: str,
        description: str,
        evidence: Dict[str, Any],
        timestamp: float,
    ):
        self.alert_type = alert_type
        self.severity = severity  # LOW, MEDIUM, HIGH, CRITICAL
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.detection_method = detection_method  # RULE, KMP, REGEX, DECISION_TREE
        self.description = description
        self.evidence = evidence
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "detection_method": self.detection_method,
            "description": self.description,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
        }


class StatefulRuleEngine:
    """
    Evaluates network events against deterministic thresholds and sliding-window history.
    """

    def __init__(
        self,
        port_scan_threshold: int = 15,
        failed_conn_threshold: int = 10,
        time_window_seconds: float = 60.0,
        exfiltration_byte_threshold: int = 10_000_000,
    ):
        self.port_scan_threshold = port_scan_threshold
        self.failed_conn_threshold = failed_conn_threshold
        self.time_window_seconds = time_window_seconds
        self.exfiltration_byte_threshold = exfiltration_byte_threshold

        # Sliding Window State Tracking: source_ip -> list of (timestamp, dest_port, conn_state)
        self.ip_history: Dict[str, List[Tuple[float, int, str]]] = defaultdict(list)

        # High-Risk Signatures searched via KMP
        self.kmp_signatures = [
            ("PASSWD_FILE_ACCESS", "etc/passwd", "HIGH"),
            ("SHADOW_FILE_ACCESS", "etc/shadow", "CRITICAL"),
            ("PHP_WEBSHELL_EVAL", "eval(", "CRITICAL"),
            ("COMMAND_INJECTION_SH", "/bin/sh", "CRITICAL"),
            ("XSS_PROBE", "<script>", "HIGH"),
            ("CONFIG_PROBE", ".git/config", "HIGH"),
        ]

    def _purge_old_records(self, source_ip: str, current_time: float):
        """Removes historical state outside the sliding time window."""
        cutoff = current_time - self.time_window_seconds
        self.ip_history[source_ip] = [
            record for record in self.ip_history[source_ip] if record[0] >= cutoff
        ]

    def evaluate_event(self, event: Dict[str, Any]) -> List[SuspiciousEvent]:
        """
        Processes an event against all active rules and returns any triggered detections.
        """
        detections: List[SuspiciousEvent] = []
        source_ip = event.get("source_ip", "0.0.0.0")
        dest_ip = event.get("destination_ip", "0.0.0.0")
        dest_port = event.get("destination_port", 0)
        conn_state = event.get("conn_state", "-")
        ts = event.get("timestamp", time.time())
        if ts <= 0:
            ts = time.time()

        # Update sliding history
        self._purge_old_records(source_ip, ts)
        self.ip_history[source_ip].append((ts, dest_port, conn_state))
        history = self.ip_history[source_ip]

        # -------------------------------------------------------------
        # Rule 1: Port Scan Detection
        # Multiple distinct destination ports probed by single IP
        # -------------------------------------------------------------
        distinct_ports = {rec[1] for rec in history if rec[1] > 0}
        if len(distinct_ports) >= self.port_scan_threshold:
            detections.append(
                SuspiciousEvent(
                    alert_type="PORT_SCAN_DETECTED",
                    severity="HIGH",
                    source_ip=source_ip,
                    destination_ip=dest_ip,
                    detection_method="RULE",
                    description=f"Host probed {len(distinct_ports)} distinct ports within {self.time_window_seconds}s window.",
                    evidence={
                        "distinct_port_count": len(distinct_ports),
                        "ports_sampled": list(distinct_ports)[:10],
                        "threshold": self.port_scan_threshold,
                    },
                    timestamp=ts,
                )
            )

        # -------------------------------------------------------------
        # Rule 2: Failed Connection / SYN Flood / Denial of Service
        # Rapid accumulation of incomplete/rejected connection states
        # -------------------------------------------------------------
        failed_states = {"S0", "REJ", "RSTO", "RSTOS0"}
        failed_count = sum(1 for rec in history if rec[2] in failed_states)
        if failed_count >= self.failed_conn_threshold:
            detections.append(
                SuspiciousEvent(
                    alert_type="FAILED_CONNECTION_FLOOD",
                    severity="HIGH",
                    source_ip=source_ip,
                    destination_ip=dest_ip,
                    detection_method="RULE",
                    description=f"Host accumulated {failed_count} failed connections (SYN without ACK / Rejected) within window.",
                    evidence={
                        "failed_count": failed_count,
                        "threshold": self.failed_conn_threshold,
                        "latest_conn_state": conn_state,
                    },
                    timestamp=ts,
                )
            )

        # -------------------------------------------------------------
        # Rule 3: Data Exfiltration / Transfer Anomaly
        # Abnormally large data volume transferred in single connection
        # -------------------------------------------------------------
        orig_bytes = event.get("orig_bytes", 0)
        resp_bytes = event.get("resp_bytes", 0)
        if orig_bytes > self.exfiltration_byte_threshold or resp_bytes > self.exfiltration_byte_threshold:
            detections.append(
                SuspiciousEvent(
                    alert_type="LARGE_DATA_TRANSFER_ANOMALY",
                    severity="MEDIUM",
                    source_ip=source_ip,
                    destination_ip=dest_ip,
                    detection_method="RULE",
                    description=f"Data transfer volume exceeded threshold of {self.exfiltration_byte_threshold} bytes.",
                    evidence={
                        "orig_bytes": orig_bytes,
                        "resp_bytes": resp_bytes,
                        "threshold": self.exfiltration_byte_threshold,
                    },
                    timestamp=ts,
                )
            )

        # -------------------------------------------------------------
        # Rule 4: KMP Substring Pattern Search
        # O(N+M) exact matching across URI, service, and connection history
        # -------------------------------------------------------------
        text_corpus = f"{event.get('service', '')} {event.get('history', '')} {event.get('uri', '')}"
        for sig_name, pattern, severity in self.kmp_signatures:
            matches = kmp_search(text_corpus, pattern, case_sensitive=False)
            if matches:
                detections.append(
                    SuspiciousEvent(
                        alert_type=f"KMP_{sig_name}",
                        severity=severity,
                        source_ip=source_ip,
                        destination_ip=dest_ip,
                        detection_method="KMP",
                        description=f"KMP string matcher detected signature '{pattern}' at index {matches[0]}.",
                        evidence={
                            "matched_pattern": pattern,
                            "match_positions": matches,
                            "inspected_corpus": text_corpus[:100],
                        },
                        timestamp=ts,
                    )
                )

        return detections
