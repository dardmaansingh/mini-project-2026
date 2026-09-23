"""
Consumer Worker Thread.

Academic Context (Operating Systems / Multithreading):
- Consumer threads continuously dequeue events from the shared Circular Buffer.
- Synchronization: Waits on the buffer's filled-slot semaphore, acquires mutex, removes item, signals empty-slot semaphore.
- Executes the multi-tier detection pipeline (Rules, Regex, KMP, Decision Tree) concurrently.
"""

import threading
import time
from typing import Optional, Dict, Any
from processor.dsa.circular_buffer import CircularBuffer
from detection.rules.rule_engine import StatefulRuleEngine
from detection.patterns.regex_patterns import RegexPatternDetector
from detection.ml.decision_tree import DecisionTreeDetector
from alerting.alert_manager import AlertManager


class ConsumerWorker(threading.Thread):
    """
    Worker thread that dequeues events, evaluates detection stages, and dispatches alerts.
    """

    def __init__(
        self,
        worker_id: int,
        buffer: CircularBuffer,
        rule_engine: StatefulRuleEngine,
        regex_detector: RegexPatternDetector,
        ml_detector: DecisionTreeDetector,
        alert_manager: AlertManager,
        db_repository: Optional[Any] = None,
        dequeue_timeout: float = 1.0,
    ):
        super().__init__(name=f"Consumer-Worker-{worker_id}", daemon=True)
        self.worker_id = worker_id
        self.buffer = buffer
        self.rule_engine = rule_engine
        self.regex_detector = regex_detector
        self.ml_detector = ml_detector
        self.alert_manager = alert_manager
        self.db_repository = db_repository
        self.dequeue_timeout = dequeue_timeout

        self.is_running = False
        self.items_consumed = 0
        self.alerts_generated = 0

    def run(self):
        """Main consumer loop."""
        self.is_running = True

        while self.is_running:
            event = self.buffer.dequeue(block=True, timeout=self.dequeue_timeout)
            if event is None:
                continue

            # Poison pill / sentinel for shutdown
            if event is False or event == "__STOP__":
                break

            self.process_event(event)
            self.items_consumed += 1

        self.is_running = False

    def process_event(self, event: Dict[str, Any]):
        """Runs an individual network event through the full detection pipeline."""
        src_ip = event.get("source_ip", "0.0.0.0")
        dst_ip = event.get("destination_ip", "0.0.0.0")
        ts = event.get("timestamp", time.time())

        # Stage 1: Stateful Rules & KMP Search
        rule_detections = self.rule_engine.evaluate_event(event)
        for det in rule_detections:
            alert = self.alert_manager.process_detection(
                alert_type=det.alert_type,
                severity=det.severity,
                source_ip=det.source_ip,
                destination_ip=det.destination_ip,
                detection_method=det.detection_method,
                description=det.description,
                evidence=det.evidence,
                timestamp=det.timestamp,
            )
            if alert:
                self.alerts_generated += 1
                if self.db_repository:
                    self._persist_alert_safely(alert)

        # Stage 2: Regex Automata Signatures
        regex_matches = self.regex_detector.evaluate_event(event)
        for match in regex_matches:
            alert = self.alert_manager.process_detection(
                alert_type=f"REGEX_{match.pattern_name}",
                severity=match.severity,
                source_ip=src_ip,
                destination_ip=dst_ip,
                detection_method="REGEX",
                description=match.description,
                evidence=match.to_dict(),
                timestamp=ts,
            )
            if alert:
                self.alerts_generated += 1
                if self.db_repository:
                    self._persist_alert_safely(alert)

        # Stage 3: Decision Tree ML Classification
        ml_result = self.ml_detector.classify_event(event)
        if ml_result.get("is_suspicious"):
            alert = self.alert_manager.process_detection(
                alert_type=f"ML_{ml_result.get('class_label')}",
                severity="HIGH",
                source_ip=src_ip,
                destination_ip=dst_ip,
                detection_method="DECISION_TREE",
                description=f"Decision tree classified connection as suspicious (confidence {ml_result.get('confidence')}).",
                evidence=ml_result,
                timestamp=ts,
            )
            if alert:
                self.alerts_generated += 1
                if self.db_repository:
                    self._persist_alert_safely(alert)

        # Persist raw network log entry if DB repository is available
        if self.db_repository:
            try:
                self.db_repository.insert_log(event)
            except Exception:
                pass  # DB errors caught gracefully

    def _persist_alert_safely(self, alert: Dict[str, Any]):
        """Persists alert record into MySQL repository without failing worker thread."""
        try:
            self.db_repository.insert_alert(alert)
        except Exception:
            pass

    def stop(self):
        """Signals worker to terminate."""
        self.is_running = False
