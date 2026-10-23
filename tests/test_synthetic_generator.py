"""
Unit tests for NetSentinel Synthetic Event Generator and Attack Scenarios.
"""

import pytest
import asyncio
from backend.app.ingestion.synthetic import SyntheticEventGenerator
from backend.app.normalization.schema import NormalizedEvent


@pytest.mark.asyncio
async def test_generator_event_structure():
    received_events = []

    async def on_event(ev: NormalizedEvent):
        received_events.append(ev)

    gen = SyntheticEventGenerator(
        on_event=on_event,
        events_per_second=20.0,
        anomaly_rate=0.1,
    )
    await gen.start()
    await asyncio.sleep(0.5)
    await gen.stop()

    assert len(received_events) >= 1
    sample = received_events[0]
    assert sample.simulated is True
    assert sample.event_type in (
        "connection", "dns_query", "auth_failure", "auth_success", "dhcp", "flow"
    )
    assert sample.source_ip is not None


@pytest.mark.asyncio
async def test_trigger_port_scan_scenario():
    received_events = []

    async def on_event(ev: NormalizedEvent):
        received_events.append(ev)

    gen = SyntheticEventGenerator(on_event=on_event)
    events = await gen.trigger_port_scan()

    assert len(events) >= 20
    assert len({e.destination_port for e in events}) >= 15
    assert len(received_events) == len(events)


@pytest.mark.asyncio
async def test_trigger_dns_spike_scenario():
    received_events = []

    async def on_event(ev: NormalizedEvent):
        received_events.append(ev)

    gen = SyntheticEventGenerator(on_event=on_event)
    events = await gen.trigger_dns_spike(count=40)

    assert len(events) == 40
    assert all(e.event_type == "dns_query" for e in events)
    assert len(received_events) == 40


@pytest.mark.asyncio
async def test_trigger_brute_force_scenario():
    received_events = []

    async def on_event(ev: NormalizedEvent):
        received_events.append(ev)

    gen = SyntheticEventGenerator(on_event=on_event)
    events = await gen.trigger_auth_brute_force(count=15)

    assert len(events) == 15
    assert all(e.event_type == "auth_failure" for e in events)
    assert all(e.authentication_result == "failure" for e in events)
    assert len(received_events) == 15


@pytest.mark.asyncio
async def test_pause_and_resume():
    received_events = []

    async def on_event(ev: NormalizedEvent):
        received_events.append(ev)

    gen = SyntheticEventGenerator(on_event=on_event, events_per_second=20.0)
    await gen.start()

    # Pause
    gen.pause()
    assert gen.paused is True
    count_before = len(received_events)
    await asyncio.sleep(0.3)
    count_after = len(received_events)
    # When paused, no events should be emitted
    assert count_after == count_before

    # Resume
    gen.resume()
    assert gen.paused is False
    await asyncio.sleep(0.3)
    assert len(received_events) > count_after

    await gen.stop()
