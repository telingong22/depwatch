"""Alert/notification module for sending dependency update digests."""

from __future__ import annotations

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import List

from depwatch.checker import UpdateInfo
from depwatch.config import AlertConfig

logger = logging.getLogger(__name__)


@dataclass
class DigestPayload:
    """Holds a list of updates to be sent as a digest."""
    updates: List[UpdateInfo]

    def is_empty(self) -> bool:
        return len(self.updates) == 0

    def format_text(self) -> str:
        if self.is_empty():
            return "No dependency updates found."
        lines = ["Dependency Update Digest", "=" * 40]
        for u in self.updates:
            lines.append(str(u))
        return "\n".join(lines)


def send_email_digest(payload: DigestPayload, config: AlertConfig) -> bool:
    """Send a digest email via SMTP.

    Returns True on success, False on failure.
    """
    if payload.is_empty():
        logger.info("No updates to report; skipping email.")
        return False

    smtp_host = config.smtp_host or "localhost"
    smtp_port = config.smtp_port or 25
    sender = config.sender or "depwatch@localhost"
    target = config.target

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "depwatch: dependency update digest"
    msg["From"] = sender
    msg["To"] = target

    body = payload.format_text()
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.sendmail(sender, [target], msg.as_string())
        logger.info("Digest sent to %s", target)
        return True
    except (smtplib.SMTPException, OSError) as exc:
        logger.error("Failed to send digest email: %s", exc)
        return False


def notify(payload: DigestPayload, config: AlertConfig) -> bool:
    """Dispatch a digest notification according to the alert config."""
    method = (config.method or "email").lower()
    if method == "email":
        return send_email_digest(payload, config)
    logger.warning("Unknown notification method '%s'; skipping.", method)
    return False
