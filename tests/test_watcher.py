"""Tests for depwatch.watcher.FileWatcher."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from depwatch.watcher import FileWatcher, _WATCHED_FILENAMES


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _watcher(tmp_path: Path, callback=None, poll_interval: float = 0.05):
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.31.0\n")
    cb = callback or MagicMock()
    return FileWatcher([req], cb, poll_interval=poll_interval), req, cb


# ---------------------------------------------------------------------------
# unit tests
# ---------------------------------------------------------------------------

def test_watched_filenames_contains_expected():
    assert "requirements.txt" in _WATCHED_FILENAMES
    assert "go.mod" in _WATCHED_FILENAMES


def test_non_watched_files_are_filtered(tmp_path: Path):
    setup_py = tmp_path / "setup.py"
    setup_py.write_text("")
    watcher = FileWatcher([setup_py], MagicMock())
    assert watcher._paths == []


def test_snapshot_records_mtime(tmp_path: Path):
    watcher, req, _ = _watcher(tmp_path)
    watcher._snapshot()
    assert req in watcher._mtimes
    assert watcher._mtimes[req] == req.stat().st_mtime


def test_snapshot_missing_file(tmp_path: Path):
    ghost = tmp_path / "requirements.txt"
    watcher = FileWatcher([ghost], MagicMock())
    watcher._snapshot()
    assert watcher._mtimes[ghost] == 0.0


def test_callback_triggered_on_change(tmp_path: Path):
    triggered = threading.Event()

    def cb(path):
        triggered.set()

    watcher, req, _ = _watcher(tmp_path, callback=cb, poll_interval=0.05)
    watcher.start()
    time.sleep(0.02)
    req.write_text("requests==2.32.0\n")
    assert triggered.wait(timeout=1.0), "callback was not triggered"
    watcher.stop()


def test_callback_not_triggered_without_change(tmp_path: Path):
    watcher, req, cb = _watcher(tmp_path, poll_interval=0.05)
    watcher.start()
    time.sleep(0.2)
    watcher.stop()
    cb.assert_not_called()


def test_stop_joins_thread(tmp_path: Path):
    watcher, _, _ = _watcher(tmp_path, poll_interval=0.05)
    watcher.start()
    assert watcher._thread is not None
    watcher.stop()
    assert not watcher._thread.is_alive()


def test_callback_exception_does_not_crash_watcher(tmp_path: Path):
    boom_count = [0]
    done = threading.Event()

    def bad_cb(path):
        boom_count[0] += 1
        done.set()
        raise RuntimeError("boom")

    watcher, req, _ = _watcher(tmp_path, callback=bad_cb, poll_interval=0.05)
    watcher.start()
    time.sleep(0.02)
    req.write_text("flask==3.0.0\n")
    done.wait(timeout=1.0)
    # watcher thread must still be alive after the exception
    assert watcher._thread is not None and watcher._thread.is_alive()
    watcher.stop()
