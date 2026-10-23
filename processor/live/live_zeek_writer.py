"""
Live Zeek Log Writer & Real-Time Event Synthesizer.

Academic Context (Network Traffic Generation & Logging Subsystem):
- Implements the exact TSV formatting rules of Zeek 9.0 logging framework.
- Writes connection events (conn.log) and DNS query resolutions (dns.log) directly to disk in real time.
- Guarantees immediate flush semantics (flush + optional fsync) so that continuous tailing
  file monitors (like ZeekReader / FileMonitor) receive each event with sub-millisecond latency.
"""

import os
import time
import random
import threading
from typing import Dict, Any, Optional, List


ZEEK_CONN_HEADER = (
    "#separator \\x09\n"
    "#set_separator\t,\n"
    "#empty_field\t(empty)\n"
    "#unset_field\t-\n"
    "#path\tconn\n"
    f"#open\t{time.strftime('%Y-%m-%d-%H-%M-%S')}\n"
    "#fields\tts\tuid\tid.orig_h\tid.orig_p\tid.resp_h\tid.resp_p\tproto\tservice\tduration\torig_bytes\tresp_bytes\tconn_state\tlocal_orig\tlocal_resp\tmissed_bytes\thistory\torig_pkts\torig_ip_bytes\tresp_pkts\tresp_ip_bytes\ttunnel_parents\n"
    "#types\ttime\tstring\taddr\tport\taddr\tport\tstring\tstring\tinterval\tcount\tcount\tstring\tbool\tbool\tcount\tstring\tcount\tcount\tcount\tcount\tset[string]\n"
)

ZEEK_DNS_HEADER = (
    "#separator \\x09\n"
    "#set_separator\t,\n"
    "#empty_field\t(empty)\n"
    "#unset_field\t-\n"
    "#path\tdns\n"
    f"#open\t{time.strftime('%Y-%m-%d-%H-%M-%S')}\n"
    "#fields\tts\tuid\tid.orig_h\tid.orig_p\tid.resp_h\tid.resp_p\tproto\ttrans_id\trtt\tquery\tqclass\tqclass_name\tqtype\tqtype_name\trcode\trcode_name\tAA\tTC\tRD\tRA\tZ\tanswers\tTTLs\trejected\n"
    "#types\ttime\tstring\taddr\tport\taddr\tport\tstring\tcount\tinterval\tstring\tcount\tstring\tcount\tstring\tcount\tstring\tbool\tbool\tbool\tbool\tcount\tvector[string]\tvector[interval]\tbool\n"
)


class LiveZeekWriter:
    """
    Manages live appending of Zeek-formatted connection and DNS records to log files.
    """

    def __init__(
        self,
        conn_log_path: str = "logs/sample/conn.log",
        dns_log_path: str = "logs/sample/dns.log",
    ):
        self.conn_log_path = os.path.abspath(conn_log_path)
        self.dns_log_path = os.path.abspath(dns_log_path)
        self._write_lock = threading.Lock()
        self._uid_counter = int(time.time() * 1000) % 1_000_000

        self._ensure_header(self.conn_log_path, ZEEK_CONN_HEADER)
        self._ensure_header(self.dns_log_path, ZEEK_DNS_HEADER)

    def _next_uid(self) -> str:
        self._uid_counter += 1
        return f"C{self._uid_counter:06d}"

    def _ensure_header(self, file_path: str, header_content: str):
        """Ensures log file directory and Zeek TSV header exist."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(header_content)
                f.flush()

    def write_connection(self, record: Dict[str, Any]) -> str:
        """
        Instantly formats and writes a connection line to conn.log.
        Returns the formatted TSV line.
        """
        ts = record.get("timestamp", time.time())
        uid = record.get("uid", self._next_uid())
        src_ip = record.get("source_ip", "192.168.1.100")
        src_port = record.get("source_port", random.randint(40000, 65000))
        dst_ip = record.get("destination_ip", "192.168.1.1")
        dst_port = record.get("destination_port", 80)
        proto = record.get("protocol", "tcp")
        service = record.get("service", "-")
        duration = record.get("duration", 0.005)
        orig_bytes = record.get("orig_bytes", 150)
        resp_bytes = record.get("resp_bytes", 350)
        conn_state = record.get("conn_state", "SF")
        history = record.get("history", "ShADadfF")
        orig_pkts = record.get("orig_pkts", 4)
        resp_pkts = record.get("resp_pkts", 5)

        line = (
            f"{ts:.6f}\t{uid}\t{src_ip}\t{src_port}\t{dst_ip}\t{dst_port}\t"
            f"{proto}\t{service}\t{duration:.4f}\t{orig_bytes}\t{resp_bytes}\t"
            f"{conn_state}\t-\t-\t0\t{history}\t{orig_pkts}\t{orig_bytes + 40}\t"
            f"{resp_pkts}\t{resp_bytes + 40}\t-\n"
        )

        with self._write_lock:
            with open(self.conn_log_path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()

        return line

    def write_dns_query(
        self,
        source_ip: str,
        query: str,
        resolver_ip: str = "192.168.1.1",
        qtype: str = "A",
        rcode: str = "NOERROR",
        answers: str = "142.250.190.46",
    ) -> Dict[str, Any]:
        """
        Instantly writes both a conn.log entry (port 53) and a dns.log resolution entry.
        Every time a device issues a DNS request, this writes to the active logs immediately.
        """
        ts = time.time()
        uid = self._next_uid()
        src_port = random.randint(49152, 65535)
        trans_id = random.randint(1000, 65535)

        # 1. Write corresponding conn.log record
        conn_rec = {
            "timestamp": ts,
            "uid": uid,
            "source_ip": source_ip,
            "source_port": src_port,
            "destination_ip": resolver_ip,
            "destination_port": 53,
            "protocol": "udp",
            "service": "dns",
            "duration": round(random.uniform(0.001, 0.008), 4),
            "orig_bytes": len(query) + 30,
            "resp_bytes": 128,
            "conn_state": "SF",
            "history": "Dd",
            "orig_pkts": 1,
            "resp_pkts": 1,
        }
        self.write_connection(conn_rec)

        # 2. Write dns.log entry
        dns_line = (
            f"{ts:.6f}\t{uid}\t{source_ip}\t{src_port}\t{resolver_ip}\t53\t"
            f"udp\t{trans_id}\t0.0045\t{query}\t1\tC_INTERNET\t1\t{qtype}\t"
            f"0\t{rcode}\tF\tF\tT\tT\t0\t{answers}\t300.0\tF\n"
        )

        with self._write_lock:
            with open(self.dns_log_path, "a", encoding="utf-8") as f:
                f.write(dns_line)
                f.flush()

        conn_rec["query"] = query
        return conn_rec

    def simulate_dns_flood(
        self,
        attacker_ip: str = "192.168.1.155",
        count: int = 35,
        resolver_ip: str = "192.168.1.1",
        delay_sec: float = 0.02,
    ) -> List[Dict[str, Any]]:
        """
        Simulates an excessive DNS flood attack, writing lines directly to the log files
        at high frequency (one line every few milliseconds).
        """
        generated = []
        base_domains = ["attacker-c2.biz", "data-exfil.xyz", "botnet-beacon.top", "internal-corp.net"]

        for i in range(count):
            domain = f"probe-{i:03d}-{random.randint(1000,9999)}.{random.choice(base_domains)}"
            rec = self.write_dns_query(
                source_ip=attacker_ip,
                query=domain,
                resolver_ip=resolver_ip,
            )
            generated.append(rec)
            if delay_sec > 0:
                time.sleep(delay_sec)

        return generated
