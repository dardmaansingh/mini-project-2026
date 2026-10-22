"""
Integration Tests for Wireless REST API Endpoints.

Validates:
- /api/v1/wireless/summary
- /api/v1/wireless/networks (including search & filtering)
- /api/v1/wireless/suspicious
- /api/v1/wireless/spectrum
- /api/v1/wireless/rssi-timeline
- /api/v1/wireless/interfaces
- /api/v1/wireless/scan
- /api/v1/wireless/inject-threat
- /api/v1/wireless/mitigate
"""

import unittest
import json
from backend.app import create_app


class TestWirelessAPI(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_wireless_summary(self):
        res = self.client.get("/api/v1/wireless/summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("total_networks", data["data"])
        self.assertIn("suspicious_count", data["data"])
        self.assertIn("average_rssi_dbm", data["data"])

    def test_wireless_networks(self):
        res = self.client.get("/api/v1/wireless/networks")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["data"], list)
        self.assertGreater(len(data["data"]), 0)

        first_net = data["data"][0]
        self.assertIn("bssid", first_net)
        self.assertIn("ssid", first_net)
        self.assertIn("rssi", first_net)
        self.assertIn("signal_quality", first_net)
        self.assertIn("channel", first_net)
        self.assertIn("security", first_net)

    def test_wireless_suspicious_endpoint(self):
        res = self.client.get("/api/v1/wireless/suspicious")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["data"], list)

    def test_wireless_spectrum(self):
        res = self.client.get("/api/v1/wireless/spectrum")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("band_2_4ghz", data["data"])
        self.assertIn("band_5ghz", data["data"])

    def test_wireless_rssi_timeline(self):
        res = self.client.get("/api/v1/wireless/rssi-timeline")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("timeline_series", data["data"])

    def test_wireless_interfaces(self):
        res = self.client.get("/api/v1/wireless/interfaces")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("active_interface", data)

    def test_trigger_scan(self):
        res = self.client.post("/api/v1/wireless/scan")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")

    def test_inject_threat_and_mitigate(self):
        # Inject Evil Twin
        res = self.client.post(
            "/api/v1/wireless/inject-threat",
            data=json.dumps({"threat_type": "EVIL_TWIN"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        bssid = data["data"]["target"]["bssid"]

        # Now Mitigate it
        mit_res = self.client.post(
            "/api/v1/wireless/mitigate",
            data=json.dumps({"bssid": bssid}),
            content_type="application/json",
        )
        self.assertEqual(mit_res.status_code, 200)
        mit_data = mit_res.get_json()
        self.assertEqual(mit_data["status"], "success")


if __name__ == "__main__":
    unittest.main()
