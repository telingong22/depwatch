"""Persistent state management for tracking last-seen dependency versions."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_STATE_PATH = Path(".depwatch_state.json")

# State schema: {"<project_name>/<package_name>": "<last_seen_version>"}
StateDict = Dict[str, str]


def _state_key(project_name: str, package_name: str) -> str:
    return f"{project_name}/{package_name}"


def load_state(path: Path = _DEFAULT_STATE_PATH) -> StateDict:
    """Load persisted state from *path*. Returns empty dict if file absent."""
    if not path.exists():
        logger.debug("State file %s not found; starting fresh.", path)
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            logger.warning("State file %s has unexpected format; resetting.", path)
            return {}
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read state file %s: %s", path, exc)
        return {}


def save_state(state: StateDict, path: Path = _DEFAULT_STATE_PATH) -> None:
    """Atomically persist *state* to *path*."""
    tmp_path = path.with_suffix(".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        os.replace(tmp_path, path)
        logger.debug("State saved to %s (%d entries).", path, len(state))
    except OSError as exc:
        logger.error("Failed to save state to %s: %s", path, exc)
        tmp_path.unlink(missing_ok=True)


def get_last_seen(
    state: StateDict, project_name: str, package_name: str
) -> Optional[str]:
    """Return the last-seen version for *package_name* in *project_name*, or None."""
    return state.get(_state_key(project_name, package_name))


def set_last_seen(
    state: StateDict, project_name: str, package_name: str, version: str
) -> None:
    """Record *version* as the latest seen for *package_name* in *project_name*."""
    state[_state_key(project_name, package_name)] = version
