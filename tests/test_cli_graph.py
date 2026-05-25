"""Tests for depwatch.cli_graph."""
from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli_graph import _print_text, _run_graph, add_graph_parser
from depwatch.dependency_graph import DependencyGraph, GraphNode


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {"config": "depwatch.yml", "format": "text", "shared_only": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_graph_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_graph_parser(sub)
    args = parser.parse_args(["graph"])
    assert hasattr(args, "func")


def test_run_graph_missing_config():
    args = _make_namespace(config="nonexistent.yml")
    with patch("depwatch.cli_graph.load_config", side_effect=FileNotFoundError):
        result = _run_graph(args)
    assert result == 1


def test_run_graph_text_output(capsys):
    args = _make_namespace(format="text", shared_only=False)
    mock_cfg = MagicMock()
    mock_cfg.state_file = "state.json"
    node = GraphNode(
        package="requests", language="python", projects={"proj-a"}, current_version="1.0", latest_version="2.0"
    )
    mock_graph = DependencyGraph(nodes={"python:requests": node})
    with patch("depwatch.cli_graph.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_graph.load_state", return_value={}), \
         patch("depwatch.cli_graph._collect_updates", return_value={}), \
         patch("depwatch.cli_graph.build_all_digests", return_value=[]), \
         patch("depwatch.cli_graph.build_graph", return_value=mock_graph):
        result = _run_graph(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "requests" in captured.out


def test_run_graph_json_output(capsys):
    args = _make_namespace(format="json", shared_only=False)
    mock_cfg = MagicMock()
    mock_cfg.state_file = "state.json"
    mock_graph = DependencyGraph(nodes={})
    with patch("depwatch.cli_graph.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_graph.load_state", return_value={}), \
         patch("depwatch.cli_graph._collect_updates", return_value={}), \
         patch("depwatch.cli_graph.build_all_digests", return_value=[]), \
         patch("depwatch.cli_graph.build_graph", return_value=mock_graph):
        result = _run_graph(args)
    assert result == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "nodes" in data


def test_print_text_empty_graph(capsys):
    graph = DependencyGraph(nodes={})
    _print_text(graph, shared_only=False)
    captured = capsys.readouterr()
    assert "No packages found" in captured.out


def test_print_text_shared_only_filters(capsys):
    node_shared = GraphNode("requests", "python", {"a", "b"}, "1.0", "2.0")
    node_solo = GraphNode("flask", "python", {"a"}, "0.1", "0.2")
    graph = DependencyGraph(nodes={"python:requests": node_shared, "python:flask": node_solo})
    _print_text(graph, shared_only=True)
    captured = capsys.readouterr()
    assert "requests" in captured.out
    assert "flask" not in captured.out
