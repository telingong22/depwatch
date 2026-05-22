"""Fetches latest release information for Python and Go dependencies."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

PYPI_URL = "https://pypi.org/pypi/{package}/json"
GO_PROXY_URL = "https://proxy.golang.org/{module}/@latest"


@dataclass
class ReleaseInfo:
    name: str
    version: str
    url: str
    language: str


def fetch_latest_python(package: str, timeout: int = 10) -> Optional[ReleaseInfo]:
    """Fetch the latest release version of a PyPI package."""
    url = PYPI_URL.format(package=package)
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        version = data["info"]["version"]
        project_url = data["info"]["project_url"] or f"https://pypi.org/project/{package}/"
        return ReleaseInfo(name=package, version=version, url=project_url, language="python")
    except requests.RequestException as exc:
        logger.warning("Failed to fetch PyPI package %s: %s", package, exc)
        return None
    except (KeyError, ValueError) as exc:
        logger.warning("Unexpected response for PyPI package %s: %s", package, exc)
        return None


def fetch_latest_go(module: str, timeout: int = 10) -> Optional[ReleaseInfo]:
    """Fetch the latest release version of a Go module via the Go module proxy."""
    encoded_module = module.replace("/", "/")
    url = GO_PROXY_URL.format(module=encoded_module)
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        version = data.get("Version", "")
        if not version:
            logger.warning("No version found for Go module %s", module)
            return None
        module_url = f"https://pkg.go.dev/{module}@{version}"
        return ReleaseInfo(name=module, version=version, url=module_url, language="go")
    except requests.RequestException as exc:
        logger.warning("Failed to fetch Go module %s: %s", module, exc)
        return None
    except (KeyError, ValueError) as exc:
        logger.warning("Unexpected response for Go module %s: %s", module, exc)
        return None


def fetch_latest(name: str, language: str) -> Optional[ReleaseInfo]:
    """Dispatch fetch based on language."""
    if language == "python":
        return fetch_latest_python(name)
    if language == "go":
        return fetch_latest_go(name)
    raise ValueError(f"Unsupported language: {language}")
