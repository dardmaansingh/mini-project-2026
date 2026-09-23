"""
Unit Tests for Custom Circular Buffer.

Academic Verification (Data Structures & OS Concurrency):
- Verifies FIFO order.
- Verifies modulo pointer wrap-around.
- Verifies full and empty boundary assertions.
- Verifies high-water mark and dropped counts.
"""

import unittest
from processor.dsa.circular_buffer import (
    CircularBuffer,
    CircularBufferFullException,
    CircularBufferEmptyException,
)


class TestCircularBuffer(unittest.TestCase):

    def test_initial_state(self):
        cb = CircularBuffer(capacity=5)
        self.assertTrue(cb.is_empty())
        self.assertFalse(cb.is_full())
        self.assertEqual(cb.get_size(), 0)
        self.assertEqual(cb.capacity, 5)

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            CircularBuffer(capacity=0)
        with self.assertRaises(ValueError):
            CircularBuffer(capacity=-3)

    def test_enqueue_and_dequeue_fifo(self):
        cb = CircularBuffer(capacity=4)
        cb.enqueue("event_1")
        cb.enqueue("event_2")
        cb.enqueue("event_3")

        self.assertEqual(cb.get_size(), 3)
        self.assertEqual(cb.dequeue(), "event_1")
        self.assertEqual(cb.dequeue(), "event_2")
        self.assertEqual(cb.dequeue(), "event_3")
        self.assertTrue(cb.is_empty())

    def test_modulo_wrap_around(self):
        """
        Critical DSA Verification:
        Ensures tail and head pointers wrap around modulo capacity without array re-allocation.
        """
        cb = CircularBuffer(capacity=3)

        # Enqueue 3 items -> full
        cb.enqueue("A")
        cb.enqueue("B")
        cb.enqueue("C")
        self.assertTrue(cb.is_full())
        self.assertEqual(cb.tail, 0)  # (2 + 1) % 3 = 0

        # Dequeue 2 items -> 1 left
        self.assertEqual(cb.dequeue(), "A")
        self.assertEqual(cb.dequeue(), "B")
        self.assertEqual(cb.head, 2)

        # Enqueue 2 new items -> wraps around
        cb.enqueue("D")  # inserted at index 0, tail becomes 1
        cb.enqueue("E")  # inserted at index 1, tail becomes 2
        self.assertTrue(cb.is_full())

        # Dequeue all in exact FIFO sequence: C, D, E
        self.assertEqual(cb.dequeue(), "C")
        self.assertEqual(cb.dequeue(), "D")
        self.assertEqual(cb.dequeue(), "E")
        self.assertTrue(cb.is_empty())

    def test_non_blocking_exceptions(self):
        cb = CircularBuffer(capacity=2)
        cb.enqueue(1, block=False)
        cb.enqueue(2, block=False)

        with self.assertRaises(CircularBufferFullException):
            cb.enqueue(3, block=False)

        self.assertEqual(cb.dequeue(block=False), 1)
        self.assertEqual(cb.dequeue(block=False), 2)

        with self.assertRaises(CircularBufferEmptyException):
            cb.dequeue(block=False)

    def test_telemetry_metrics(self):
        cb = CircularBuffer(capacity=10)
        for i in range(7):
            cb.enqueue(f"item_{i}")
        for _ in range(3):
            cb.dequeue()

        metrics = cb.get_metrics()
        self.assertEqual(metrics["capacity"], 10)
        self.assertEqual(metrics["current_size"], 4)
        self.assertEqual(metrics["total_enqueued"], 7)
        self.assertEqual(metrics["total_dequeued"], 3)
        self.assertEqual(metrics["high_water_mark"], 7)


if __name__ == "__main__":
    unittest.main()
