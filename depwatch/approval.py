"""Approval workflow: track which updates have been approved or rejected."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from depwatch.checker import UpdateInfo

_DEFAULT_PATH = Path("depwatch_approvals.json")


@dataclass
class ApprovalRecord:
    project: str
    package: str
    version: str
    status: str  # "approved" | "rejected" | "pending"
    author: str = "depwatch"
    note: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "version": self.version,
            "status": self.status,
            "author": self.author,
            "note": self.note,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovalRecord":
        return cls(
            project=data["project"],
            package=data["package"],
            version=data["version"],
            status=data["status"],
            author=data.get("author", "depwatch"),
            note=data.get("note", ""),
            timestamp=data.get("timestamp", ""),
        )


def _record_key(project: str, package: str, version: str) -> str:
    return f"{project}::{package}::{version}"


def load_approvals(path: Path = _DEFAULT_PATH) -> Dict[str, ApprovalRecord]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
        if not isinstance(raw, list):
            return {}
        result: Dict[str, ApprovalRecord] = {}
        for item in raw:
            rec = ApprovalRecord.from_dict(item)
            key = _record_key(rec.project, rec.package, rec.version)
            result[key] = rec
        return result
    except (json.JSONDecodeError, KeyError):
        return {}


def save_approvals(records: Dict[str, ApprovalRecord], path: Path = _DEFAULT_PATH) -> None:
    path.write_text(json.dumps([r.to_dict() for r in records.values()], indent=2))


def set_approval(
    update: UpdateInfo,
    status: str,
    author: str = "depwatch",
    note: str = "",
    path: Path = _DEFAULT_PATH,
) -> ApprovalRecord:
    if status not in ("approved", "rejected", "pending"):
        raise ValueError(f"Invalid status: {status!r}")
    records = load_approvals(path)
    rec = ApprovalRecord(
        project=update.project,
        package=update.package,
        version=update.latest,
        status=status,
        author=author,
        note=note,
    )
    records[_record_key(rec.project, rec.package, rec.version)] = rec
    save_approvals(records, path)
    return rec


def get_status(
    update: UpdateInfo, path: Path = _DEFAULT_PATH
) -> Optional[ApprovalRecord]:
    records = load_approvals(path)
    return records.get(_record_key(update.project, update.package, update.latest))


def filter_unapproved(
    updates: List[UpdateInfo], path: Path = _DEFAULT_PATH
) -> List[UpdateInfo]:
    """Return only updates that are NOT explicitly approved."""
    records = load_approvals(path)
    return [
        u for u in updates
        if records.get(_record_key(u.project, u.package, u.latest), None) is None
        or records[_record_key(u.project, u.package, u.latest)].status != "approved"
    ]
