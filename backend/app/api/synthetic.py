"""NetSentinel API — Synthetic generator control endpoints."""

from fastapi import APIRouter, HTTPException, Body
from typing import Optional

router = APIRouter(prefix="/api/synthetic", tags=["synthetic"])

# Will be injected at startup
_generator = None


def set_generator(gen) -> None:
    global _generator
    _generator = gen


@router.get("/status")
async def status():
    if not _generator:
        return {"running": False, "paused": False, "events_per_second": 0, "anomaly_rate": 0}
    return {
        "running": _generator.running,
        "paused": _generator.paused,
        "events_per_second": _generator._events_per_second,
        "anomaly_rate": _generator._anomaly_rate,
    }


@router.post("/pause")
async def pause():
    if not _generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    _generator.pause()
    return {"status": "paused"}


@router.post("/resume")
async def resume():
    if not _generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    _generator.resume()
    return {"status": "resumed"}


@router.post("/rate")
async def set_rate(events_per_second: float = Body(..., embed=True)):
    if not _generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    _generator.set_rate(events_per_second)
    return {"events_per_second": _generator._events_per_second}


@router.post("/trigger/port-scan")
async def trigger_port_scan():
    if not _generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    events = await _generator.trigger_port_scan()
    return {"triggered": "port_scan", "events_generated": len(events)}


@router.post("/trigger/dns-spike")
async def trigger_dns_spike(count: int = Body(60, embed=True)):
    if not _generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    events = await _generator.trigger_dns_spike(count=count)
    return {"triggered": "dns_spike", "events_generated": len(events)}


@router.post("/trigger/brute-force")
async def trigger_brute_force(count: int = Body(20, embed=True)):
    if not _generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    events = await _generator.trigger_brute_force(count=count)
    return {"triggered": "brute_force", "events_generated": len(events)}


@router.post("/trigger/bandwidth-anomaly")
async def trigger_bandwidth():
    if not _generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    await _generator.trigger_bandwidth_anomaly()
    return {"triggered": "bandwidth_anomaly"}
