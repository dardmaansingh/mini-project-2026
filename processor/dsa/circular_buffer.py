"""
Custom Circular Buffer / Circular Queue Implementation from Scratch.

Academic Context (Data Structures & Operating Systems):
- Fixed-capacity array with O(1) enqueue and dequeue operations.
- Modulo arithmetic for wrap-around pointer movement.
- Thread-safe coordination using Mutual Exclusion (Lock) and Counting Semaphores:
  1. Mutex (Lock): Guards the critical section modifying pointers and count.
  2. Empty Semaphore (initialized to capacity): Tracks available empty buffer slots.
  3. Full Semaphore (initialized to 0): Tracks available filled slots containing items.
- Avoids reliance on Python's built-in queue.Queue or collections.deque.
"""

import threading
import time
from typing import Any, Optional, Dict


class CircularBufferFullException(Exception):
    """Raised when an enqueue operation fails because the buffer is at maximum capacity."""
    pass


class CircularBufferEmptyException(Exception):
    """Raised when a dequeue operation fails because the buffer contains no items."""
    pass


class CircularBuffer:
    """
    Thread-Safe Circular Buffer implemented with fixed array and modulo arithmetic.

    Attributes:
        capacity (int): Maximum number of elements the buffer can hold.
        buffer (list): Fixed-size backing array.
        head (int): Read pointer (front of the queue).
        tail (int): Write pointer (rear of the queue).
        count (int): Current number of stored elements.
    """

    def __init__(self, capacity: int = 256):
        if capacity <= 0:
            raise ValueError(f"Buffer capacity must be a positive integer, got: {capacity}")

        self.capacity: int = capacity
        self.buffer: list = [None] * capacity
        self.head: int = 0
        self.tail: int = 0
        self.count: int = 0

        # Concurrency & Synchronization Primitives
        self._lock = threading.Lock()
        self._empty_slots = threading.Semaphore(capacity)
        self._filled_slots = threading.Semaphore(0)

        # Operational & Performance Telemetry
        self.total_enqueued: int = 0
        self.total_dequeued: int = 0
        self.high_water_mark: int = 0
        self.dropped_count: int = 0

    def is_empty(self) -> bool:
        """Returns True if the buffer currently contains zero elements."""
        with self._lock:
            return self.count == 0

    def is_full(self) -> bool:
        """Returns True if current count equals total capacity."""
        with self._lock:
            return self.count == self.capacity

    def get_size(self) -> int:
        """Returns the current number of items in the buffer."""
        with self._lock:
            return self.count

    def enqueue(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Inserts an item into the rear of the circular buffer.

        Algorithm:
        1. Acquire an empty-slot semaphore permit (blocking or with timeout).
        2. Acquire the mutex to enter the critical section.
        3. Place item at buffer[tail].
        4. Advance tail using modulo wrap-around: tail = (tail + 1) % capacity.
        5. Increment count and record metrics.
        6. Release mutex and signal the filled-slot semaphore.
        """
        # Step 1: Wait for an available empty slot
        acquired = self._empty_slots.acquire(blocking=block, timeout=timeout)
        if not acquired:
            with self._lock:
                self.dropped_count += 1
            if not block:
                raise CircularBufferFullException("Circular buffer is full (non-blocking call).")
            return False

        # Step 2: Critical Section
        with self._lock:
            self.buffer[self.tail] = item
            self.tail = (self.tail + 1) % self.capacity
            self.count += 1
            self.total_enqueued += 1
            if self.count > self.high_water_mark:
                self.high_water_mark = self.count

        # Step 3: Signal consumer that a new filled slot is ready
        self._filled_slots.release()
        return True

    def dequeue(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """
        Removes and returns the oldest item from the front of the circular buffer.

        Algorithm:
        1. Acquire a filled-slot semaphore permit (blocking or with timeout).
        2. Acquire the mutex to enter the critical section.
        3. Read item from buffer[head], and clear the slot reference.
        4. Advance head using modulo wrap-around: head = (head + 1) % capacity.
        5. Decrement count and record metrics.
        6. Release mutex and signal the empty-slot semaphore.
        """
        # Step 1: Wait for an available filled slot
        acquired = self._filled_slots.acquire(blocking=block, timeout=timeout)
        if not acquired:
            if not block:
                raise CircularBufferEmptyException("Circular buffer is empty (non-blocking call).")
            return None

        # Step 2: Critical Section
        with self._lock:
            item = self.buffer[self.head]
            self.buffer[self.head] = None  # Prevent memory leak / object retention
            self.head = (self.head + 1) % self.capacity
            self.count -= 1
            self.total_dequeued += 1

        # Step 3: Signal producer that an empty slot is now free
        self._empty_slots.release()
        return item

    def get_metrics(self) -> Dict[str, Any]:
        """Returns thread-safe snapshot of buffer state and utilization statistics."""
        with self._lock:
            return {
                "capacity": self.capacity,
                "current_size": self.count,
                "utilization_percent": round((self.count / self.capacity) * 100, 2),
                "head_pointer": self.head,
                "tail_pointer": self.tail,
                "total_enqueued": self.total_enqueued,
                "total_dequeued": self.total_dequeued,
                "high_water_mark": self.high_water_mark,
                "dropped_count": self.dropped_count,
            }

    def clear(self) -> None:
        """Resets the buffer to initial empty state. (Not recommended while active threads run)."""
        with self._lock:
            self.buffer = [None] * self.capacity
            self.head = 0
            self.tail = 0
            self.count = 0
            # Reset semaphores
            self._empty_slots = threading.Semaphore(self.capacity)
            self._filled_slots = threading.Semaphore(0)
