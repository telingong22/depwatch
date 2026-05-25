"""Tests for depwatch.clustering."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from depwatch.checker import UpdateInfo
from depwatch.clustering import Cluster, ClusterReport, build_clusters
from depwatch.digest import ProjectDigest


def _make_update(
    project: str = "myproject",
    package: str = "requests",
    current: str = "1.0.0",
    latest: str = "2.0.0",
    language: str = "python",
) -> UpdateInfo:
    u = MagicMock(spec=UpdateInfo)
    u.project_name = project
    u.package_name = package
    u.current_version = current
    u.latest_version = latest
    u.language = language
    return u


def _make_digest(updates) -> ProjectDigest:
    d = MagicMock(spec=ProjectDigest)
    d.updates = updates
    return d


# ---------------------------------------------------------------------------
# Cluster unit tests
# ---------------------------------------------------------------------------

def test_cluster_is_empty_when_no_updates():
    c = Cluster(key="python/major", language="python", bump="major")
    assert c.is_empty()


def test_cluster_not_empty_with_updates():
    c = Cluster(key="python/major", language="python", bump="major",
                updates=[_make_update()])
    assert not c.is_empty()


def test_cluster_to_dict_keys():
    c = Cluster(key="python/minor", language="python", bump="minor",
                updates=[_make_update(current="1.0.0", latest="1.1.0")])
    d = c.to_dict()
    assert set(d.keys()) == {"key", "language", "bump", "count", "packages"}


def test_cluster_to_dict_count():
    updates = [_make_update(), _make_update(package="boto3")]
    c = Cluster(key="python/major", language="python", bump="major",
                updates=updates)
    assert c.to_dict()["count"] == 2


def test_cluster_str_contains_key():
    c = Cluster(key="go/patch", language="go", bump="patch",
                updates=[_make_update()])
    assert "go/patch" in str(c)


# ---------------------------------------------------------------------------
# ClusterReport unit tests
# ---------------------------------------------------------------------------

def test_report_is_empty_when_no_clusters():
    r = ClusterReport()
    assert r.is_empty()


def test_report_not_empty_with_clusters():
    c = Cluster(key="python/major", language="python", bump="major",
                updates=[_make_update()])
    r = ClusterReport(clusters=[c])
    assert not r.is_empty()


def test_report_to_dict_has_clusters_key():
    r = ClusterReport()
    assert "clusters" in r.to_dict()


def test_report_summary_empty():
    r = ClusterReport()
    assert "No clusters" in r.summary()


def test_report_summary_lists_clusters():
    c = Cluster(key="python/major", language="python", bump="major",
                updates=[_make_update()])
    r = ClusterReport(clusters=[c])
    assert "python/major" in r.summary()


# ---------------------------------------------------------------------------
# build_clusters integration-style tests
# ---------------------------------------------------------------------------

def test_build_clusters_groups_by_language_and_bump():
    digests = {
        "proj": _make_digest([
            _make_update(current="1.0.0", latest="2.0.0", language="python"),
            _make_update(package="flask", current="1.0.0", latest="1.1.0",
                         language="python"),
        ])
    }
    report = build_clusters(digests)
    keys = {c.key for c in report.clusters}
    assert "python/major" in keys
    assert "python/minor" in keys


def test_build_clusters_empty_digests_returns_empty_report():
    report = build_clusters({})
    assert report.is_empty()


def test_build_clusters_go_and_python_separate():
    digests = {
        "p1": _make_digest([
            _make_update(language="python", current="1.0.0", latest="2.0.0"),
        ]),
        "p2": _make_digest([
            _make_update(language="go", current="1.0.0", latest="2.0.0"),
        ]),
    }
    report = build_clusters(digests)
    keys = {c.key for c in report.clusters}
    assert "python/major" in keys
    assert "go/major" in keys
    assert len(report.clusters) == 2
