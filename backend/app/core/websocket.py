"""
NetSentinel — WebSocket Connection Manager.

Manages all active WebSocket connections and broadcasts
real-time event/alert updates to authorized clients.
"""

from __future__ import annotations
import asyncio
import json
import logging
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Thread-safe WebSocket connection manager with bounded broadcast queue."""

    def __init__(self, max_queue_size: int = 500):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._broadcast_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("WebSocket client connected. Total: %d", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("WebSocket client disconnected. Total: %d", len(self._connections))

    async def broadcast(self, message: dict) -> None:
        """Enqueue a message for broadcasting. Drops oldest if queue is full (backpressure)."""
        try:
            self._broadcast_queue.put_nowait(message)
        except asyncio.QueueFull:
            # Drop oldest to avoid unbounded memory growth
            try:
                self._broadcast_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            self._broadcast_queue.put_nowait(message)

    async def broadcast_loop(self) -> None:
        """Background task that drains the queue and sends to all connected clients."""
        while True:
            message = await self._broadcast_queue.get()
            data = json.dumps(message, default=str)
            dead: Set[WebSocket] = set()
            async with self._lock:
                connections = set(self._connections)
            for ws in connections:
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                await self.disconnect(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Singleton instance
ws_manager = WebSocketManager()
