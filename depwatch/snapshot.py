"""Snapshot: captures and compares dependency state across runs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class SnapshotEntry:
    package: str
    version: str
    captured_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "version": self.version,
            "captured_at": self.captured_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnapshotEntry":
        return cls(
            package=data["package"],
            version=data["version"],
            captured_at=data.get("captured_at", ""),
        )


@dataclass
class Snapshot:
    project: str
    entries: List[SnapshotEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            project=data["project"],
            entries=[SnapshotEntry.from_dict(e) for e in data.get("entries", [])],
        )


def load_snapshot(path: str) -> Optional[Snapshot]:
    """Load a snapshot from a JSON file; return None if missing or invalid."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return None
        return Snapshot.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None


def save_snapshot(path: str, snapshot: Snapshot) -> None:
    """Persist a snapshot to a JSON file, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def diff_snapshots(
    old: Optional[Snapshot], new: Snapshot
) -> Dict[str, tuple]:
    """Return packages whose version changed between snapshots.

    Returns a dict of {package: (old_version_or_None, new_version)}.
    """
    old_map: Dict[str, str] = (
        {e.package: e.version for e in old.entries} if old else {}
    )
    new_map: Dict[str, str] = {e.package: e.version for e in new.entries}

    changed: Dict[str, tuple] = {}
    for pkg, ver in new_map.items():
        prev = old_map.get(pkg)
        if prev != ver:
            changed[pkg] = (prev, ver)
    return changed
