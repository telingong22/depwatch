"""Dependency version checker: compares current vs latest versions."""

from dataclasses import dataclass
from typing import Optional
from packaging.version import Version, InvalidVersion

from depwatch.config import ProjectConfig
from depwatch.fetcher import ReleaseInfo, fetch_latest


@dataclass
class UpdateInfo:
    package: str
    current_version: str
    latest_version: str
    release_url: str
    is_outdated: bool

    def __str__(self) -> str:
        status = "outdated" if self.is_outdated else "up-to-date"
        return (
            f"{self.package} [{status}]: "
            f"current={self.current_version}, latest={self.latest_version}"
        )


def _is_newer(current: str, latest: str) -> bool:
    """Return True if latest is strictly newer than current."""
    try:
        return Version(latest) > Version(current)
    except InvalidVersion:
        return latest != current


def check_package(
    package: str,
    current_version: str,
    language: str,
) -> Optional[UpdateInfo]:
    """Fetch the latest release and compare with current_version.

    Returns None if the latest release cannot be determined.
    """
    info: Optional[ReleaseInfo] = fetch_latest(package, language)
    if info is None:
        return None

    outdated = _is_newer(current_version, info.version)
    return UpdateInfo(
        package=package,
        current_version=current_version,
        latest_version=info.version,
        release_url=info.url,
        is_outdated=outdated,
    )


def check_project(project: ProjectConfig) -> list[UpdateInfo]:
    """Check all dependencies listed in *project* and return UpdateInfo list.

    Only packages whose version can be resolved are included.
    """
    results: list[UpdateInfo] = []
    for package, current_version in project.dependencies.items():
        update = check_package(package, current_version, project.language)
        if update is not None:
            results.append(update)
    return results
