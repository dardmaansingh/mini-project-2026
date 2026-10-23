"""NetSentinel API — Assets and Access Points endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime

from backend.app.database import get_db
from backend.app.models.asset import NetworkAsset
from backend.app.models.event import NetworkEvent
from backend.app.models.alert import Alert

assets_router = APIRouter(prefix="/api/assets", tags=["assets"])
ap_router = APIRouter(prefix="/api/access-points", tags=["access-points"])


# ── Assets ──────────────────────────────────────────────────────────────────

@assets_router.get("")
async def list_assets(
    db: AsyncSession = Depends(get_db),
    asset_type: Optional[str] = None,
    is_authorized: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    q = select(NetworkAsset)
    if asset_type:
        q = q.where(NetworkAsset.asset_type == asset_type)
    if is_authorized is not None:
        q = q.where(NetworkAsset.is_authorized == is_authorized)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(NetworkAsset.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return {"total": total, "items": [_serialize_asset(a) for a in result.scalars().all()]}


@assets_router.post("")
async def create_asset(db: AsyncSession = Depends(get_db), body: dict = Body(...)):
    asset = NetworkAsset(**body)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return _serialize_asset(asset)


@assets_router.get("/{asset_id}")
async def get_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NetworkAsset).where(NetworkAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return _serialize_asset(asset)


def _serialize_asset(a: NetworkAsset) -> dict:
    return {
        "id": a.id,
        "asset_type": a.asset_type,
        "name": a.name,
        "hostname": a.hostname,
        "ip_address": a.ip_address,
        "mac_address": a.mac_address,
        "vendor": a.vendor,
        "location": a.location,
        "ap_id": a.ap_id,
        "ssid": a.ssid,
        "switch_id": a.switch_id,
        "switch_port": a.switch_port,
        "vlan_id": a.vlan_id,
        "is_authorized": a.is_authorized,
        "status": a.status,
        "last_seen": a.last_seen.isoformat() if a.last_seen else None,
    }


# ── Access Points ────────────────────────────────────────────────────────────

@ap_router.get("")
async def list_access_points(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NetworkAsset).where(NetworkAsset.asset_type == "access_point")
    )
    aps = result.scalars().all()

    # Enrich with recent event counts
    enriched = []
    for ap in aps:
        count_result = await db.execute(
            select(func.count(NetworkEvent.id)).where(NetworkEvent.ap_id == ap.ap_id)
        )
        event_count = count_result.scalar_one()
        alert_count_result = await db.execute(
            select(func.count(Alert.id)).where(Alert.ap_id == ap.ap_id, Alert.status != "resolved")
        )
        alert_count = alert_count_result.scalar_one()
        data = _serialize_asset(ap)
        data["recent_event_count"] = event_count
        data["open_alert_count"] = alert_count
        enriched.append(data)

    return {"total": len(enriched), "items": enriched}


@ap_router.get("/{ap_id}/events")
async def get_ap_events(
    ap_id: str,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = select(NetworkEvent).where(NetworkEvent.ap_id == ap_id).order_by(desc(NetworkEvent.timestamp_utc))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    events = result.scalars().all()
    return {
        "ap_id": ap_id,
        "total": total,
        "items": [{
            "id": e.id,
            "timestamp_utc": e.timestamp_utc.isoformat() if e.timestamp_utc else None,
            "event_type": e.event_type,
            "source_ip": e.source_ip,
            "domain": e.domain,
            "simulated": e.simulated,
        } for e in events],
    }


@ap_router.get("/{ap_id}/alerts")
async def get_ap_alerts(ap_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alert).where(Alert.ap_id == ap_id).order_by(desc(Alert.first_seen)).limit(50)
    )
    return {"ap_id": ap_id, "items": [
        {"id": a.id, "title": a.title, "severity": a.severity, "status": a.status, "first_seen": a.first_seen.isoformat() if a.first_seen else None}
        for a in result.scalars().all()
    ]}
