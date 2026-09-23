"""
Unit Tests for Zeek Parser.

Verifies:
- Standard TSV log parsing with #fields and #types.
- JSON line parsing.
- Handling of unset fields (-).
- Malformed line resilience.
"""

import unittest
from processor.parser.zeek_parser import ZeekParser


class TestZeekParser(unittest.TestCase):

    def setUp(self):
        self.parser = ZeekParser()

    def test_tsv_header_and_data_line(self):
        header_fields = "#fields\tts\tuid\tid.orig_h\tid.orig_p\tid.resp_h\tid.resp_p\tproto\tservice\tduration\torig_bytes\tresp_bytes\tconn_state"
        header_types = "#types\ttime\tstring\taddr\tport\taddr\tport\tstring\tstring\tinterval\tcount\tcount\tstring"

        self.assertIsNone(self.parser.parse_line(header_fields))
        self.assertIsNone(self.parser.parse_line(header_types))

        data_line = "1727096400.123\tCtest01\t192.168.1.50\t49152\t8.8.8.8\t53\tudp\tdns\t0.005\t45\t120\tSF"
        record = self.parser.parse_line(data_line)

        self.assertIsNotNone(record)
        self.assertEqual(record["source_ip"], "192.168.1.50")
        self.assertEqual(record["source_port"], 49152)
        self.assertEqual(record["destination_ip"], "8.8.8.8")
        self.assertEqual(record["destination_port"], 53)
        self.assertEqual(record["protocol"], "udp")
        self.assertEqual(record["service"], "dns")
        self.assertEqual(record["duration"], 0.005)
        self.assertEqual(record["orig_bytes"], 45)
        self.assertEqual(record["resp_bytes"], 120)
        self.assertEqual(record["conn_state"], "SF")

    def test_unset_dash_fields(self):
        line = "1727096400.000\tCtest02\t10.0.0.1\t1234\t10.0.0.2\t80\ttcp\t-\t-\t-\t-\tS0"
        # Reset parser with default headers
        parser = ZeekParser()
        parser._set_default_conn_fields()
        # Create line matching default 21 fields
        full_line = "1727096400.000\tCtest02\t10.0.0.1\t1234\t10.0.0.2\t80\ttcp\t-\t-\t-\t-\tS0\t-\t-\t0\tS\t1\t40\t0\t0\t-"
        record = parser.parse_line(full_line)

        self.assertIsNotNone(record)
        self.assertEqual(record["duration"], 0.0)
        self.assertEqual(record["orig_bytes"], 0)
        self.assertEqual(record["service"], "-")
        self.assertEqual(record["conn_state"], "S0")

    def test_json_line_parsing(self):
        json_line = '{"ts": 1727096400.5, "uid": "Cjson01", "id.orig_h": "172.16.0.5", "id.orig_p": 5555, "id.resp_h": "1.1.1.1", "id.resp_p": 53, "proto": "udp", "conn_state": "SF"}'
        record = self.parser.parse_line(json_line)

        self.assertIsNotNone(record)
        self.assertEqual(record["source_ip"], "172.16.0.5")
        self.assertEqual(record["destination_port"], 53)
        self.assertEqual(record["protocol"], "udp")

    def test_malformed_line_handling(self):
        malformed = "invalid_line_with_too_few_columns\tanother_column"
        record = self.parser.parse_line(malformed)
        self.assertIsNone(record)
        self.assertGreater(self.parser.error_count, 0)


if __name__ == "__main__":
    unittest.main()
