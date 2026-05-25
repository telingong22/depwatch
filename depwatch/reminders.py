"""Reminder tracking: flag packages that have been pending update for too long."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from depwatch.checker import UpdateInfo

_DEFAULT_REMINDER_DAYS = 7


@dataclass
class ReminderEntry:
    project: str
    package: str
    language: str
    latest: str
    first_seen: str  # ISO-8601
    reminder_days: int = _DEFAULT_REMINDER_DAYS

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "language": self.language,
            "latest": self.latest,
            "first_seen": self.first_seen,
            "reminder_days": self.reminder_days,
        }

    @staticmethod
    def from_dict(d: dict) -> "ReminderEntry":
        return ReminderEntry(
            project=d["project"],
            package=d["package"],
            language=d["language"],
            latest=d["latest"],
            first_seen=d["first_seen"],
            reminder_days=int(d.get("reminder_days", _DEFAULT_REMINDER_DAYS)),
        )

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        try:
            seen = datetime.fromisoformat(self.first_seen)
        except ValueError:
            return False
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
        return (now - seen).days >= self.reminder_days


def _reminder_key(project: str, package: str) -> str:
    return f"{project}::{package}"


def load_reminders(path: Path) -> Dict[str, ReminderEntry]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(raw, dict):
        return {}
    result: Dict[str, ReminderEntry] = {}
    for k, v in raw.items():
        try:
            result[k] = ReminderEntry.from_dict(v)
        except (KeyError, TypeError):
            continue
    return result


def save_reminders(path: Path, store: Dict[str, ReminderEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: v.to_dict() for k, v in store.items()}, indent=2))


def record_reminders(
    path: Path,
    updates: List[UpdateInfo],
    reminder_days: int = _DEFAULT_REMINDER_DAYS,
    now: Optional[datetime] = None,
) -> Dict[str, ReminderEntry]:
    now = now or datetime.now(timezone.utc)
    store = load_reminders(path)
    for u in updates:
        key = _reminder_key(u.project, u.package)
        if key not in store or store[key].latest != u.latest:
            store[key] = ReminderEntry(
                project=u.project,
                package=u.package,
                language=u.language,
                latest=u.latest,
                first_seen=now.isoformat(),
                reminder_days=reminder_days,
            )
    save_reminders(path, store)
    return store


def get_overdue(store: Dict[str, ReminderEntry], now: Optional[datetime] = None) -> List[ReminderEntry]:
    return [e for e in store.values() if e.is_overdue(now)]
