"""File-system watcher that detects changes to dependency files and triggers
a re-scan without waiting for the next scheduled interval."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Dict

logger = logging.getLogger(__name__)

_WATCHED_FILENAMES = {
    "requirements.txt",
    "go.mod",
}


class FileWatcher:
    """Poll watched dependency files for mtime changes and invoke a callback."""

    def __init__(
        self,
        paths: list[Path],
        callback: Callable[[Path], None],
        poll_interval: float = 5.0,
    ) -> None:
        self._paths = [p for p in paths if p.name in _WATCHED_FILENAMES]
        self._callback = callback
        self._poll_interval = poll_interval
        self._mtimes: Dict[Path, float] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the background polling thread."""
        self._snapshot()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("FileWatcher started, watching %d file(s)", len(self._paths))

    def stop(self) -> None:
        """Signal the polling thread to stop and join it."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._poll_interval + 1)
        logger.info("FileWatcher stopped")

    # ------------------------------------------------------------------
    def _snapshot(self) -> None:
        for path in self._paths:
            try:
                self._mtimes[path] = path.stat().st_mtime
            except FileNotFoundError:
                self._mtimes[path] = 0.0

    def _run(self) -> None:
        while not self._stop_event.wait(self._poll_interval):
            for path in self._paths:
                try:
                    mtime = path.stat().st_mtime
                except FileNotFoundError:
                    mtime = 0.0
                if mtime != self._mtimes.get(path):
                    logger.info("Detected change in %s", path)
                    self._mtimes[path] = mtime
                    try:
                        self._callback(path)
                    except Exception:
                        logger.exception("Callback raised an error for %s", path)
