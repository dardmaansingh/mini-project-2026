"""
Detection Engine Accuracy and Ground-Truth Validation Test.

Academic Requirement (Verification & Validation):
- Validates detection accuracy on >= 50 real/structured Zeek log entries.
- Verifies Rule-based Port Scan detection.
- Verifies KMP string matching on malicious payloads.
- Verifies Regex signature matching for SQLi and scanner tools.
"""

import os
import unittest
from processor.readers.zeek_reader import ZeekReader
from detection.rules.rule_engine import StatefulRuleEngine
from detection.patterns.regex_patterns import RegexPatternDetector
from alerting.alert_manager import AlertManager


class TestDetectionAccuracy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.reader = ZeekReader()
        cls.conn_log_path = os.path.join(os.path.dirname(__file__), "../../logs/sample/conn.log")
        cls.http_log_path = os.path.join(os.path.dirname(__file__), "../../logs/sample/http.log")

    def test_conn_log_ingestion_count(self):
        """Verifies at least 50 valid log entries are read and parsed without error."""
        records = self.reader.read_file(self.conn_log_path)
        self.assertGreaterEqual(len(records), 50, "Sample log must contain >= 50 entries as per department framework.")

    def test_rule_based_port_scan_detection(self):
        """
        Validates that the scanning host 10.0.0.88 probing 16 ports is accurately flagged.
        """
        records = self.reader.read_file(self.conn_log_path)
        rule_engine = StatefulRuleEngine(port_scan_threshold=15, time_window_seconds=60.0)

        all_detections = []
        for r in records:
            dets = rule_engine.evaluate_event(r)
            all_detections.extend(dets)

        scan_alerts = [d for d in all_detections if d.alert_type == "PORT_SCAN_DETECTED"]
        self.assertGreater(len(scan_alerts), 0, "Port scan must be detected for 10.0.0.88")
        self.assertEqual(scan_alerts[0].source_ip, "10.0.0.88")
        self.assertEqual(scan_alerts[0].severity, "HIGH")

    def test_kmp_and_regex_http_detection(self):
        """
        Validates KMP and Regex detection on sample HTTP traffic containing directory traversal,
        SQL injection, and security scanners.
        """
        records = self.reader.read_file(self.http_log_path)
        rule_engine = StatefulRuleEngine()
        regex_detector = RegexPatternDetector()

        kmp_matches = []
        regex_matches = []

        for r in records:
            # Map uri to service/uri field for KMP inspection
            rule_dets = rule_engine.evaluate_event(r)
            kmp_matches.extend([d for d in rule_dets if d.detection_method == "KMP"])

            reg_dets = regex_detector.evaluate_event(r)
            regex_matches.extend(reg_dets)

        # Verify KMP caught /etc/passwd or /etc/shadow
        kmp_patterns = [k.evidence.get("matched_pattern") for k in kmp_matches]
        self.assertIn("etc/passwd", kmp_patterns)

        # Verify Regex caught SQL Injection and Scanner
        regex_patterns = [rm.pattern_name for rm in regex_matches]
        self.assertIn("SQL_INJECTION", regex_patterns)
        self.assertIn("SCANNER_USER_AGENT", regex_patterns)

    def test_excessive_dns_flood_detection(self):
        """
        Validates that high-volume DNS requests exceeding threshold generate EXCESSIVE_DNS_QUERY_FLOOD alerts.
        """
        rule_engine = StatefulRuleEngine(dns_query_threshold=10, time_window_seconds=60.0)
        detections = []
        attacker_ip = "192.168.1.155"

        for i in range(15):
            event = {
                "source_ip": attacker_ip,
                "destination_ip": "1.1.1.1",
                "destination_port": 53,
                "protocol": "udp",
                "service": "dns",
                "timestamp": 1727096400.0 + (i * 0.1),
                "query": f"exfil-chunk-{i}.tunnel.biz",
            }
            dets = rule_engine.evaluate_event(event)
            detections.extend(dets)

        dns_alerts = [d for d in detections if d.alert_type == "EXCESSIVE_DNS_QUERY_FLOOD"]
        self.assertGreater(len(dns_alerts), 0, "Excessive DNS queries must trigger EXCESSIVE_DNS_QUERY_FLOOD alert.")
        self.assertEqual(dns_alerts[0].source_ip, attacker_ip)
        self.assertEqual(dns_alerts[0].severity, "HIGH")
        self.assertIn("DNS requests within", dns_alerts[0].description)


if __name__ == "__main__":
    unittest.main()
