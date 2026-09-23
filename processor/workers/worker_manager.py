"""
Worker Manager & Concurrency Lifecycle Coordinator.

Academic Context (Operating Systems / Thread Pool Management):
- Coordinates the lifecycles of N consumer worker threads and producer processes.
- Supervises thread health, handles graceful pipeline drain and shutdown.
- Provides unified telemetry across queue, concurrency, and detection subsystems.
"""

import time
from typing import List, Dict, Any, Optional
from processor.dsa.circular_buffer import CircularBuffer
from processor.workers.producer import ProducerWorker
from processor.workers.consumer import ConsumerWorker
from detection.rules.rule_engine import StatefulRuleEngine
from detection.patterns.regex_patterns import RegexPatternDetector
from detection.ml.decision_tree import DecisionTreeDetector
from alerting.alert_manager import AlertManager


class ConcurrencyPipelineManager:
    """
    Supervises the multi-threaded Producer-Consumer network log processing pipeline.
    """

    def __init__(
        self,
        buffer_capacity: int = 256,
        num_consumers: int = 4,
        rule_engine: Optional[StatefulRuleEngine] = None,
        regex_detector: Optional[RegexPatternDetector] = None,
        ml_detector: Optional[DecisionTreeDetector] = None,
        alert_manager: Optional[AlertManager] = None,
        db_repository: Optional[Any] = None,
    ):
        self.buffer = CircularBuffer(capacity=buffer_capacity)
        self.num_consumers = num_consumers

        self.rule_engine = rule_engine or StatefulRuleEngine()
        self.regex_detector = regex_detector or RegexPatternDetector()
        self.ml_detector = ml_detector or DecisionTreeDetector()
        self.alert_manager = alert_manager or AlertManager()
        self.db_repository = db_repository

        self.producer: Optional[ProducerWorker] = None
        self.consumers: List[ConsumerWorker] = []
        self.is_active = False

    def start(self, producer: Optional[ProducerWorker] = None):
        """Starts worker threads."""
        self.is_active = True
        self.consumers = []

        # Initialize and launch consumer thread pool
        for i in range(self.num_consumers):
            consumer = ConsumerWorker(
                worker_id=i + 1,
                buffer=self.buffer,
                rule_engine=self.rule_engine,
                regex_detector=self.regex_detector,
                ml_detector=self.ml_detector,
                alert_manager=self.alert_manager,
                db_repository=self.db_repository,
                dequeue_timeout=0.5,
            )
            consumer.start()
            self.consumers.append(consumer)

        # Launch producer if supplied
        if producer:
            self.producer = producer
            self.producer.start()

    def wait_until_drained(self, timeout: float = 10.0) -> bool:
        """Blocks until circular buffer is empty and all items are processed."""
        start_time = time.time()
        while self.buffer.get_size() > 0:
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.05)
        # Allow brief moment for consumers to complete in-flight items
        time.sleep(0.1)
        return True

    def stop(self, timeout: float = 5.0):
        """Gracefully halts all producer and consumer threads."""
        self.is_active = False

        if self.producer and self.producer.is_alive():
            self.producer.stop()
            self.producer.join(timeout=timeout)

        # Notify consumers to stop
        for consumer in self.consumers:
            consumer.stop()

        # Send stop sentinels to unblock any waiting consumer semaphores
        for _ in range(len(self.consumers)):
            self.buffer.enqueue(False, block=False)

        for consumer in self.consumers:
            if consumer.is_alive():
                consumer.join(timeout=timeout)

    def get_telemetry(self) -> Dict[str, Any]:
        """Provides holistic system snapshot across concurrency, buffer, and alerts."""
        buffer_metrics = self.buffer.get_metrics()
        total_consumed = sum(c.items_consumed for c in self.consumers)
        total_worker_alerts = sum(c.alerts_generated for c in self.consumers)

        return {
            "pipeline_active": self.is_active,
            "consumer_count": len(self.consumers),
            "buffer": buffer_metrics,
            "total_events_consumed": total_consumed,
            "total_alerts_generated": total_worker_alerts,
            "severity_distribution": self.alert_manager.get_severity_counts(),
        }
