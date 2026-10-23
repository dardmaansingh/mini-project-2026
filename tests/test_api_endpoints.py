"""
Integration tests for NetSentinel FastAPI REST Endpoints.
Tests endpoints against the running instance or ASGITransport.
"""

import pytest
import httpx


@pytest.fixture
def base_url():
    return "http://127.0.0.1:8000"


@pytest.mark.asyncio
async def test_health_endpoint(base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["service"] == "NetSentinel"
        assert "version" in data


@pytest.mark.asyncio
async def test_metrics_overview(base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        res = await client.get("/api/metrics/overview")
        assert res.status_code == 200
        data = res.json()
        assert "total_events" in data
        assert "events_per_minute" in data
        assert "new_alerts" in data
        assert "monitored_aps" in data
        assert "event_volume_24h" in data


@pytest.mark.asyncio
async def test_events_endpoint(base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        res = await client.get("/api/events?page=1&page_size=10")
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_alerts_endpoint(base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        res = await client.get("/api/alerts?page=1&page_size=10")
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "items" in data


@pytest.mark.asyncio
async def test_access_points_endpoint(base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        res = await client.get("/api/access-points")
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert data["total"] >= 1
        first_ap = data["items"][0]
        assert "ap_id" in first_ap
        assert "name" in first_ap


@pytest.mark.asyncio
async def test_assets_list_and_create(base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        # List assets
        res = await client.get("/api/assets")
        assert res.status_code == 200
        initial_total = res.json()["total"]

        # Create new asset
        payload = {
            "name": "Integration-Test-Sensor",
            "asset_type": "server",
            "ip_address": "10.20.9.188",
            "mac_address": "00:11:22:33:44:88",
            "is_authorized": True,
            "status": "online",
            "location": "Server Room",
        }
        create_res = await client.post("/api/assets", json=payload)
        assert create_res.status_code == 200
        created = create_res.json()
        assert created["name"] == "Integration-Test-Sensor"
        assert created["ip_address"] == "10.20.9.188"

        # Verify count increment
        res2 = await client.get("/api/assets")
        assert res2.json()["total"] == initial_total + 1


@pytest.mark.asyncio
async def test_rules_list_and_patch(base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        res = await client.get("/api/rules")
        assert res.status_code == 200
        rules = res.json()["items"]
        assert len(rules) >= 10

        rule_id = rules[0]["id"]
        patch_res = await client.patch(f"/api/rules/{rule_id}", json={"threshold": 45})
        assert patch_res.status_code == 200
        assert patch_res.json()["threshold"] == 45


@pytest.mark.asyncio
async def test_data_sources_list(base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        res = await client.get("/api/sources")
        assert res.status_code == 200
        sources = res.json()["items"]
        assert len(sources) >= 1
        types = [s["source_type"] for s in sources]
        assert "synthetic" in types


@pytest.mark.asyncio
async def test_audit_logs_list(base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        res = await client.get("/api/audit-logs")
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "items" in data
