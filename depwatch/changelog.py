"""Fetch and parse changelog/release notes URLs for packages."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import urllib.request
import urllib.error
import json


@dataclass
class ChangelogInfo:
    package: str
    language: str
    version: str
    url: Optional[str]
    summary: Optional[str]

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "language": self.language,
            "version": self.version,
            "url": self.url,
            "summary": self.summary,
        }


def _pypi_changelog_url(package: str, version: str) -> Optional[str]:
    """Return the PyPI project URL for the given package/version, or None."""
    api_url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        with urllib.request.urlopen(api_url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        urls = data.get("info", {}).get("project_urls") or {}
        for key in ("Changelog", "changelog", "Release Notes", "Changes"):
            if key in urls:
                return urls[key]
        return data.get("info", {}).get("home_page") or None
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None


def _go_changelog_url(module: str, version: str) -> Optional[str]:
    """Return a best-effort GitHub releases URL for a Go module."""
    # Strip leading v from version for display
    parts = module.split("/")
    if len(parts) >= 3 and parts[0] == "github.com":
        owner, repo = parts[1], parts[2]
        tag = version if version.startswith("v") else f"v{version}"
        return f"https://github.com/{owner}/{repo}/releases/tag/{tag}"
    return None


def fetch_changelog(package: str, language: str, version: str) -> ChangelogInfo:
    """Fetch changelog metadata for a package at a given version."""
    if language == "python":
        url = _pypi_changelog_url(package, version)
    elif language == "go":
        url = _go_changelog_url(package, version)
    else:
        url = None

    return ChangelogInfo(
        package=package,
        language=language,
        version=version,
        url=url,
        summary=None,
    )


def fetch_changelogs_for_updates(updates: list) -> list[ChangelogInfo]:
    """Return ChangelogInfo for each UpdateInfo in *updates*."""
    results: list[ChangelogInfo] = []
    for upd in updates:
        info = fetch_changelog(
            package=upd.package,
            language=upd.language,
            version=upd.latest,
        )
        results.append(info)
    return results
