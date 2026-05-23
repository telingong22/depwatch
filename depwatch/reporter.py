"""Reporter module: formats and writes human-readable summary reports to disk."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from depwatch.digest import ProjectDigest


@dataclass
class ReportEntry:
    project: str
    package: str
    current_version: str
    latest_version: str
    published_at: str


@dataclass
class Report:
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    entries: List[ReportEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "entries": [
                {
                    "project": e.project,
                    "package": e.package,
                    "current_version": e.current_version,
                    "latest_version": e.latest_version,
                    "published_at": e.published_at,
                }
                for e in self.entries
            ],
        }


def build_report(digests: List[ProjectDigest]) -> Report:
    """Build a Report from a list of ProjectDigests."""
    report = Report()
    for digest in digests:
        for update in digest.updates:
            report.entries.append(
                ReportEntry(
                    project=digest.project_name,
                    package=update.package,
                    current_version=update.current_version,
                    latest_version=update.latest_version,
                    published_at=update.published_at or "",
                )
            )
    return report


def write_report(report: Report, path: str) -> None:
    """Serialise *report* as JSON and write it to *path*, creating parent dirs."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report.to_dict(), fh, indent=2)


def format_report_text(report: Report) -> str:
    """Return a plain-text summary suitable for logging or stdout."""
    if report.is_empty():
        return "No dependency updates found."
    lines = [f"Dependency update report ({report.generated_at}):", ""]
    for entry in report.entries:
        lines.append(
            f"  [{entry.project}] {entry.package}: "
            f"{entry.current_version} -> {entry.latest_version}"
            + (f"  (released {entry.published_at})" if entry.published_at else "")
        )
    return "\n".join(lines)
