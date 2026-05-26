"""Confidence scoring for dependency updates based on release signals."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


@dataclass
class ConfidenceScore:
    project: str
    package: str
    language: str
    current_version: str
    latest_version: str
    score: float  # 0.0 – 1.0
    reasons: List[str]

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "language": self.language,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "score": round(self.score, 3),
            "reasons": self.reasons,
        }

    def __str__(self) -> str:
        pct = int(self.score * 100)
        return f"{self.package} ({self.project}): {pct}% confidence — {'; '.join(self.reasons)}"


@dataclass
class ConfidenceReport:
    entries: List[ConfidenceScore]

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}


def _score_update(update: UpdateInfo) -> ConfidenceScore:
    """Compute a confidence score for a single update."""
    score = 0.5
    reasons: List[str] = []

    current = update.current_version or ""
    latest = update.latest_version or ""

    # Penalise if current version is unknown/unpinned
    if not current or current in ("unknown", ""):
        score -= 0.15
        reasons.append("current version unpinned")
    else:
        score += 0.1
        reasons.append("current version pinned")

    # Reward stable-looking semver releases (no pre-release markers)
    pre_markers = ("alpha", "beta", "rc", "dev", "pre", "a", "b")
    if any(m in latest.lower() for m in pre_markers):
        score -= 0.2
        reasons.append("latest is a pre-release")
    else:
        score += 0.15
        reasons.append("latest is a stable release")

    # Reward Go modules (typically well-versioned)
    if update.language == "go":
        score += 0.05
        reasons.append("Go module")

    score = max(0.0, min(1.0, score))
    return ConfidenceScore(
        project=update.project,
        package=update.package,
        language=update.language,
        current_version=current,
        latest_version=latest,
        score=score,
        reasons=reasons,
    )


def build_confidence_report(digests: List[ProjectDigest]) -> ConfidenceReport:
    entries: List[ConfidenceScore] = []
    for digest in digests:
        for update in digest.updates:
            entries.append(_score_update(update))
    entries.sort(key=lambda e: e.score, reverse=True)
    return ConfidenceReport(entries=entries)
