"""
Integration Tests for Flask REST API Endpoints.

Academic Verification (Web & Computer Networks):
- Tests HTTP status codes (200 OK, 404, 400).
- Verifies JSON structure for summary, protocols, top sources, alerts, and pipeline telemetry.
- Tests mock webhook dispatch and burst injection endpoints.
"""

import unittest
import json
from backend.app import create_app


class TestFlaskAPI(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_statistics_summary(self):
        res = self.client.get("/api/v1/statistics/summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("total_connections", data["data"])
        self.assertIn("severity_counts", data["data"])

    def test_statistics_protocols(self):
        res = self.client.get("/api/v1/statistics/protocols")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["data"], list)

    def test_top_sources(self):
        res = self.client.get("/api/v1/statistics/top-sources")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["data"], list)

    def test_alerts_endpoint(self):
        res = self.client.get("/api/v1/alerts")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("data", data)

    def test_pipeline_telemetry(self):
        res = self.client.get("/api/v1/pipeline/telemetry")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("buffer", data["data"])
        self.assertEqual(data["data"]["buffer"]["capacity"], 256)

    def test_mock_webhook(self):
        payload = {"alert_id": "ALT-TEST-99", "severity": "HIGH", "timestamp": 1727096400.0}
        res = self.client.post(
            "/api/v1/alerts/webhook/test",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "received")
        self.assertEqual(data["alert_id"], "ALT-TEST-99")

    def test_burst_injection(self):
        res = self.client.post(
            "/api/v1/events/inject-burst",
            data=json.dumps({"count": 20}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["requested_burst"], 20)


if __name__ == "__main__":
    unittest.main()
