"""Integration tests for the labeling pipeline."""
from __future__ import annotations

from unittest.mock import MagicMock

from depwatch.labeling import label_all, LABEL_MAJOR, LABEL_SECURITY, LABEL_PRE_RELEASE, LABEL_PYTHON


def _u(pkg, current, latest, language="python", project="app"):
    u = MagicMock()
    u.package_name = pkg
    u.current_version = current
    u.latest_version = latest
    u.language = language
    u.project_name = project
    return u


def test_mixed_updates_all_labeled():
    updates = [
        _u("django", "3.2.0", "4.0.0"),
        _u("flask", "2.0.0", "2.1.0"),
        _u("cryptography", "3.4.0", "3.4.8"),
    ]
    result = label_all(updates, security_packages=["cryptography"])
    assert len(result) == 3
    labels_by_pkg = {lu.update.package_name: lu.labels for lu in result}
    assert LABEL_MAJOR in labels_by_pkg["django"]
    assert LABEL_SECURITY in labels_by_pkg["cryptography"]
    assert LABEL_PYTHON in labels_by_pkg["flask"]


def test_pre_release_and_major_coexist():
    u = _u("mylib", "1.0.0", "2.0.0b2")
    result = label_all([u])
    labels = result[0].labels
    assert LABEL_MAJOR in labels
    assert LABEL_PRE_RELEASE in labels


def test_empty_updates_returns_empty():
    result = label_all([])
    assert result == []


def test_to_dict_round_trip_preserves_labels():
    updates = [_u("requests", "2.27.0", "2.28.0")]
    result = label_all(updates)
    d = result[0].to_dict()
    assert isinstance(d["labels"], list)
    assert d["package"] == "requests"
    assert d["current"] == "2.27.0"
    assert d["latest"] == "2.28.0"
