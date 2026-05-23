"""Persistent history of dependency updates for trend tracking."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class HistoryEntry:
    project: str
    package: str
    language: str
    from_version: Optional[str]
    to_version: str
    detected_at: str  # ISO-8601

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "HistoryEntry":
        return HistoryEntry(**d)


def _load_raw(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


def load_history(path: str) -> List[HistoryEntry]:
    """Load all history entries from *path*."""
    return [HistoryEntry.from_dict(d) for d in _load_raw(path)]


def append_entry(path: str, entry: HistoryEntry) -> None:
    """Append a single entry to the history file, creating it if needed."""
    raw = _load_raw(path)
    raw.append(entry.to_dict())
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(raw, fh, indent=2)


def record_updates(path: str, project: str, language: str, updates: list) -> None:
    """Bulk-record a list of UpdateInfo objects into history."""
    now = datetime.now(timezone.utc).isoformat()
    for upd in updates:
        entry = HistoryEntry(
            project=project,
            package=upd.package,
            language=language,
            from_version=upd.current_version,
            to_version=upd.latest_version,
            detected_at=now,
        )
        append_entry(path, entry)
