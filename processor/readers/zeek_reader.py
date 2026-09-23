"""
Zeek Log Reader.

Coordinates with FileMonitor and ZeekParser to read log streams or static batch files,
emitting structured event dictionaries for the concurrency pipeline.
"""

import os
from typing import Generator, List, Dict, Any, Optional
from processor.parser.zeek_parser import ZeekParser
from processor.readers.file_monitor import FileMonitor


class ZeekReader:
    """
    High-level reader providing both batch-file reading and continuous streaming.
    """

    def __init__(self, parser: Optional[ZeekParser] = None):
        self.parser = parser or ZeekParser()

    def read_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Reads an entire Zeek log file statically from start to finish.
        Used for benchmarks, batch testing, and unit tests.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Log file not found: {file_path}")

        records = []
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                record = self.parser.parse_line(line)
                if record:
                    records.append(record)
        return records

    def stream_file(self, file_path: str, poll_interval: float = 0.1) -> Generator[Dict[str, Any], None, None]:
        """
        Streams newly appended Zeek log entries in real time.
        """
        monitor = FileMonitor(file_path, start_from_beginning=True, poll_interval=poll_interval)
        for raw_line in monitor.tail_lines():
            record = self.parser.parse_line(raw_line)
            if record:
                yield record
