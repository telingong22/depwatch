"""Audit log: records every alert/notification action taken by depwatch."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_AUDIT_PATH = Path("depwatch_audit.json")


@dataclass
class AuditEntry:
    timestamp: str
    action: str          # e.g. "email_sent", "webhook_sent", "suppressed"
    project: str
    package: str
    current_version: str
    latest_version: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "project": self.project,
            "package": self.package,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AuditEntry":
        return cls(
            timestamp=d["timestamp"],
            action=d["action"],
            project=d["project"],
            package=d["package"],
            current_version=d["current_version"],
            latest_version=d["latest_version"],
            detail=d.get("detail", ""),
        )


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def load_audit(path: Path = DEFAULT_AUDIT_PATH) -> List[AuditEntry]:
    return [AuditEntry.from_dict(d) for d in _load_raw(path)]


def append_audit(entry: AuditEntry, path: Path = DEFAULT_AUDIT_PATH) -> None:
    entries = _load_raw(path)
    entries.append(entry.to_dict())
    path.write_text(json.dumps(entries, indent=2))


def record_action(
    action: str,
    project: str,
    package: str,
    current_version: str,
    latest_version: str,
    detail: str = "",
    path: Path = DEFAULT_AUDIT_PATH,
) -> AuditEntry:
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        action=action,
        project=project,
        package=package,
        current_version=current_version,
        latest_version=latest_version,
        detail=detail,
    )
    append_audit(entry, path)
    return entry
