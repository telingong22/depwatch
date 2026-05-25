"""Tests for depwatch.dependency_graph."""
from __future__ import annotations

import pytest

from depwatch.checker import UpdateInfo
from depwatch.dependency_graph import (
    DependencyGraph,
    GraphNode,
    _node_key,
    build_graph,
)
from depwatch.digest import ProjectDigest


def _make_update(package: str, language: str, current: str = "1.0.0", latest: str = "2.0.0") -> UpdateInfo:
    return UpdateInfo(
        project_name="proj",
        package=package,
        language=language,
        current_version=current,
        latest_version=latest,
    )


def _make_digest(project_name: str, updates: list) -> ProjectDigest:
    return ProjectDigest(project_name=project_name, updates=updates)


# --- GraphNode ---

def test_graph_node_to_dict_keys():
    node = GraphNode(package="requests", language="python", projects={"p1"}, current_version="1.0", latest_version="2.0")
    d = node.to_dict()
    assert set(d.keys()) == {"package", "language", "projects", "current_version", "latest_version", "shared"}


def test_graph_node_shared_true():
    node = GraphNode(package="requests", language="python", projects={"p1", "p2"})
    assert node.to_dict()["shared"] is True


def test_graph_node_shared_false():
    node = GraphNode(package="requests", language="python", projects={"p1"})
    assert node.to_dict()["shared"] is False


# --- _node_key ---

def test_node_key_lowercases_package():
    assert _node_key("Requests", "python") == "python:requests"


def test_node_key_includes_language():
    assert _node_key("gin", "go") == "go:gin"


# --- build_graph ---

def test_build_graph_empty_digests():
    graph = build_graph([])
    assert graph.is_empty()


def test_build_graph_single_project():
    u = _make_update("requests", "python")
    u.project_name = "proj-a"
    d = _make_digest("proj-a", [u])
    graph = build_graph([d])
    assert not graph.is_empty()
    assert len(graph.nodes) == 1


def test_build_graph_shared_package_across_projects():
    u1 = _make_update("requests", "python")
    u1.project_name = "proj-a"
    u2 = _make_update("requests", "python")
    u2.project_name = "proj-b"
    graph = build_graph([
        _make_digest("proj-a", [u1]),
        _make_digest("proj-b", [u2]),
    ])
    assert len(graph.nodes) == 1
    node = list(graph.nodes.values())[0]
    assert node.projects == {"proj-a", "proj-b"}


def test_build_graph_shared_packages_list():
    u1 = _make_update("requests", "python")
    u1.project_name = "proj-a"
    u2 = _make_update("requests", "python")
    u2.project_name = "proj-b"
    u3 = _make_update("flask", "python")
    u3.project_name = "proj-a"
    graph = build_graph([
        _make_digest("proj-a", [u1, u3]),
        _make_digest("proj-b", [u2]),
    ])
    shared = graph.shared_packages()
    assert len(shared) == 1
    assert shared[0].package == "requests"


def test_packages_for_project_filters_correctly():
    u1 = _make_update("requests", "python")
    u1.project_name = "proj-a"
    u2 = _make_update("flask", "python")
    u2.project_name = "proj-b"
    graph = build_graph([
        _make_digest("proj-a", [u1]),
        _make_digest("proj-b", [u2]),
    ])
    pkgs = graph.packages_for_project("proj-a")
    assert len(pkgs) == 1
    assert pkgs[0].package == "requests"


def test_build_graph_to_dict_structure():
    u = _make_update("requests", "python")
    u.project_name = "proj-a"
    graph = build_graph([_make_digest("proj-a", [u])])
    d = graph.to_dict()
    assert "nodes" in d
    assert "total_packages" in d
    assert "shared_packages" in d
    assert d["total_packages"] == 1
    assert d["shared_packages"] == 0
