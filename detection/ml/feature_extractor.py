"""
Feature Extractor for Machine Learning Classification.

Transforms raw Zeek event dictionaries into normalized numerical feature vectors
suitable for Decision Tree training and inference.
"""

from typing import Dict, Any, List


class NetworkFeatureExtractor:
    """
    Extracts consistent feature vectors from Zeek conn.log records.

    Feature Vector Specification (Length: 10):
    [0] duration: Connection duration (seconds)
    [1] orig_bytes: Bytes sent by originator
    [2] resp_bytes: Bytes sent by responder
    [3] proto_tcp: 1 if protocol is TCP, else 0
    [4] proto_udp: 1 if protocol is UDP, else 0
    [5] proto_other: 1 if protocol is ICMP/other, else 0
    [6] conn_state_failed: 1 if conn_state indicates SYN-no-ACK or rejection (S0, REJ, RSTO), else 0
    [7] dest_port_privileged: 1 if destination port < 1024, else 0
    [8] orig_pkts: Number of packets sent by originator
    [9] resp_pkts: Number of packets sent by responder
    """

    FEATURE_NAMES = [
        "duration",
        "orig_bytes",
        "resp_bytes",
        "proto_tcp",
        "proto_udp",
        "proto_other",
        "conn_state_failed",
        "dest_port_privileged",
        "orig_pkts",
        "resp_pkts",
    ]

    FAILED_CONN_STATES = {"S0", "REJ", "RSTO", "RSTOS0"}

    @classmethod
    def extract_features(cls, event: Dict[str, Any]) -> List[float]:
        """Converts an event dictionary into a 10-dimensional numeric vector."""
        duration = float(event.get("duration", 0.0) or 0.0)
        orig_bytes = float(event.get("orig_bytes", 0) or 0)
        resp_bytes = float(event.get("resp_bytes", 0) or 0)

        proto = str(event.get("protocol", "")).lower()
        proto_tcp = 1.0 if proto == "tcp" else 0.0
        proto_udp = 1.0 if proto == "udp" else 0.0
        proto_other = 1.0 if proto not in ("tcp", "udp") else 0.0

        conn_state = str(event.get("conn_state", "")).upper()
        conn_state_failed = 1.0 if conn_state in cls.FAILED_CONN_STATES else 0.0

        dest_port = int(event.get("destination_port", 0) or 0)
        dest_port_privileged = 1.0 if 0 < dest_port < 1024 else 0.0

        orig_pkts = float(event.get("orig_pkts", 0) or 0)
        resp_pkts = float(event.get("resp_pkts", 0) or 0)

        return [
            duration,
            orig_bytes,
            resp_bytes,
            proto_tcp,
            proto_udp,
            proto_other,
            conn_state_failed,
            dest_port_privileged,
            orig_pkts,
            resp_pkts,
        ]
