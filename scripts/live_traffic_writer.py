"""
Live Traffic and DNS Event Log Writer CLI.

Simulates real devices sending packets and DNS queries on the network,
instantly writing Zeek 9.0 formatted entries into conn.log and dns.log.
"""

import sys
import time
import argparse
from processor.live.live_zeek_writer import LiveZeekWriter


def main():
    parser = argparse.ArgumentParser(description="Live Zeek Traffic & DNS Event Writer")
    parser.add_argument("--conn-log", default="logs/sample/conn.log", help="Path to conn.log")
    parser.add_argument("--dns-log", default="logs/sample/dns.log", help="Path to dns.log")
    parser.add_argument("--dns-query", type=str, help="Simulate a single live DNS query")
    parser.add_argument("--dns-flood", action="store_true", help="Simulate an excessive DNS flood attack")
    parser.add_argument("--count", type=int, default=35, help="Number of queries for DNS flood")
    parser.add_argument("--ip", type=str, default="192.168.1.155", help="Source IP of sending device")
    parser.add_argument("--continuous", action="store_true", help="Continuously emit background traffic and DNS queries")
    parser.add_argument("--interval", type=float, default=0.5, help="Interval between continuous packets (seconds)")

    args = parser.parse_args()
    writer = LiveZeekWriter(conn_log_path=args.conn_log, dns_log_path=args.dns_log)

    print("=" * 60)
    print(" Live Zeek Real-Time Event Writer")
    print(f" Target Logs: {args.conn_log} | {args.dns_log}")
    print("=" * 60)

    if args.dns_query:
        print(f"[*] Emitting live DNS query: {args.dns_query} from {args.ip}...")
        rec = writer.write_dns_query(source_ip=args.ip, query=args.dns_query)
        print(f"[+] Written to {args.conn_log} and {args.dns_log}: {rec['uid']}")

    elif args.dns_flood:
        print(f"[*] Launching excessive DNS flood simulation ({args.count} queries) from {args.ip}...")
        start = time.perf_counter()
        results = writer.simulate_dns_flood(attacker_ip=args.ip, count=args.count, delay_sec=0.02)
        elapsed = time.perf_counter() - start
        print(f"[+] Successfully wrote {len(results)} live DNS events to disk in {elapsed:.4f}s.")
        print(f"[+] Tailers will detect EXCESSIVE_DNS_QUERY_FLOOD alert!")

    elif args.continuous:
        print(f"[*] Continuously streaming live network & DNS events every {args.interval}s (Ctrl+C to stop)...")
        domains = ["google.com", "github.com", "cloudflare.com", "internal-portal.local", "api.stripe.com"]
        try:
            count = 0
            while True:
                count += 1
                query = domains[count % len(domains)]
                writer.write_dns_query(source_ip=f"192.168.1.{100 + (count % 20)}", query=query)
                sys.stdout.write(f"\r[+] Events written: {count} | Last DNS: {query}")
                sys.stdout.flush()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[*] Stopped.")
    else:
        # Default: write 1 sample normal DNS query and 1 HTTP connection
        print("[*] Writing 1 live DNS query and 1 HTTP connection...")
        writer.write_dns_query(source_ip=args.ip, query="dashboard.internal.network")
        writer.write_connection({
            "source_ip": args.ip,
            "destination_ip": "142.250.190.46",
            "destination_port": 443,
            "protocol": "tcp",
            "service": "ssl",
        })
        print(f"[+] Done. Checked and appended to {args.conn_log}.")


if __name__ == "__main__":
    main()
