"""
Detection Engine Accuracy and Ground-Truth Validation Test.

Academic Requirement (Verification & Validation):
- Validates detection accuracy on >= 50 real/structured Zeek log entries.
- Verifies Rule-based Port Scan detection.
- Verifies KMP string matching on malicious payloads.
- Verifies Regex signature matching for SQLi and scanner tools.
- Verifies Decision Tree classification correctness.
"""

import os
import unittest
from processor.readers.zeek_reader import ZeekReader
from detection.rules.rule_engine import StatefulRuleEngine
from detection.patterns.regex_patterns import RegexPatternDetector
from detection.ml.decision_tree import DecisionTreeDetector
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

    def test_decision_tree_classification(self):
        """
        Verifies Decision Tree correctly classifies normal traffic as 0 and probe/scan traffic as 1.
        """
        dt = DecisionTreeDetector()

        # Normal established web transaction
        normal_event = {
            "duration": 0.85,
            "orig_bytes": 1200,
            "resp_bytes": 15000,
            "protocol": "tcp",
            "conn_state": "SF",
            "destination_port": 443,
            "orig_pkts": 10,
            "resp_pkts": 14,
        }
        res_normal = dt.classify_event(normal_event)
        self.assertFalse(res_normal["is_suspicious"], "Normal SF connection should not be flagged.")

        # Suspicious port scan probe
        probe_event = {
            "duration": 0.001,
            "orig_bytes": 0,
            "resp_bytes": 0,
            "protocol": "tcp",
            "conn_state": "S0",
            "destination_port": 22,
            "orig_pkts": 1,
            "resp_pkts": 0,
        }
        res_probe = dt.classify_event(probe_event)
        self.assertTrue(res_probe["is_suspicious"], "Failed SYN probe (S0) must be flagged.")


if __name__ == "__main__":
    unittest.main()
