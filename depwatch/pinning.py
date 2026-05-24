"""Pinning advisor: suggests exact version pins based on current latest releases."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


@dataclass
class PinSuggestion:
    project: str
    package: str
    language: str
    current: str
    suggested_pin: str  # e.g. "requests==2.31.0" or "github.com/gin-gonic/gin v1.9.1"

    def __str__(self) -> str:
        return (
            f"[{self.project}] {self.package}: pin to {self.suggested_pin} "
            f"(currently {self.current!r})"
        )

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "language": self.language,
            "current": self.current,
            "suggested_pin": self.suggested_pin,
        }


def _format_pin(language: str, package: str, version: str) -> str:
    """Return a canonical pin string for the given language ecosystem."""
    if language == "python":
        return f"{package}=={version}"
    if language == "go":
        return f"{package} v{version.lstrip('v')}"
    return f"{package}@{version}"


def build_pin_suggestions(digests: List[ProjectDigest]) -> List[PinSuggestion]:
    """Return one PinSuggestion per outdated package across all project digests."""
    suggestions: List[PinSuggestion] = []
    for digest in digests:
        for update in digest.updates:
            pin = _format_pin(update.language, update.package, update.latest_version)
            suggestions.append(
                PinSuggestion(
                    project=digest.project_name,
                    package=update.package,
                    language=update.language,
                    current=update.current_version,
                    suggested_pin=pin,
                )
            )
    return suggestions


def suggestions_to_text(suggestions: List[PinSuggestion]) -> str:
    """Render suggestions as a human-readable block."""
    if not suggestions:
        return "No pin suggestions — all dependencies are up to date."
    lines = ["Pin suggestions:", ""]
    for s in suggestions:
        lines.append(f"  {s}")
    return "\n".join(lines)
