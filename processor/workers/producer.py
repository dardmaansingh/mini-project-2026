"""
Producer Worker Thread.

Academic Context (Operating Systems):
- The Producer thread ingests parsed Zeek log events and places them into the shared Circular Buffer.
- Synchronization: Waits on the buffer's empty-slot semaphore, acquires mutex, inserts event, signals full-slot semaphore.
"""

import threading
import time
from typing import Iterable, Dict, Any, Optional
from processor.dsa.circular_buffer import CircularBuffer


class ProducerWorker(threading.Thread):
    """
    Producer thread that pulls structured log events from an iterable/stream
    and pushes them into the shared Circular Buffer.
    """

    def __init__(
        self,
        buffer: CircularBuffer,
        event_stream: Optional[Iterable[Dict[str, Any]]] = None,
        name: str = "Producer-Thread",
        enqueue_timeout: float = 2.0,
    ):
        super().__init__(name=name, daemon=True)
        self.buffer = buffer
        self.event_stream = event_stream
        self.enqueue_timeout = enqueue_timeout
        self.is_running = False
        self.items_produced = 0
        self.items_dropped = 0

    def run(self):
        """Main producer execution loop."""
        self.is_running = True
        if self.event_stream is None:
            return

        for event in self.event_stream:
            if not self.is_running:
                break

            success = self.buffer.enqueue(event, block=True, timeout=self.enqueue_timeout)
            if success:
                self.items_produced += 1
            else:
                self.items_dropped += 1

        self.is_running = False

    def enqueue_direct(self, event: Dict[str, Any], block: bool = True, timeout: Optional[float] = None) -> bool:
        """Enqueues an event directly (used for programmatic burst injection)."""
        success = self.buffer.enqueue(event, block=block, timeout=timeout or self.enqueue_timeout)
        if success:
            self.items_produced += 1
        else:
            self.items_dropped += 1
        return success

    def stop(self):
        """Signals producer to halt execution."""
        self.is_running = False
