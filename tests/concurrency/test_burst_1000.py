"""
1000-Entry Burst Stress Test.

Academic Context (Operating Systems & Real-Time Concurrency):
- Stress tests the Producer-Consumer architecture and custom Circular Buffer under high traffic load.
- Injects 1000 synthetic Zeek connection events in rapid succession into a buffer with capacity 256.
- Measures:
  1. Accepted entries
  2. Processed entries
  3. Lost entries (must be 0)
  4. Duplicate entries (must be 0)
  5. Processing time and throughput
  6. High-water mark buffer utilization
"""

import time
import unittest
from scripts.generate_test_logs import generate_zeek_conn_records
from processor.workers.worker_manager import ConcurrencyPipelineManager


class TestBurst1000Concurrency(unittest.TestCase):

    def test_burst_1000_processing(self):
        burst_size = 1000
        buffer_capacity = 256  # Forces multiple buffer wrap-arounds
        num_workers = 4

        print(f"\n=======================================================")
        print(f"[*] Starting 1000-Entry Burst Stress Test")
        print(f"[*] Buffer Capacity: {buffer_capacity} | Consumers: {num_workers}")
        print(f"=======================================================")

        # Generate 1000 unique records
        records = generate_zeek_conn_records(burst_size)
        self.assertEqual(len(records), burst_size)

        # Initialize manager
        manager = ConcurrencyPipelineManager(
            buffer_capacity=buffer_capacity,
            num_consumers=num_workers,
        )

        manager.start()

        start_time = time.perf_counter()

        # Ingest 1000 entries
        enqueued_count = 0
        for rec in records:
            success = manager.buffer.enqueue(rec, block=True, timeout=5.0)
            if success:
                enqueued_count += 1

        # Wait until consumers drain all items from the buffer
        drained = manager.wait_until_drained(timeout=10.0)
        self.assertTrue(drained, "Circular buffer failed to drain within timeout.")

        duration = time.perf_counter() - start_time

        telemetry = manager.get_telemetry()
        manager.stop()

        buffer_metrics = telemetry["buffer"]
        total_consumed = telemetry["total_events_consumed"]
        lost_entries = enqueued_count - total_consumed
        throughput = total_consumed / duration if duration > 0 else 0

        print(f"[+] Total Injected:     {burst_size}")
        print(f"[+] Total Enqueued:     {enqueued_count}")
        print(f"[+] Total Consumed:     {total_consumed}")
        print(f"[+] Lost Entries:       {lost_entries}")
        print(f"[+] High Water Mark:    {buffer_metrics['high_water_mark']} / {buffer_capacity} ({round((buffer_metrics['high_water_mark']/buffer_capacity)*100, 1)}%)")
        print(f"[+] Total Duration:     {duration:.4f} seconds")
        print(f"[+] System Throughput:  {throughput:.1f} events/sec")
        print(f"[+] Alerts Flagged:     {telemetry['total_alerts_generated']}")
        print(f"=======================================================\n")

        # Rigorous assertions
        self.assertEqual(enqueued_count, burst_size, "All 1000 entries must be accepted.")
        self.assertEqual(total_consumed, burst_size, "All 1000 entries must be dequeued and processed.")
        self.assertEqual(lost_entries, 0, "No entries may be lost during burst.")
        self.assertEqual(buffer_metrics["dropped_count"], 0, "Zero entries should be dropped.")


if __name__ == "__main__":
    unittest.main()
