"""Webhook notifier: sends digest payloads to HTTP endpoints."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from depwatch.notifier import DigestPayload

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    url: str
    secret: Optional[str] = None
    timeout: int = 10
    extra_headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"webhook url must start with http:// or https://, got: {self.url!r}")
        if self.timeout < 1:
            raise ValueError(f"webhook timeout must be >= 1, got: {self.timeout}")


def _build_body(payload: DigestPayload) -> bytes:
    """Serialise the digest payload to a JSON body."""
    data: Dict[str, Any] = {
        "projects": [
            {
                "project": u.project,
                "package": u.package,
                "current_version": u.current_version,
                "latest_version": u.latest_version,
            }
            for u in payload.updates
        ]
    }
    return json.dumps(data).encode()


def send_webhook(config: WebhookConfig, payload: DigestPayload) -> bool:
    """POST the digest payload to the configured webhook URL.

    Returns True on success, False on any network or HTTP error.
    """
    if payload.is_empty():
        logger.debug("webhook: payload is empty, skipping")
        return True

    body = _build_body(payload)
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        **config.extra_headers,
    }
    if config.secret:
        headers["X-DepWatch-Secret"] = config.secret

    req = urllib.request.Request(config.url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=config.timeout) as resp:
            status = resp.status
            logger.info("webhook: POST %s -> HTTP %d", config.url, status)
            return 200 <= status < 300
    except urllib.error.HTTPError as exc:
        logger.error("webhook: HTTP error %d for %s: %s", exc.code, config.url, exc.reason)
        return False
    except urllib.error.URLError as exc:
        logger.error("webhook: network error for %s: %s", config.url, exc.reason)
        return False
