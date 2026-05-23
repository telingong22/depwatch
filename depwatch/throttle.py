"""Throttle: per-package alert suppression based on a cooldown window.

Prevents repeated alerts for the same package within a configurable
cooldown period by tracking the last-alerted timestamp in a JSON file.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict

_DEFAULT_COOLDOWN_HOURS = 24


@dataclass
class ThrottlePolicy:
    cooldown_hours: int = _DEFAULT_COOLDOWN_HOURS

    def __post_init__(self) -> None:
        if self.cooldown_hours < 1:
            raise ValueError("cooldown_hours must be >= 1")

    @property
    def cooldown_seconds(self) -> float:
        return self.cooldown_hours * 3600.0


def _load_store(path: str) -> Dict[str, float]:
    """Load the throttle store from *path*; return empty dict on any error."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        return {str(k): float(v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError, OSError):
        return {}


def _save_store(path: str, store: Dict[str, float]) -> None:
    """Persist *store* to *path*, creating parent directories as needed."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(store, fh, indent=2)


def is_throttled(package: str, policy: ThrottlePolicy, store_path: str) -> bool:
    """Return True if *package* was alerted within the cooldown window."""
    store = _load_store(store_path)
    last_ts = store.get(package)
    if last_ts is None:
        return False
    return (time.time() - last_ts) < policy.cooldown_seconds


def record_alert(package: str, store_path: str) -> None:
    """Mark *package* as alerted right now."""
    store = _load_store(store_path)
    store[package] = time.time()
    _save_store(store_path, store)


def filter_throttled(
    packages: list[str],
    policy: ThrottlePolicy,
    store_path: str,
) -> list[str]:
    """Return only those packages in *packages* that are NOT throttled."""
    return [p for p in packages if not is_throttled(p, policy, store_path)]
