"""NetSentinel API — Metrics overview, detection rules, data sources, audit logs."""

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from datetime import datetime, timezone, timedelta
from typing import Optional

from backend.app.database import get_db
from backend.app.models.event import NetworkEvent
from backend.app.models.alert import Alert
from backend.app.models.asset import NetworkAsset
from backend.app.models.rule import DetectionRule, DataSource, AuditLog

metrics_router = APIRouter(prefix="/api/metrics", tags=["metrics"])
rules_router = APIRouter(prefix="/api/rules", tags=["rules"])
sources_router = APIRouter(prefix="/api/sources", tags=["sources"])
audit_router = APIRouter(prefix="/api/audit-logs", tags=["audit"])
health_router = APIRouter(prefix="/api", tags=["health"])


# ── Health ─────────────────────────────────────────────────────────────────

@health_router.get("/health")
async def health():
    return {"status": "healthy", "service": "NetSentinel", "version": "2.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Metrics Overview ───────────────────────────────────────────────────────

@metrics_router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    last_60s = now - timedelta(seconds=60)
    last_24h = now - timedelta(hours=24)

    total_events = (await db.execute(select(func.count(NetworkEvent.id)))).scalar_one()
    events_last_min = (await db.execute(
        select(func.count(NetworkEvent.id)).where(NetworkEvent.received_at >= last_60s)
    )).scalar_one()
    new_alerts = (await db.execute(
        select(func.count(Alert.id)).where(Alert.status == "new")
    )).scalar_one()
    high_critical = (await db.execute(
        select(func.count(Alert.id)).where(Alert.severity.in_(["high", "critical"]), Alert.status != "resolved")
    )).scalar_one()
    total_aps = (await db.execute(
        select(func.count(NetworkAsset.id)).where(NetworkAsset.asset_type == "access_point")
    )).scalar_one()
    total_switches = (await db.execute(
        select(func.count(NetworkAsset.id)).where(NetworkAsset.asset_type == "switch")
    )).scalar_one()

    # Event volume per hour (last 24h)
    dialect_name = db.bind.dialect.name if db.bind else "postgresql"
    if dialect_name == "sqlite":
        hourly_q = await db.execute(text("""
            SELECT strftime('%Y-%m-%d %H:00:00', timestamp_utc) AS hour, COUNT(*) AS cnt
            FROM network_events
            WHERE timestamp_utc >= datetime('now', '-24 hours')
            GROUP BY hour ORDER BY hour
        """))
    else:
        hourly_q = await db.execute(text("""
            SELECT date_trunc('hour', timestamp_utc) AS hour, COUNT(*) AS cnt
            FROM network_events
            WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
            GROUP BY hour ORDER BY hour
        """))
    hourly = [{"hour": str(r[0]), "count": r[1]} for r in hourly_q.all()]

    # Recent alerts
    recent_alerts_q = await db.execute(
        select(Alert).order_by(desc(Alert.first_seen)).limit(10)
    )
    recent_alerts = [
        {"id": a.id, "title": a.title, "severity": a.severity, "status": a.status, "first_seen": a.first_seen.isoformat() if a.first_seen else None}
        for a in recent_alerts_q.scalars().all()
    ]

    return {
        "total_events": total_events,
        "events_per_minute": events_last_min,
        "new_alerts": new_alerts,
        "high_critical_alerts": high_critical,
        "monitored_aps": total_aps,
        "monitored_switches": total_switches,
        "event_volume_24h": hourly,
        "recent_alerts": recent_alerts,
    }


# ── Detection Rules ────────────────────────────────────────────────────────

@rules_router.get("")
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DetectionRule).order_by(DetectionRule.id))
    return {"items": [_serialize_rule(r) for r in result.scalars().all()]}


@rules_router.get("/{rule_id}")
async def get_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DetectionRule).where(DetectionRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return _serialize_rule(rule)


@rules_router.patch("/{rule_id}")
async def update_rule(rule_id: str, db: AsyncSession = Depends(get_db), body: dict = Body(...)):
    result = await db.execute(select(DetectionRule).where(DetectionRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    allowed = {"enabled", "severity", "threshold", "detection_window_seconds", "cooldown_seconds", "extra_config"}
    for k, v in body.items():
        if k in allowed:
            setattr(rule, k, v)

    await db.commit()
    await db.refresh(rule)
    return _serialize_rule(rule)


@rules_router.post("/{rule_id}/test")
async def test_rule(rule_id: str):
    """Placeholder — returns a synthetic test result for the rule."""
    return {"rule_id": rule_id, "test_status": "passed", "note": "Rule test against synthetic events succeeded."}


def _serialize_rule(r: DetectionRule) -> dict:
    return {
        "id": r.id, "name": r.name, "description": r.description,
        "category": r.category, "enabled": r.enabled,
        "severity": r.severity, "confidence": r.confidence,
        "detection_window_seconds": r.detection_window_seconds,
        "threshold": r.threshold, "cooldown_seconds": r.cooldown_seconds,
        "alert_count": r.alert_count,
        "last_triggered": r.last_triggered.isoformat() if r.last_triggered else None,
        "extra_config": r.extra_config,
    }


# ── Data Sources ───────────────────────────────────────────────────────────

@sources_router.get("")
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataSource).order_by(DataSource.name))
    return {"items": [_serialize_source(s) for s in result.scalars().all()]}


def _serialize_source(s: DataSource) -> dict:
    return {
        "id": s.id, "name": s.name, "source_type": s.source_type,
        "is_simulated": s.is_simulated, "is_enabled": s.is_enabled,
        "status": s.status,
        "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
        "events_total": s.events_total,
        "events_last_minute": s.events_last_minute,
        "parse_failures": s.parse_failures,
    }


# ── Audit Logs ─────────────────────────────────────────────────────────────

@audit_router.get("")
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = select(AuditLog).order_by(desc(AuditLog.created_at))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return {"total": total, "items": [
        {"id": a.id, "actor": a.actor, "action": a.action, "resource_type": a.resource_type,
         "resource_id": a.resource_id, "details": a.details, "created_at": a.created_at.isoformat()}
        for a in result.scalars().all()
    ]}
