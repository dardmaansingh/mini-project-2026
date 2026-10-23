"""
Zeek Log Parser Module.

Parses Zeek (formerly Bro) network monitoring logs (both standard TSV format
and JSON log format) into structured, strongly-typed Python dictionaries.
"""

import json
from typing import Dict, List, Optional, Any, Tuple


class ZeekParser:
    """
    Parser for Zeek connection (conn.log), HTTP (http.log), and DNS (dns.log) files.
    Maintains header state (#fields, #types, #separator) across lines in TSV mode.
    """

    # Mapping from Zeek's nested connection field names to normalized system keys
    FIELD_ALIASES = {
        "id.orig_h": "source_ip",
        "id.orig_p": "source_port",
        "id.resp_h": "destination_ip",
        "id.resp_p": "destination_port",
        "ts": "timestamp",
        "proto": "protocol",
    }

    def __init__(self):
        self.fields: List[str] = []
        self.types: List[str] = []
        self.separator: str = "\t"
        self.unset_field: str = "-"
        self.empty_field: str = "(empty)"
        self.parsed_count: int = 0
        self.error_count: int = 0

    def parse_header_line(self, line: str) -> bool:
        """
        Processes Zeek metadata headers (#separator, #fields, #types, etc.).
        Returns True if the line was a header line.
        """
        line = line.strip()
        if not line.startswith("#"):
            return False

        parts = line.split()
        if not parts:
            return True

        tag = parts[0]
        if tag == "#separator":
            # Example: #separator \x09
            if len(parts) > 1:
                sep_repr = parts[1]
                if sep_repr == r"\x09":
                    self.separator = "\t"
                elif sep_repr == r"\x20":
                    self.separator = " "
        elif tag == "#fields":
            self.fields = parts[1:]
        elif tag == "#types":
            self.types = parts[1:]
        elif tag == "#unset_field":
            if len(parts) > 1:
                self.unset_field = parts[1]
        elif tag == "#empty_field":
            if len(parts) > 1:
                self.empty_field = parts[1]

        return True

    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parses a single line of log text.
        Supports both Zeek TSV (when headers were supplied) and Zeek JSON.

        Returns:
            Optional[Dict[str, Any]]: Normalized dictionary of event attributes, or None if skipped/malformed.
        """
        line = line.strip()
        if not line:
            return None

        # Check for header comments
        if line.startswith("#"):
            self.parse_header_line(line)
            return None

        # Case 1: JSON formatted Zeek line
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                normalized = self._normalize_record(data)
                self.parsed_count += 1
                return normalized
            except Exception:
                self.error_count += 1
                return None

        # Case 2: TSV formatted Zeek line
        if not self.fields:
            # Fallback: assume default conn.log column headers if no header block was present
            self._set_default_conn_fields()

        values = line.split(self.separator)
        if len(values) != len(self.fields):
            # Incomplete or misaligned line
            self.error_count += 1
            return None

        raw_record = dict(zip(self.fields, values))
        normalized = self._normalize_record(raw_record)
        self.parsed_count += 1
        return normalized

    def _normalize_record(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes and type-casts Zeek fields into canonical application schema."""
        record: Dict[str, Any] = {}

        for k, v in raw.items():
            # Remap aliases
            clean_key = self.FIELD_ALIASES.get(k, k)
            record[clean_key] = v

        # Normalize timestamp
        ts_val = record.get("timestamp")
        try:
            record["timestamp"] = float(ts_val) if ts_val not in (None, self.unset_field, "") else 0.0
        except (ValueError, TypeError):
            record["timestamp"] = 0.0

        # Normalize ports
        for port_field in ("source_port", "destination_port"):
            val = record.get(port_field)
            try:
                record[port_field] = int(val) if val not in (None, self.unset_field, "") else 0
            except (ValueError, TypeError):
                record[port_field] = 0

        # Normalize numeric counters
        for count_field in ("orig_bytes", "resp_bytes", "orig_pkts", "resp_pkts"):
            val = record.get(count_field)
            try:
                record[count_field] = int(val) if val not in (None, self.unset_field, "") else 0
            except (ValueError, TypeError):
                record[count_field] = 0

        # Normalize duration
        dur_val = record.get("duration")
        try:
            record["duration"] = float(dur_val) if dur_val not in (None, self.unset_field, "") else 0.0
        except (ValueError, TypeError):
            record["duration"] = 0.0

        # String defaults
        record["source_ip"] = str(record.get("source_ip", "0.0.0.0"))
        record["destination_ip"] = str(record.get("destination_ip", "0.0.0.0"))
        record["protocol"] = str(record.get("protocol", "unknown")).lower()
        record["service"] = str(record.get("service", "-"))
        if record.get("destination_port") == 53 and record["service"] in ("-", "", "unknown"):
            record["service"] = "dns"
        record["conn_state"] = str(record.get("conn_state", "-"))
        record["history"] = str(record.get("history", "-"))
        record["uid"] = str(record.get("uid", "-"))
        if "query" in raw:
            record["query"] = str(raw["query"])

        return record

    def _set_default_conn_fields(self):
        """Sets standard Zeek 9.0 conn.log fields as fallback."""
        self.fields = [
            "ts", "uid", "id.orig_h", "id.orig_p", "id.resp_h", "id.resp_p",
            "proto", "service", "duration", "orig_bytes", "resp_bytes",
            "conn_state", "local_orig", "local_resp", "missed_bytes",
            "history", "orig_pkts", "orig_ip_bytes", "resp_pkts", "resp_ip_bytes", "tunnel_parents"
        ]
