"""
NetSentinel Pytest Configuration and Fixtures.
Provides transparent fallback to in-memory ASGITransport when the live backend is not running.
"""

import socket
import pytest
import httpx
from backend.app.main import app


def _is_backend_live(host: str = "127.0.0.1", port: int = 8000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.15):
            return True
    except OSError:
        return False


@pytest.fixture(autouse=True)
def _ensure_httpx_transport(monkeypatch):
    """If backend is not running on 127.0.0.1:8000, route requests via ASGITransport."""
    if not _is_backend_live():
        original_init = httpx.AsyncClient.__init__

        def patched_init(self, *args, **kwargs):
            if "transport" not in kwargs:
                kwargs["transport"] = httpx.ASGITransport(app=app)
            original_init(self, *args, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)
