"""Integration tests for the dependency graph feature."""
from __future__ import annotations

import pytest

from depwatch.checker import UpdateInfo
from depwatch.dependency_graph import build_graph
from depwatch.digest import ProjectDigest


def _u(project: str, package: str, language: str = "python", current: str = "1.0", latest: str = "2.0") -> UpdateInfo:
    u = UpdateInfo(
        project_name=project,
        package=package,
        language=language,
        current_version=current,
        latest_version=latest,
    )
    return u


def _d(project_name: str, updates: list) -> ProjectDigest:
    return ProjectDigest(project_name=project_name, updates=updates)


def test_full_pipeline_single_project_no_shared():
    digests = [_d("alpha", [_u("alpha", "requests"), _u("alpha", "flask")])]
    graph = build_graph(digests)
    assert len(graph.nodes) == 2
    assert graph.shared_packages() == []


def test_full_pipeline_two_projects_one_shared():
    digests = [
        _d("alpha", [_u("alpha", "requests"), _u("alpha", "flask")]),
        _d("beta", [_u("beta", "requests"), _u("beta", "gin", language="go")]),
    ]
    graph = build_graph(digests)
    shared = graph.shared_packages()
    assert len(shared) == 1
    assert shared[0].package == "requests"


def test_full_pipeline_go_and_python_same_name_different_nodes():
    """Same package name in different languages should be separate nodes."""
    digests = [
        _d("alpha", [_u("alpha", "yaml", language="python")]),
        _d("beta", [_u("beta", "yaml", language="go")]),
    ]
    graph = build_graph(digests)
    assert len(graph.nodes) == 2
    assert graph.shared_packages() == []


def test_to_dict_total_and_shared_counts():
    digests = [
        _d("alpha", [_u("alpha", "requests"), _u("alpha", "flask")]),
        _d("beta", [_u("beta", "requests")]),
    ]
    graph = build_graph(digests)
    d = graph.to_dict()
    assert d["total_packages"] == 2
    assert d["shared_packages"] == 1
