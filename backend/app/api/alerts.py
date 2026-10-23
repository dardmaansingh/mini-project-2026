"""NetSentinel API — Alerts endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime
from typing import Optional

from backend.app.database import get_db
from backend.app.models.alert import Alert, AlertNote
from backend.app.core.websocket import ws_manager

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

VALID_STATUSES = {"new", "acknowledged", "investigating", "resolved", "false_positive"}


@router.get("")
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    rule_id: Optional[str] = None,
    source_ip: Optional[str] = None,
    simulated: Optional[bool] = None,
    since: Optional[datetime] = None,
    sort: str = Query("desc", pattern="^(asc|desc)$"),
):
    q = select(Alert)
    if severity:
        q = q.where(Alert.severity == severity)
    if status:
        q = q.where(Alert.status == status)
    if rule_id:
        q = q.where(Alert.rule_id == rule_id)
    if source_ip:
        q = q.where(Alert.source_ip == source_ip)
    if simulated is not None:
        q = q.where(Alert.simulated == simulated)
    if since:
        q = q.where(Alert.first_seen >= since)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    order = desc(Alert.first_seen) if sort == "desc" else Alert.first_seen
    q = q.order_by(order).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    alerts = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_serialize(a) for a in alerts],
    }


@router.get("/{alert_id}")
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _serialize(alert, detail=True)


@router.patch("/{alert_id}")
async def update_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Body(None),
    assigned_to: Optional[str] = Body(None),
    note: Optional[str] = Body(None),
    author: Optional[str] = Body("system"),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=422, detail=f"Invalid status. Choose from: {VALID_STATUSES}")
        alert.status = status
        now = datetime.utcnow()
        if status == "acknowledged":
            alert.acknowledged_at = now
        elif status in ("resolved", "false_positive"):
            alert.resolved_at = now

    if assigned_to:
        alert.assigned_to = assigned_to

    if note:
        alert_note = AlertNote(alert_id=alert.id, content=note, author=author or "system")
        db.add(alert_note)

    await db.commit()
    await db.refresh(alert)

    # Broadcast status change
    await ws_manager.broadcast({"type": "alert.updated", "data": {"id": alert.id, "status": alert.status}})
    return _serialize(alert, detail=True)


@router.get("/stats/summary")
async def alert_summary(db: AsyncSession = Depends(get_db)):
    """Counts by severity and status for the overview dashboard."""
    by_severity = await db.execute(
        select(Alert.severity, func.count()).group_by(Alert.severity)
    )
    by_status = await db.execute(
        select(Alert.status, func.count()).group_by(Alert.status)
    )
    by_rule = await db.execute(
        select(Alert.rule_name, func.count()).group_by(Alert.rule_name).order_by(func.count().desc()).limit(10)
    )
    total = (await db.execute(select(func.count(Alert.id)))).scalar_one()
    high_critical = (await db.execute(
        select(func.count(Alert.id)).where(Alert.severity.in_(["high", "critical"]), Alert.status != "resolved")
    )).scalar_one()

    return {
        "total": total,
        "high_critical_unresolved": high_critical,
        "by_severity": dict(by_severity.all()),
        "by_status": dict(by_status.all()),
        "top_rules": [{"rule": r, "count": c} for r, c in by_rule.all()],
    }


def _serialize(a: Alert, detail: bool = False) -> dict:
    data = {
        "id": a.id,
        "rule_id": a.rule_id,
        "rule_name": a.rule_name,
        "title": a.title,
        "severity": a.severity,
        "confidence": a.confidence,
        "status": a.status,
        "first_seen": a.first_seen.isoformat() if a.first_seen else None,
        "last_seen": a.last_seen.isoformat() if a.last_seen else None,
        "source_ip": a.source_ip,
        "destination_ip": a.destination_ip,
        "ap_id": a.ap_id,
        "switch_id": a.switch_id,
        "event_count": a.event_count,
        "assigned_to": a.assigned_to,
        "simulated": a.simulated,
    }
    if detail:
        data.update({
            "description": a.description,
            "evidence": a.evidence,
            "recommended_steps": a.recommended_steps,
            "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            "notes": [{"author": n.author, "content": n.content, "created_at": n.created_at.isoformat()} for n in (a.notes or [])],
        })
    return data
