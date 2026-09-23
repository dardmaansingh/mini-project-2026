"""
Pipeline Service Singleton.

Academic Context (Systems Architecture):
- Maintains a thread-safe singleton instance of ConcurrencyPipelineManager.
- Bridges the asynchronous Producer-Consumer background worker pool with the Flask REST API.
"""

import threading
import time
from typing import Optional, Dict, Any
from processor.workers.worker_manager import ConcurrencyPipelineManager
from database.connection import DatabaseConnectionPool
from database.repositories.log_repository import LogRepository
from database.repositories.alert_repository import AlertRepository
from scripts.generate_test_logs import generate_zeek_conn_records


class InMemoryFallbackRepository:
    """Thread-safe fallback repository used when MySQL service is offline."""

    def __init__(self):
        self._lock = threading.Lock()
        self.logs = []
        self.alerts = []

    def insert_log(self, event: Dict[str, Any]):
        with self._lock:
            self.logs.append(event)
            if len(self.logs) > 1000:
                self.logs.pop(0)

    def insert_alert(self, alert: Dict[str, Any]):
        with self._lock:
            self.alerts.append(alert)
            if len(self.alerts) > 500:
                self.alerts.pop(0)

    def get_recent_logs(self, limit: int = 50):
        with self._lock:
            return list(reversed(self.logs[-limit:]))

    def get_recent_alerts(self, limit: int = 50, severity: Optional[str] = None):
        with self._lock:
            records = self.alerts
            if severity:
                records = [a for a in records if a.get("severity") == severity.upper()]
            return list(reversed(records[-limit:]))

    def get_top_source_ips(self, limit: int = 10):
        with self._lock:
            counts = {}
            for item in self.logs:
                ip = item.get("source_ip", "unknown")
                counts[ip] = counts.get(ip, 0) + 1
            sorted_ips = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            return [{"source_ip": ip, "connection_count": cnt} for ip, cnt in sorted_ips]

    def get_protocol_distribution(self):
        with self._lock:
            counts = {}
            for item in self.logs:
                proto = str(item.get("protocol", "unknown")).lower()
                counts[proto] = counts.get(proto, 0) + 1
            return [{"protocol": proto, "count": cnt} for proto, cnt in counts.items()]

    def get_traffic_summary(self):
        with self._lock:
            total_conns = len(self.logs)
            total_bytes = sum(int(l.get("orig_bytes", 0)) + int(l.get("resp_bytes", 0)) for l in self.logs)
            avg_dur = sum(float(l.get("duration", 0.0)) for l in self.logs) / total_conns if total_conns > 0 else 0.0
            return {
                "total_connections": total_conns,
                "total_bytes": total_bytes,
                "avg_duration": round(avg_dur, 4),
            }

    def get_severity_counts(self):
        with self._lock:
            counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            for a in self.alerts:
                sev = a.get("severity", "LOW")
                if sev in counts:
                    counts[sev] += 1
            return counts


class PipelineService:
    """Manages the live background pipeline and data source."""

    _instance: Optional["PipelineService"] = None
    _init_lock = threading.Lock()

    def __init__(self):
        self.db_available, self.db_status_message = DatabaseConnectionPool.check_database_availability()

        if self.db_available:
            self.log_repo = LogRepository()
            self.alert_repo = AlertRepository()
            active_repo = self.log_repo
        else:
            self.fallback_repo = InMemoryFallbackRepository()
            self.log_repo = self.fallback_repo
            self.alert_repo = self.fallback_repo
            active_repo = self.fallback_repo

        # Initialize manager with 256 buffer capacity and 4 worker threads
        self.manager = ConcurrencyPipelineManager(
            buffer_capacity=256,
            num_consumers=4,
            db_repository=active_repo,
        )
        self.manager.start()

    @classmethod
    def get_instance(cls) -> "PipelineService":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def inject_traffic_burst(self, count: int = 100) -> Dict[str, Any]:
        """Injects synthetic traffic burst for live viva demonstration."""
        records = generate_zeek_conn_records(count)
        start = time.perf_counter()
        enqueued = 0

        for r in records:
            if self.manager.buffer.enqueue(r, block=True, timeout=2.0):
                enqueued += 1

        duration = time.perf_counter() - start
        return {
            "requested_burst": count,
            "enqueued": enqueued,
            "injection_time_seconds": round(duration, 4),
            "buffer_metrics": self.manager.buffer.get_metrics(),
        }
