"""Risk scoring for dependency updates.

Combines multiple signals (bump level, staleness, popularity, pre-release
status, and whether the package is unpinned) into a single risk score and
bucket (low / medium / high / critical) for each pending update.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.filter import _bump_level  # reuse existing bump-level logic

# ---------------------------------------------------------------------------
# Risk buckets
# ---------------------------------------------------------------------------

LOW = "low"
MEDIUM = "medium"
HIGH = "high"
CRITICAL = "critical"

_BUCKET_ORDER = [LOW, MEDIUM, HIGH, CRITICAL]


def _bucket(score: float) -> str:
    """Map a numeric score (0–100) to a named risk bucket."""
    if score >= 75:
        return CRITICAL
    if score >= 50:
        return HIGH
    if score >= 25:
        return MEDIUM
    return LOW


# ---------------------------------------------------------------------------
# Per-update risk entry
# ---------------------------------------------------------------------------

@dataclass
class RiskEntry:
    project: str
    package: str
    current_version: str
    latest_version: str
    language: str
    bump_level: str          # major / minor / patch / unknown
    is_pre_release: bool
    is_unpinned: bool
    score: float             # 0–100
    bucket: str              # low / medium / high / critical
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "language": self.language,
            "bump_level": self.bump_level,
            "is_pre_release": self.is_pre_release,
            "is_unpinned": self.is_unpinned,
            "score": round(self.score, 2),
            "bucket": self.bucket,
            "reasons": self.reasons,
        }

    def __str__(self) -> str:
        return (
            f"[{self.bucket.upper()}] {self.project}/{self.package} "
            f"{self.current_version} -> {self.latest_version} "
            f"(score={self.score:.0f})"
        )


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------

def _is_pre_release(version: str) -> bool:
    """Heuristic: any version containing a-, b-, rc-, dev-, alpha, beta."""
    lower = version.lower()
    return any(tag in lower for tag in ("a", "b", "rc", "dev", "alpha", "beta", ".post"))


def score_update(update: UpdateInfo, project: str) -> RiskEntry:
    """Compute a risk entry for a single UpdateInfo."""
    reasons: List[str] = []
    score = 0.0

    bump = _bump_level(update.current_version, update.latest_version)

    # Bump-level contribution (0 / 20 / 40 / 60)
    bump_scores = {"major": 60, "minor": 20, "patch": 10, "unknown": 30}
    bump_score = bump_scores.get(bump, 30)
    if bump_score:
        score += bump_score
        reasons.append(f"{bump} version bump (+{bump_score})")

    # Pre-release penalty: using a pre-release latest is risky
    pre = _is_pre_release(update.latest_version)
    if pre:
        score += 20
        reasons.append("latest is a pre-release (+20)")

    # Unpinned current version means the running version is ambiguous
    unpinned = update.current_version in ("", "unpinned", "*", "latest")
    if unpinned:
        score += 15
        reasons.append("current version is unpinned (+15)")

    score = min(score, 100.0)

    return RiskEntry(
        project=project,
        package=update.package,
        current_version=update.current_version,
        latest_version=update.latest_version,
        language=update.language,
        bump_level=bump,
        is_pre_release=pre,
        is_unpinned=unpinned,
        score=score,
        bucket=_bucket(score),
        reasons=reasons,
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

@dataclass
class RiskReport:
    entries: List[RiskEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def by_bucket(self, bucket: str) -> List[RiskEntry]:
        return [e for e in self.entries if e.bucket == bucket]

    def to_dict(self) -> dict:
        buckets: dict = {b: [] for b in _BUCKET_ORDER}
        for entry in self.entries:
            buckets[entry.bucket].append(entry.to_dict())
        return {
            "total": len(self.entries),
            "buckets": {b: len(buckets[b]) for b in _BUCKET_ORDER},
            "entries": [e.to_dict() for e in self.entries],
        }


def build_risk_report(digests: Sequence[ProjectDigest]) -> RiskReport:
    """Build a RiskReport from a collection of ProjectDigests."""
    entries: List[RiskEntry] = []
    for digest in digests:
        for update in digest.updates:
            entries.append(score_update(update, digest.project_name))
    # Sort: critical first, then by score descending
    entries.sort(key=lambda e: (_BUCKET_ORDER.index(e.bucket), -e.score), reverse=True)
    return RiskReport(entries=entries)
