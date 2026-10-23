"""NetSentinel API — Events endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone
from typing import Optional

from backend.app.database import get_db
from backend.app.models.event import NetworkEvent

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
async def list_events(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    event_type: Optional[str] = None,
    source_ip: Optional[str] = None,
    ap_id: Optional[str] = None,
    simulated: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    sort: str = Query("desc", pattern="^(asc|desc)$"),
):
    q = select(NetworkEvent)
    if event_type:
        q = q.where(NetworkEvent.event_type == event_type)
    if source_ip:
        q = q.where(NetworkEvent.source_ip == source_ip)
    if ap_id:
        q = q.where(NetworkEvent.ap_id == ap_id)
    if simulated is not None:
        q = q.where(NetworkEvent.simulated == simulated)
    if since:
        q = q.where(NetworkEvent.timestamp_utc >= since)
    if until:
        q = q.where(NetworkEvent.timestamp_utc <= until)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    order = desc(NetworkEvent.timestamp_utc) if sort == "desc" else NetworkEvent.timestamp_utc
    q = q.order_by(order).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    events = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_serialize_event(e) for e in events],
    }


@router.get("/{event_id}")
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NetworkEvent).where(NetworkEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _serialize_event(event)


def _serialize_event(e: NetworkEvent) -> dict:
    return {
        "id": e.id,
        "timestamp_utc": e.timestamp_utc.isoformat() if e.timestamp_utc else None,
        "event_type": e.event_type,
        "source_type": e.source_type,
        "source_ip": e.source_ip,
        "source_port": e.source_port,
        "destination_ip": e.destination_ip,
        "destination_port": e.destination_port,
        "protocol": e.protocol,
        "domain": e.domain,
        "dns_record_type": e.dns_record_type,
        "dns_response_code": e.dns_response_code,
        "ap_id": e.ap_id,
        "switch_id": e.switch_id,
        "switch_port": e.switch_port,
        "vlan_id": e.vlan_id,
        "username": e.username,
        "authentication_result": e.authentication_result,
        "bytes_sent": e.bytes_sent,
        "bytes_received": e.bytes_received,
        "packets": e.packets,
        "client_mac": e.client_mac,
        "simulated": e.simulated,
        "extra_metadata": e.extra_metadata,
    }
