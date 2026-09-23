"""
Pipeline Runner CLI Script.

Executes the end-to-end network log ingestion, circular buffering,
multi-threaded analysis, and alerting pipeline.
"""

import sys
import os
import time
import argparse
from processor.readers.zeek_reader import ZeekReader
from processor.workers.producer import ProducerWorker
from processor.workers.worker_manager import ConcurrencyPipelineManager
from database.connection import DatabaseConnectionPool
from database.repositories.log_repository import LogRepository
from database.repositories.alert_repository import AlertRepository


def run_pipeline(log_file: str, continuous: bool = False, buffer_size: int = 256, workers: int = 4):
    print("=" * 65)
    print(" Wireless Network Traffic Monitor Using Zeek (Mini Project 2026)")
    print("=" * 65)

    # Step 1: Database Diagnostic Check
    db_available, db_msg = DatabaseConnectionPool.check_database_availability()
    print(f"[*] Database Status: {'CONNECTED' if db_available else 'OFFLINE / PENDING'}")
    print(f"    Details: {db_msg}")

    db_repo = None
    if db_available:
        print("[+] Attaching MySQL repository persistence layer...")
        db_repo = LogRepository()

    # Step 2: Initialize Concurrency Pipeline
    print(f"[*] Initializing Circular Buffer (Capacity: {buffer_size}) & {workers} Consumer Workers...")
    manager = ConcurrencyPipelineManager(
        buffer_capacity=buffer_size,
        num_consumers=workers,
        db_repository=db_repo,
    )
    manager.start()

    # Step 3: Start Ingestion
    reader = ZeekReader()
    if continuous:
        print(f"[*] Streaming live newly appended lines from: {log_file} (Press Ctrl+C to stop)...")
        try:
            for record in reader.stream_file(log_file):
                manager.buffer.enqueue(record, block=True, timeout=2.0)
                sys.stdout.write(f"\r[+] Events Ingested: {manager.buffer.total_enqueued} | Queue Size: {manager.buffer.get_size()}")
                sys.stdout.flush()
        except KeyboardInterrupt:
            print("\n[*] Stopping pipeline...")
    else:
        print(f"[*] Reading batch log file: {log_file}...")
        records = reader.read_file(log_file)
        print(f"[+] Loaded {len(records)} records. Ingesting into Circular Buffer...")
        for r in records:
            manager.buffer.enqueue(r, block=True, timeout=5.0)

        # Wait for drain
        print("[*] Processing events across worker pool...")
        manager.wait_until_drained(timeout=10.0)

    # Step 4: Summary Telemetry
    telemetry = manager.get_telemetry()
    manager.stop()

    print("\n" + "=" * 65)
    print(" Pipeline Execution Summary")
    print("=" * 65)
    print(f"Total Events Consumed:    {telemetry['total_events_consumed']}")
    print(f"Total Alerts Flagged:     {telemetry['total_alerts_generated']}")
    print(f"Severity Breakdown:       {telemetry['severity_distribution']}")
    print(f"Buffer High Water Mark:   {telemetry['buffer']['high_water_mark']} / {buffer_size}")
    print(f"Buffer Dropped Items:     {telemetry['buffer']['dropped_count']}")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Zeek Log Processing Pipeline")
    parser.add_argument("--file", type=str, default="logs/sample/conn.log", help="Path to Zeek log file")
    parser.add_argument("--continuous", action="store_true", help="Continuously tail file")
    parser.add_argument("--buffer", type=int, default=256, help="Circular buffer capacity")
    parser.add_argument("--workers", type=int, default=4, help="Number of consumer threads")

    args = parser.parse_args()
    run_pipeline(args.file, continuous=args.continuous, buffer_size=args.buffer, workers=args.workers)
