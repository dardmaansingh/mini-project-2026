"""
Test Log Generator Script.

Generates synthetic Zeek conn.log entries for stress testing, 1000-entry burst benchmarks,
and edge case validation without requiring live packet capture.
"""

import os
import random
import time
from typing import List, Dict, Any


def generate_zeek_conn_records(count: int = 1000) -> List[Dict[str, Any]]:
    """Generates structured in-memory Zeek event dictionaries."""
    records = []
    base_ts = time.time() - 3600

    for i in range(count):
        # 80% normal traffic, 15% scan probe, 5% heavy transfer
        scenario = random.choices(["normal", "scan", "heavy"], weights=[0.80, 0.15, 0.05])[0]

        if scenario == "normal":
            record = {
                "uid": f"Ctest{i:06d}",
                "timestamp": base_ts + (i * 0.1),
                "source_ip": f"192.168.1.{random.randint(10, 200)}",
                "source_port": random.randint(30000, 65000),
                "destination_ip": "192.168.1.1",
                "destination_port": random.choice([80, 443, 53, 22]),
                "protocol": random.choice(["tcp", "udp"]),
                "service": random.choice(["http", "ssl", "dns"]),
                "duration": round(random.uniform(0.01, 2.5), 4),
                "orig_bytes": random.randint(100, 5000),
                "resp_bytes": random.randint(200, 25000),
                "conn_state": "SF",
                "history": "ShADadfF",
                "orig_pkts": random.randint(3, 15),
                "resp_pkts": random.randint(3, 20),
            }
        elif scenario == "scan":
            record = {
                "uid": f"Ctest{i:06d}",
                "timestamp": base_ts + (i * 0.1),
                "source_ip": "10.0.0.77",  # Attacker IP
                "source_port": random.randint(40000, 50000),
                "destination_ip": "192.168.1.50",
                "destination_port": (i % 500) + 1,  # Stepping through ports
                "protocol": "tcp",
                "service": "-",
                "duration": 0.001,
                "orig_bytes": 0,
                "resp_bytes": 0,
                "conn_state": "S0",
                "history": "S",
                "orig_pkts": 1,
                "resp_pkts": 0,
            }
        else:  # heavy / exfiltration
            record = {
                "uid": f"Ctest{i:06d}",
                "timestamp": base_ts + (i * 0.1),
                "source_ip": "192.168.1.99",
                "source_port": 54321,
                "destination_ip": "203.0.113.5",
                "destination_port": 443,
                "protocol": "tcp",
                "service": "ssl",
                "duration": 45.2,
                "orig_bytes": 15_000_000,
                "resp_bytes": 1200,
                "conn_state": "SF",
                "history": "ShADadFf",
                "orig_pkts": 12000,
                "resp_pkts": 800,
            }

        records.append(record)
    return records


def export_zeek_tsv(records: List[Dict[str, Any]], output_path: str):
    """Writes records into authentic Zeek TSV format."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fields = [
        "ts", "uid", "id.orig_h", "id.orig_p", "id.resp_h", "id.resp_p",
        "proto", "service", "duration", "orig_bytes", "resp_bytes",
        "conn_state", "local_orig", "local_resp", "missed_bytes",
        "history", "orig_pkts", "orig_ip_bytes", "resp_pkts", "resp_ip_bytes", "tunnel_parents"
    ]
    types = [
        "time", "string", "addr", "port", "addr", "port",
        "string", "string", "interval", "count", "count",
        "string", "bool", "bool", "count", "string", "count", "count", "count", "count", "set[string]"
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#separator \\x09\n")
        f.write("#set_separator\t,\n")
        f.write("#empty_field\t(empty)\n")
        f.write("#unset_field\t-\n")
        f.write("#path\tconn\n")
        f.write(f"#open\t{time.strftime('%Y-%m-%d-%H-%M-%S')}\n")
        f.write("#fields\t" + "\t".join(fields) + "\n")
        f.write("#types\t" + "\t".join(types) + "\n")

        for r in records:
            row = [
                f"{r['timestamp']:.6f}",
                r["uid"],
                r["source_ip"],
                str(r["source_port"]),
                r["destination_ip"],
                str(r["destination_port"]),
                r["protocol"],
                r["service"],
                f"{r['duration']:.4f}",
                str(r["orig_bytes"]),
                str(r["resp_bytes"]),
                r["conn_state"],
                "-", "-", "0",
                r["history"],
                str(r["orig_pkts"]),
                str(r["orig_pkts"] * 40),
                str(r["resp_pkts"]),
                str(r["resp_pkts"] * 40),
                "-"
            ]
            f.write("\t".join(row) + "\n")

        f.write(f"#close\t{time.strftime('%Y-%m-%d-%H-%M-%S')}\n")


if __name__ == "__main__":
    records = generate_zeek_conn_records(1000)
    out_file = "logs/test/burst_1000_conn.log"
    export_zeek_tsv(records, out_file)
    print(f"[+] Successfully generated 1000 Zeek log records in {out_file}")
