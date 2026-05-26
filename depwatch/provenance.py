"""Provenance tracking: record where each update was first detected."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from depwatch.checker import UpdateInfo


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProvenanceEntry:
    project: str
    package: str
    language: str
    first_seen: str
    latest_version: str
    source: str  # e.g. "pypi", "goproxy"

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "language": self.language,
            "first_seen": self.first_seen,
            "latest_version": self.latest_version,
            "source": self.source,
        }

    @staticmethod
    def from_dict(d: dict) -> "ProvenanceEntry":
        return ProvenanceEntry(
            project=d["project"],
            package=d["package"],
            language=d["language"],
            first_seen=d["first_seen"],
            latest_version=d["latest_version"],
            source=d.get("source", "unknown"),
        )


def _entry_key(project: str, package: str) -> str:
    return f"{project}::{package.lower()}"


def _source_for(language: str) -> str:
    return "pypi" if language == "python" else "goproxy"


def load_provenance(path: Path) -> Dict[str, ProvenanceEntry]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict):
            return {}
        return {k: ProvenanceEntry.from_dict(v) for k, v in raw.items()}
    except (json.JSONDecodeError, KeyError):
        return {}


def save_provenance(path: Path, store: Dict[str, ProvenanceEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: v.to_dict() for k, v in store.items()}, indent=2))


def record_provenance(
    updates: List[UpdateInfo],
    store: Dict[str, ProvenanceEntry],
    now: Optional[str] = None,
) -> Dict[str, ProvenanceEntry]:
    ts = now or _now_iso()
    for u in updates:
        key = _entry_key(u.project, u.package)
        if key not in store:
            store[key] = ProvenanceEntry(
                project=u.project,
                package=u.package,
                language=u.language,
                first_seen=ts,
                latest_version=u.latest,
                source=_source_for(u.language),
            )
    return store
