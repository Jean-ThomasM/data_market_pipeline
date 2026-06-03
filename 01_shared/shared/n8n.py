import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class N8nClient:
    def __init__(self, webhook_url: str):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.webhook_url = webhook_url.rstrip("/")

    def trigger_workflow(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        resp = self.session.post(self.webhook_url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
