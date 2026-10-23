"""
NetSentinel — FastAPI Application Entry Point.

Wires together: database, WebSocket manager, synthetic generator,
detection engine, alert manager, and all API routers.
"""

from __future__ import annotations
import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import engine, Base, AsyncSessionLocal
from backend.app.core.websocket import ws_manager
from backend.app.ingestion.synthetic import SyntheticEventGenerator
from backend.app.ingestion.pipeline import pipeline
from backend.app.models import *  # noqa: F401,F403 — ensures all models registered with Base

# API routers
from backend.app.api.events import router as events_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.assets import assets_router, ap_router
from backend.app.api.misc import metrics_router, rules_router, sources_router, audit_router, health_router
from backend.app.api.synthetic import router as synthetic_router, set_generator

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Startup seed data ──────────────────────────────────────────────────────

async def _seed_initial_data() -> None:
    """Insert default detection rules and demo data sources if not present."""
    from backend.app.models.rule import DetectionRule, DataSource
    from sqlalchemy import select

    RULES = [
        {"id": "RULE-001", "name": "DNS Query Rate Anomaly", "category": "dns", "severity": "medium",
         "description": "Detects IPs generating unusually high DNS query rates.", "threshold": settings.dns_query_rate_threshold,
         "detection_window_seconds": settings.detection_window_seconds, "cooldown_seconds": 300},
        {"id": "RULE-002", "name": "Port Scan Detected", "category": "network", "severity": "high",
         "description": "Detects a source contacting many distinct ports in a short window.", "threshold": settings.port_scan_port_threshold,
         "detection_window_seconds": settings.detection_window_seconds, "cooldown_seconds": 300},
        {"id": "RULE-003", "name": "Repeated Authentication Failures", "category": "auth", "severity": "medium",
         "description": "Detects brute force or password spray patterns.", "threshold": settings.auth_failure_threshold,
         "detection_window_seconds": settings.detection_window_seconds, "cooldown_seconds": 300},
        {"id": "RULE-004", "name": "Bandwidth Anomaly", "category": "flow", "severity": "medium",
         "description": "Detects unusual increases in data transfer volume.", "threshold": 100.0,
         "detection_window_seconds": settings.detection_window_seconds, "cooldown_seconds": 600},
        {"id": "RULE-005", "name": "Suspicious Outbound Communication", "category": "threat_intel", "severity": "high",
         "description": "Flags connections to known or suspected malicious destinations.", "threshold": None,
         "detection_window_seconds": settings.detection_window_seconds, "cooldown_seconds": 600},
        {"id": "RULE-006", "name": "Unauthorized Device", "category": "asset", "severity": "medium",
         "description": "Detects devices not in the approved asset inventory.", "threshold": None,
         "detection_window_seconds": 3600, "cooldown_seconds": 3600},
        {"id": "RULE-007", "name": "DHCP Anomaly", "category": "dhcp", "severity": "high",
         "description": "Detects rogue DHCP servers or unusual lease behavior.", "threshold": None,
         "detection_window_seconds": settings.detection_window_seconds, "cooldown_seconds": 600},
        {"id": "RULE-008", "name": "Possible Lateral Movement", "category": "network", "severity": "high",
         "description": "Detects unusual internal host-to-host communication patterns.", "threshold": None,
         "detection_window_seconds": 300, "cooldown_seconds": 600},
        {"id": "RULE-009", "name": "Network Infrastructure Anomaly", "category": "infrastructure", "severity": "low",
         "description": "Detects AP disconnections, switch port flapping, link errors.", "threshold": None,
         "detection_window_seconds": 300, "cooldown_seconds": 120},
        {"id": "RULE-010", "name": "Monitoring and Logging Gaps", "category": "monitoring", "severity": "informational",
         "description": "Detects when expected logging sources stop sending events.", "threshold": None,
         "detection_window_seconds": 300, "cooldown_seconds": 300},
    ]

    SOURCES = [
        {"id": str(uuid.uuid4()), "name": "Synthetic Event Generator", "source_type": "synthetic",
         "is_simulated": True, "is_enabled": True, "status": "healthy"},
        {"id": str(uuid.uuid4()), "name": "Campus DNS Resolver (future)", "source_type": "syslog",
         "is_simulated": False, "is_enabled": False, "status": "offline",
         "config": {"note": "Requires college authorization and rsyslog configuration."}},
        {"id": str(uuid.uuid4()), "name": "Zeek Network Sensor (future)", "source_type": "zeek",
         "is_simulated": False, "is_enabled": False, "status": "offline",
         "config": {"note": "Requires authorized network tap and Zeek installation."}},
    ]

    async with AsyncSessionLocal() as session:
        for rule_data in RULES:
            existing = await session.get(DetectionRule, rule_data["id"])
            if not existing:
                session.add(DetectionRule(**rule_data))
        for src in SOURCES:
            result = await session.execute(select(DataSource).where(DataSource.source_type == src["source_type"]))
            if not result.scalar_one_or_none():
                session.add(DataSource(**src))
        await session.commit()

    # Seed demo access points and switches
    from backend.app.models.asset import NetworkAsset
    APS = [
        ("AP-LIB-01", "Library AP Floor 1", "10.10.1.101", "SW-ACC-LIB", "Gi0/1", "10"),
        ("AP-LIB-02", "Library AP Floor 2", "10.10.1.102", "SW-ACC-LIB", "Gi0/2", "10"),
        ("AP-CS-01", "CS Dept AP Lab 1", "10.10.2.101", "SW-ACC-CS", "Gi0/1", "20"),
        ("AP-CS-02", "CS Dept AP Lab 2", "10.10.2.102", "SW-ACC-CS", "Gi0/2", "20"),
        ("AP-CAFE-01", "Cafeteria AP", "10.10.3.101", "SW-DIST-01", "Gi0/5", "30"),
        ("AP-ADMIN-01", "Admin Building AP", "10.10.4.101", "SW-DIST-02", "Gi0/3", "40"),
    ]
    async with AsyncSessionLocal() as session:
        for ap_id, name, ip, sw, port, vlan in APS:
            result = await session.execute(select(NetworkAsset).where(NetworkAsset.ap_id == ap_id))
            if not result.scalar_one_or_none():
                session.add(NetworkAsset(
                    asset_type="access_point", name=name, ip_address=ip,
                    ap_id=ap_id, switch_id=sw, switch_port=port, vlan_id=vlan,
                    is_authorized=True, status="online",
                ))
        await session.commit()


# ── Lifespan ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")

    await _seed_initial_data()
    logger.info("Initial seed data applied.")

    # Start WebSocket broadcast loop
    broadcast_task = asyncio.create_task(ws_manager.broadcast_loop(), name="ws-broadcast")

    # Start synthetic generator
    generator = None
    if settings.synthetic_enabled:
        generator = SyntheticEventGenerator(
            on_event=pipeline.ingest,
            events_per_second=settings.synthetic_events_per_second,
            anomaly_rate=settings.synthetic_anomaly_rate,
        )
        set_generator(generator)
        await generator.start()
        logger.info("Synthetic event generator running.")

    yield  # Application is running

    # Shutdown
    if generator:
        await generator.stop()
    broadcast_task.cancel()
    await engine.dispose()
    logger.info("NetSentinel shutdown complete.")


# ── App factory ────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="NetSentinel API",
        description="College Network Security Monitoring System — REST API",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all routers
    for r in [events_router, alerts_router, assets_router, ap_router,
              metrics_router, rules_router, sources_router, audit_router,
              health_router, synthetic_router]:
        app.include_router(r)

    # WebSocket endpoint
    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                # Keep connection alive; handle client ping/pong
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
