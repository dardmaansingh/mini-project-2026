"""
NetSentinel — Synthetic Event Generator.

Produces realistic but clearly fictional network events for demo/testing.
Every generated event is marked simulated=True.
Supports: normal traffic, DNS spikes, port scans, auth failures,
          bandwidth anomalies, DHCP anomalies, AP disconnections,
          switch port flapping, logging gaps.
"""

from __future__ import annotations
import asyncio
import random
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable

from backend.app.normalization.schema import NormalizedEvent
from backend.app.config import settings

logger = logging.getLogger(__name__)

# ── Fictional college network topology ─────────────────────────────────────
INTERNAL_SUBNETS = ["10.10.{}.{}".format(vlan, host) for vlan in range(1, 6) for host in range(2, 30)]
EXTERNAL_IPS = [
    "8.8.8.8", "1.1.1.1", "142.250.80.14", "52.86.201.3", "104.18.7.92",
    "185.220.101.32", "198.51.100.7", "203.0.113.42", "91.108.4.0",
]
ACCESS_POINTS = ["AP-LIB-01", "AP-LIB-02", "AP-CS-01", "AP-CS-02", "AP-CAFE-01", "AP-ADMIN-01"]
SWITCHES = ["SW-CORE-01", "SW-DIST-01", "SW-DIST-02", "SW-ACC-LIB", "SW-ACC-CS"]
VLANS = ["10", "20", "30", "40", "50"]
DOMAINS = [
    "google.com", "youtube.com", "github.com", "stackoverflow.com",
    "canvas.university.edu", "moodle.university.edu", "library.university.edu",
    "outlook.com", "microsoft.com", "npmjs.com", "pypi.org",
]
SUSPICIOUS_DOMAINS = [
    "malware-c2.xyz", "botnet-controller.ru", "exfil-endpoint.tk",
    "suspicious-beacon.net", "tunnelout.onion.to", "dga-abc123.com",
]
USERNAMES = ["alice", "bob", "charlie", "dave", "eve", "frank", "student01", "student42", "prof_smith"]
DNS_RECORD_TYPES = ["A", "AAAA", "MX", "PTR", "CNAME", "TXT", "SRV"]
PROTOCOLS = ["TCP", "UDP", "ICMP"]

SOURCE_ID = "SYNTHETIC-GENERATOR-001"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _random_internal() -> str:
    return random.choice(INTERNAL_SUBNETS)


def _random_ap() -> str:
    return random.choice(ACCESS_POINTS)


def _random_switch() -> str:
    return random.choice(SWITCHES)


def _random_vlan() -> str:
    return random.choice(VLANS)


# ── Individual event builders ───────────────────────────────────────────────

def _dns_query(anomalous: bool = False) -> NormalizedEvent:
    domain = random.choice(SUSPICIOUS_DOMAINS if anomalous else DOMAINS)
    return NormalizedEvent(
        timestamp_utc=_now(),
        event_type="dns_query",
        source_type="synthetic",
        source_ip=_random_internal(),
        destination_ip="10.10.0.1",  # campus DNS resolver
        destination_port=53,
        protocol="UDP",
        domain=domain,
        dns_record_type=random.choice(DNS_RECORD_TYPES),
        dns_response_code="NXDOMAIN" if anomalous and random.random() < 0.4 else "NOERROR",
        ap_id=_random_ap() if random.random() < 0.6 else None,
        vlan_id=_random_vlan(),
        simulated=True,
        ingestion_source_id=SOURCE_ID,
        extra_metadata={"scenario": "dns_spike" if anomalous else "normal_dns"},
    )


def _connection_event(suspicious: bool = False) -> NormalizedEvent:
    src = _random_internal()
    dst = random.choice(EXTERNAL_IPS) if suspicious else _random_internal()
    dport = random.choice([80, 443, 8080, 22, 3389, 5900]) if suspicious else random.choice([80, 443, 8080])
    return NormalizedEvent(
        timestamp_utc=_now(),
        event_type="connection",
        source_type="synthetic",
        source_ip=src,
        source_port=random.randint(1024, 65535),
        destination_ip=dst,
        destination_port=dport,
        protocol=random.choice(["TCP", "UDP"]),
        bytes_sent=random.randint(500, 50000),
        bytes_received=random.randint(200, 200000),
        packets=random.randint(5, 500),
        duration_ms=random.uniform(50, 5000),
        ap_id=_random_ap() if random.random() < 0.5 else None,
        vlan_id=_random_vlan(),
        simulated=True,
        ingestion_source_id=SOURCE_ID,
        extra_metadata={"scenario": "suspicious_outbound" if suspicious else "normal_connection"},
    )


def _auth_event(failure: bool = False) -> NormalizedEvent:
    return NormalizedEvent(
        timestamp_utc=_now(),
        event_type="auth_failure" if failure else "auth_success",
        source_type="synthetic",
        source_ip=_random_internal(),
        destination_ip="10.10.0.10",  # RADIUS / auth server
        destination_port=1812,
        protocol="UDP",
        username=random.choice(USERNAMES),
        authentication_result="failure" if failure else "success",
        ap_id=_random_ap(),
        vlan_id=_random_vlan(),
        simulated=True,
        ingestion_source_id=SOURCE_ID,
        extra_metadata={"scenario": "auth_failure" if failure else "normal_auth"},
    )


def _port_scan_burst(source_ip: Optional[str] = None) -> list[NormalizedEvent]:
    """Generate a burst of connection attempts simulating a port scan."""
    src = source_ip or _random_internal()
    target = _random_internal()
    events = []
    for port in random.sample(range(1, 10000), random.randint(25, 80)):
        events.append(NormalizedEvent(
            timestamp_utc=_now(),
            event_type="connection",
            source_type="synthetic",
            source_ip=src,
            source_port=random.randint(1024, 65535),
            destination_ip=target,
            destination_port=port,
            protocol="TCP",
            bytes_sent=64,
            bytes_received=0,
            packets=1,
            duration_ms=random.uniform(0.1, 5.0),
            simulated=True,
            ingestion_source_id=SOURCE_ID,
            extra_metadata={"scenario": "port_scan"},
        ))
    return events


def _bandwidth_spike(source_ip: Optional[str] = None) -> NormalizedEvent:
    src = source_ip or _random_internal()
    return NormalizedEvent(
        timestamp_utc=_now(),
        event_type="flow",
        source_type="synthetic",
        source_ip=src,
        destination_ip=random.choice(EXTERNAL_IPS),
        destination_port=443,
        protocol="TCP",
        bytes_sent=random.randint(500_000_000, 2_000_000_000),  # hundreds of MB
        bytes_received=random.randint(10_000, 1_000_000),
        packets=random.randint(50000, 500000),
        duration_ms=random.uniform(30000, 120000),
        simulated=True,
        ingestion_source_id=SOURCE_ID,
        extra_metadata={"scenario": "bandwidth_anomaly"},
    )


def _dhcp_anomaly() -> NormalizedEvent:
    return NormalizedEvent(
        timestamp_utc=_now(),
        event_type="dhcp",
        source_type="synthetic",
        source_ip=_random_internal(),
        destination_ip="255.255.255.255",
        destination_port=67,
        protocol="UDP",
        client_mac=":".join(f"{random.randint(0,255):02x}" for _ in range(6)),
        vlan_id=_random_vlan(),
        simulated=True,
        ingestion_source_id=SOURCE_ID,
        extra_metadata={"scenario": "dhcp_anomaly", "dhcp_message_type": "DISCOVER", "rogue_server": True},
    )


def _ap_disconnect() -> NormalizedEvent:
    return NormalizedEvent(
        timestamp_utc=_now(),
        event_type="ap_event",
        source_type="synthetic",
        source_ip=f"10.10.0.{random.randint(50, 60)}",
        ap_id=_random_ap(),
        switch_id=_random_switch(),
        vlan_id=_random_vlan(),
        simulated=True,
        ingestion_source_id=SOURCE_ID,
        extra_metadata={"scenario": "ap_disconnect", "ap_event_type": "disconnected", "reason": "link_down"},
    )


def _switch_port_flap() -> NormalizedEvent:
    return NormalizedEvent(
        timestamp_utc=_now(),
        event_type="switch_event",
        source_type="synthetic",
        source_ip=f"10.10.0.{random.randint(40, 50)}",
        switch_id=_random_switch(),
        switch_port=f"GigabitEthernet0/{random.randint(1, 48)}",
        vlan_id=_random_vlan(),
        simulated=True,
        ingestion_source_id=SOURCE_ID,
        extra_metadata={"scenario": "switch_port_flap", "event_subtype": random.choice(["up", "down"]), "error_count": random.randint(5, 50)},
    )


def _unknown_device() -> NormalizedEvent:
    return NormalizedEvent(
        timestamp_utc=_now(),
        event_type="connection",
        source_type="synthetic",
        source_ip=f"10.10.{random.randint(6,9)}.{random.randint(2,254)}",  # unknown subnet
        destination_ip=_random_internal(),
        destination_port=random.choice([80, 443, 22]),
        protocol="TCP",
        client_mac=":".join(f"{random.randint(0,255):02x}" for _ in range(6)),
        vlan_id=_random_vlan(),
        simulated=True,
        ingestion_source_id=SOURCE_ID,
        extra_metadata={"scenario": "unknown_device"},
    )


# ── Scenario weights for normal traffic mix ────────────────────────────────
_NORMAL_GENERATORS = [
    (_dns_query, 40),
    (_connection_event, 45),
    (lambda: _auth_event(failure=False), 10),
    (_dhcp_anomaly, 5),
]

_ANOMALY_GENERATORS = [
    (lambda: _dns_query(anomalous=True), 15),
    (lambda: _connection_event(suspicious=True), 20),
    (lambda: _auth_event(failure=True), 25),
    (_bandwidth_spike, 10),
    (_ap_disconnect, 10),
    (_switch_port_flap, 10),
    (_unknown_device, 10),
]


def _weighted_choice(weighted: list[tuple]) -> NormalizedEvent:
    generators, weights = zip(*weighted)
    return random.choices(generators, weights=weights, k=1)[0]()


# ── Generator class ────────────────────────────────────────────────────────

class SyntheticEventGenerator:
    """
    Produces a continuous stream of synthetic network events.
    Call start() to begin; stop() to halt gracefully.
    """

    def __init__(
        self,
        on_event: Callable[[NormalizedEvent], Awaitable[None]],
        events_per_second: float = 2.0,
        anomaly_rate: float = 0.05,
    ):
        self._on_event = on_event
        self._events_per_second = events_per_second
        self._anomaly_rate = anomaly_rate
        self._running = False
        self._paused = False
        self._task: Optional[asyncio.Task] = None

    @property
    def running(self) -> bool:
        return self._running

    @property
    def paused(self) -> bool:
        return self._paused

    def pause(self) -> None:
        self._paused = True
        logger.info("Synthetic generator paused.")

    def resume(self) -> None:
        self._paused = False
        logger.info("Synthetic generator resumed.")

    def set_rate(self, eps: float) -> None:
        self._events_per_second = max(0.1, eps)

    def set_anomaly_rate(self, rate: float) -> None:
        self._anomaly_rate = max(0.0, min(1.0, rate))

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="synthetic-generator")
        logger.info("Synthetic event generator started (%.1f eps, %.0f%% anomaly rate).",
                    self._events_per_second, self._anomaly_rate * 100)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Synthetic event generator stopped.")

    async def _loop(self) -> None:
        while self._running:
            if not self._paused:
                try:
                    event = self._generate_one()
                    await self._on_event(event)
                except Exception as exc:
                    logger.error("Synthetic generator error: %s", exc, exc_info=True)
            interval = 1.0 / max(0.1, self._events_per_second)
            await asyncio.sleep(interval)

    def _generate_one(self) -> NormalizedEvent:
        if random.random() < self._anomaly_rate:
            return _weighted_choice(_ANOMALY_GENERATORS)
        return _weighted_choice(_NORMAL_GENERATORS)

    # ── Manual scenario triggers ───────────────────────────────────────────

    async def trigger_port_scan(self) -> list[NormalizedEvent]:
        events = _port_scan_burst()
        for ev in events:
            await self._on_event(ev)
        return events

    async def trigger_dns_spike(self, count: int = 60) -> list[NormalizedEvent]:
        src = _random_internal()
        events = []
        for _ in range(count):
            ev = _dns_query(anomalous=True)
            ev.source_ip = src
            await self._on_event(ev)
            events.append(ev)
        return events

    async def trigger_auth_brute_force(self, count: int = 20) -> list[NormalizedEvent]:
        src = _random_internal()
        victim = random.choice(USERNAMES)
        events = []
        for _ in range(count):
            ev = _auth_event(failure=True)
            ev.source_ip = src
            ev.username = victim
            await self._on_event(ev)
            events.append(ev)
        return events

    async def trigger_bandwidth_anomaly(self) -> NormalizedEvent:
        ev = _bandwidth_spike()
        await self._on_event(ev)
        return ev
