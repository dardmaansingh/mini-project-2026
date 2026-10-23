"""
Unit tests for NetSentinel Correlation and Detection Engine.
Validates rule logic across DNS spikes, port scans, brute force, and rogue devices.
"""

import pytest
from datetime import datetime, timezone, timedelta
from backend.app.detection.engine import DetectionEngine
from backend.app.normalization.schema import NormalizedEvent


@pytest.mark.asyncio
async def test_dns_rate_anomaly_detection():
    alerts = []
    async def capture_alert(a: dict):
        alerts.append(a)

    engine = DetectionEngine(on_alert=capture_alert)
    now = datetime.now(timezone.utc)
    source_ip = "10.20.1.45"

    # Inject 60 rapid DNS events from source_ip
    for i in range(60):
        ev = NormalizedEvent(
            event_type="dns_query",
            source_type="syslog",
            timestamp_utc=now + timedelta(seconds=i * 0.5),
            source_ip=source_ip,
            destination_ip="10.20.0.1",
            domain=f"subdomain-{i}.tunnel.attacker.com",
            simulated=True,
        )
        await engine.process_event(ev)

    dns_alerts = [a for a in alerts if a["rule_id"] == "RULE-001"]
    assert len(dns_alerts) >= 1
    assert dns_alerts[0]["source_ip"] == source_ip
    assert dns_alerts[0]["severity"] in ("medium", "high")


@pytest.mark.asyncio
async def test_port_scan_detection():
    alerts = []
    async def capture_alert(a: dict):
        alerts.append(a)

    engine = DetectionEngine(on_alert=capture_alert)
    now = datetime.now(timezone.utc)
    source_ip = "10.10.5.99"

    # Contact 25 distinct destination ports from same source
    for p in range(25):
        ev = NormalizedEvent(
            event_type="connection",
            source_type="zeek",
            timestamp_utc=now + timedelta(seconds=p),
            source_ip=source_ip,
            destination_ip="10.10.1.10",
            destination_port=1000 + p,
            protocol="tcp",
            simulated=True,
        )
        await engine.process_event(ev)

    scan_alerts = [a for a in alerts if a["rule_id"] == "RULE-002"]
    assert len(scan_alerts) >= 1
    assert scan_alerts[0]["source_ip"] == source_ip
    assert scan_alerts[0]["severity"] == "high"


@pytest.mark.asyncio
async def test_auth_brute_force_detection():
    alerts = []
    async def capture_alert(a: dict):
        alerts.append(a)

    engine = DetectionEngine(on_alert=capture_alert)
    now = datetime.now(timezone.utc)
    source_ip = "10.10.2.14"

    # Inject 8 failed authentication attempts
    for i in range(8):
        ev = NormalizedEvent(
            event_type="auth_failure",
            source_type="radius",
            timestamp_utc=now + timedelta(seconds=i * 2),
            source_ip=source_ip,
            username=f"student_{i}",
            authentication_result="failure",
            simulated=True,
        )
        await engine.process_event(ev)

    auth_alerts = [a for a in alerts if a["rule_id"] == "RULE-003"]
    assert len(auth_alerts) >= 1
    assert auth_alerts[0]["source_ip"] == source_ip


@pytest.mark.asyncio
async def test_dhcp_anomaly_detection():
    alerts = []
    async def capture_alert(a: dict):
        alerts.append(a)

    engine = DetectionEngine(on_alert=capture_alert)
    now = datetime.now(timezone.utc)

    # Inject unauthorized DHCP offer from non-standard IP
    ev = NormalizedEvent(
        event_type="dhcp",
        source_type="dhcp",
        timestamp_utc=now,
        source_ip="10.10.9.88",
        extra_metadata={"dhcp_message_type": "OFFER", "server_ip": "10.10.9.88", "rogue_server": True},
        simulated=True,
    )
    await engine.process_event(ev)

    dhcp_alerts = [a for a in alerts if a["rule_id"] == "RULE-007"]
    assert len(dhcp_alerts) >= 1
    assert dhcp_alerts[0]["severity"] == "high"
