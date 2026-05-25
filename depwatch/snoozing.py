"""Snoozed-update management: temporarily silence an update until a future date."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from depwatch.checker import UpdateInfo

_DEFAULT_PATH = Path("depwatch_snooze.json")


def _snooze_key(project: str, package: str) -> str:
    return f"{project}::{package}"


@dataclass
class SnoozeEntry:
    project: str
    package: str
    until: str  # ISO-8601 datetime string
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "until": self.until,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnoozeEntry":
        return cls(
            project=data["project"],
            package=data["package"],
            until=data["until"],
            reason=data.get("reason", ""),
        )

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if the snooze is still in effect."""
        if now is None:
            now = datetime.now(timezone.utc)
        try:
            until_dt = datetime.fromisoformat(self.until)
        except ValueError:
            return False
        if until_dt.tzinfo is None:
            until_dt = until_dt.replace(tzinfo=timezone.utc)
        return now < until_dt


def _load_raw(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def load_snoozes(path: Path = _DEFAULT_PATH) -> Dict[str, SnoozeEntry]:
    raw = _load_raw(path)
    result: Dict[str, SnoozeEntry] = {}
    for key, value in raw.items():
        try:
            result[key] = SnoozeEntry.from_dict(value)
        except (KeyError, TypeError):
            continue
    return result


def save_snoozes(snoozes: Dict[str, SnoozeEntry], path: Path = _DEFAULT_PATH) -> None:
    path.write_text(json.dumps({k: v.to_dict() for k, v in snoozes.items()}, indent=2))


def add_snooze(project: str, package: str, until: str, reason: str = "",
               path: Path = _DEFAULT_PATH) -> SnoozeEntry:
    snoozes = load_snoozes(path)
    entry = SnoozeEntry(project=project, package=package, until=until, reason=reason)
    snoozes[_snooze_key(project, package)] = entry
    save_snoozes(snoozes, path)
    return entry


def apply_snoozes(updates: List[UpdateInfo], path: Path = _DEFAULT_PATH,
                  now: Optional[datetime] = None) -> List[UpdateInfo]:
    """Return only updates that are NOT currently snoozed."""
    snoozes = load_snoozes(path)
    return [
        u for u in updates
        if not _is_snoozed(u, snoozes, now)
    ]


def _is_snoozed(update: UpdateInfo, snoozes: Dict[str, SnoozeEntry],
                now: Optional[datetime]) -> bool:
    key = _snooze_key(update.project_name, update.package_name)
    entry = snoozes.get(key)
    return entry is not None and entry.is_active(now)
