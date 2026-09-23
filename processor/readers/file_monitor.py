"""
File Monitor and Live Log Tailer.

Monitors active log files on disk, detects newly appended lines,
tracks byte offsets to prevent duplicate reading, and handles file truncation.
"""

import os
import time
from typing import Generator, Optional


class FileMonitor:
    """
    Non-blocking / poll-based file follower that reads new lines as they are appended.
    Remembers offset to maintain exactly-once ingestion semantics.
    """

    def __init__(self, file_path: str, start_from_beginning: bool = True, poll_interval: float = 0.1):
        self.file_path: str = file_path
        self.start_from_beginning: bool = start_from_beginning
        self.poll_interval: float = poll_interval
        self.last_offset: int = 0
        self.is_running: bool = False

    def tail_lines(self) -> Generator[str, None, None]:
        """
        Continuously yields newly appended lines from the file until stopped.
        Handles file creation delay and file truncation/rotation.
        """
        self.is_running = True

        # Wait for file to exist
        while self.is_running and not os.path.exists(self.file_path):
            time.sleep(self.poll_interval)

        if not self.is_running:
            return

        with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
            if not self.start_from_beginning:
                f.seek(0, os.SEEK_END)
            self.last_offset = f.tell()

            while self.is_running:
                current_size = os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0

                # Detect file rotation or truncation (size shrunk)
                if current_size < self.last_offset:
                    f.seek(0, os.SEEK_SET)
                    self.last_offset = 0

                line = f.readline()
                if line:
                    self.last_offset = f.tell()
                    yield line
                else:
                    time.sleep(self.poll_interval)

    def stop(self):
        """Signals the follower loop to terminate gracefully."""
        self.is_running = False
