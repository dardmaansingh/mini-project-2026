"""
HTTP Webhook Alert Dispatcher.

Academic Context (Computer Networks & Distributed Systems):
- Asynchronously notifies external receivers via standard HTTP POST with JSON payloads.
- Modular architecture allowing mock/local testing without external dependencies.
- Defensive network design with connection timeouts and failure absorption.
"""

import json
import logging
from typing import Dict, Any, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class WebhookDispatcher:
    """
    Sends structured alert notifications over HTTP/REST.
    """

    def __init__(self, webhook_url: Optional[str] = None, timeout: float = 2.0, enabled: bool = True):
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.enabled = enabled
        self.dispatched_count = 0
        self.failed_count = 0

    def dispatch(self, alert_payload: Dict[str, Any]) -> bool:
        """
        Dispatches alert dictionary via HTTP POST.
        Returns True if successful (status 2xx) or if in mock mode.
        """
        if not self.enabled or not self.webhook_url:
            return False

        if not REQUESTS_AVAILABLE:
            self.failed_count += 1
            return False

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Zeek-Traffic-Monitor-Webhook/1.0",
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=alert_payload,
                headers=headers,
                timeout=self.timeout,
            )
            if 200 <= response.status_code < 300:
                self.dispatched_count += 1
                return True
            else:
                self.failed_count += 1
                return False
        except Exception:
            self.failed_count += 1
            return False
