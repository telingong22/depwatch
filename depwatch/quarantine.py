"""Quarantine: temporarily hold updates that require manual review before acting on them."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from depwatch.checker import UpdateInfo


@dataclass
class QuarantineEntry:
    project: str
    package: str
    current: str
    latest: str
    language: str
    reason: str
    quarantined_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    released_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "current": self.current,
            "latest": self.latest,
            "language": self.language,
            "reason": self.reason,
            "quarantined_at": self.quarantined_at,
            "released_at": self.released_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "QuarantineEntry":
        return QuarantineEntry(
            project=d["project"],
            package=d["package"],
            current=d["current"],
            latest=d["latest"],
            language=d["language"],
            reason=d["reason"],
            quarantined_at=d.get("quarantined_at", ""),
            released_at=d.get("released_at"),
        )


def _entry_key(project: str, package: str, latest: str) -> str:
    return f"{project}::{package}::{latest}"


def load_quarantine(path: str) -> Dict[str, QuarantineEntry]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if not isinstance(raw, dict):
            return {}
        return {k: QuarantineEntry.from_dict(v) for k, v in raw.items()}
    except (json.JSONDecodeError, KeyError):
        return {}


def save_quarantine(path: str, store: Dict[str, QuarantineEntry]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({k: v.to_dict() for k, v in store.items()}, fh, indent=2)


def quarantine_update(update: UpdateInfo, reason: str, path: str) -> QuarantineEntry:
    store = load_quarantine(path)
    key = _entry_key(update.project, update.package, update.latest)
    entry = QuarantineEntry(
        project=update.project,
        package=update.package,
        current=update.current,
        latest=update.latest,
        language=update.language,
        reason=reason,
    )
    store[key] = entry
    save_quarantine(path, store)
    return entry


def release_from_quarantine(project: str, package: str, latest: str, path: str) -> bool:
    store = load_quarantine(path)
    key = _entry_key(project, package, latest)
    if key not in store:
        return False
    store[key].released_at = datetime.now(timezone.utc).isoformat()
    save_quarantine(path, store)
    return True


def list_active(path: str) -> List[QuarantineEntry]:
    return [e for e in load_quarantine(path).values() if e.released_at is None]
