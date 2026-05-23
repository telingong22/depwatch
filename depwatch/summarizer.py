"""Summarizer: produce a human-readable summary of a digest payload."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.notifier import DigestPayload
from depwatch.digest import ProjectDigest
from depwatch.checker import UpdateInfo


@dataclass
class SummaryLine:
    project: str
    package: str
    current: str
    latest: str
    language: str

    def __str__(self) -> str:
        return (
            f"[{self.language}] {self.project} — "
            f"{self.package}: {self.current} → {self.latest}"
        )


@dataclass
class Summary:
    lines: List[SummaryLine]

    def is_empty(self) -> bool:
        return len(self.lines) == 0

    def to_text(self) -> str:
        if self.is_empty():
            return "No updates found."
        header = f"depwatch: {len(self.lines)} update(s) available\n"
        separator = "-" * 40 + "\n"
        body = "\n".join(str(line) for line in self.lines)
        return header + separator + body

    def to_dict(self) -> dict:
        return {
            "total": len(self.lines),
            "updates": [
                {
                    "project": l.project,
                    "package": l.package,
                    "current": l.current,
                    "latest": l.latest,
                    "language": l.language,
                }
                for l in self.lines
            ],
        }


def _lines_from_digest(digest: ProjectDigest) -> List[SummaryLine]:
    lines: List[SummaryLine] = []
    for update in digest.updates:
        lines.append(
            SummaryLine(
                project=digest.project_name,
                package=update.package,
                current=update.current_version or "unknown",
                latest=update.latest_version,
                language=digest.language,
            )
        )
    return lines


def build_summary(payload: DigestPayload) -> Summary:
    """Build a Summary from a DigestPayload."""
    lines: List[SummaryLine] = []
    for digest in payload.digests:
        lines.extend(_lines_from_digest(digest))
    return Summary(lines=lines)
