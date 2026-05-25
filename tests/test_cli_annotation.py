"""Tests for depwatch.cli_annotation."""
from __future__ import annotations

import argparse
import json
import pytest

from depwatch.annotation import AnnotationStore, save_annotations, Annotation
from depwatch.cli_annotation import add_annotation_parser, _run_annotation


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": "",
        "annotation_cmd": None,
        "project": None,
        "package": None,
        "note": None,
        "author": "depwatch",
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_annotation_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_annotation_parser(sub)
    args = parser.parse_args(["annotate", "list"])
    assert args.cmd == "annotate"


def test_run_annotation_no_cmd_returns_error(tmp_path):
    ns = _make_namespace(file=str(tmp_path / "a.json"), annotation_cmd=None)
    result = _run_annotation(ns)
    assert result == 1


def test_run_annotation_add_creates_entry(tmp_path):
    path = str(tmp_path / "a.json")
    ns = _make_namespace(
        file=path,
        annotation_cmd="add",
        project="myapp",
        package="requests",
        note="needs review",
        author="bob",
    )
    result = _run_annotation(ns)
    assert result == 0

    from depwatch.annotation import load_annotations
    store = load_annotations(path)
    assert not store.is_empty()
    assert store.entries[0].note == "needs review"


def test_run_annotation_list_empty(tmp_path, capsys):
    path = str(tmp_path / "a.json")
    ns = _make_namespace(file=path, annotation_cmd="list", project=None, package=None)
    result = _run_annotation(ns)
    assert result == 0
    captured = capsys.readouterr()
    assert "No annotations" in captured.out


def test_run_annotation_list_text(tmp_path, capsys):
    path = str(tmp_path / "a.json")
    store = AnnotationStore()
    store.add(Annotation(project="p", package="pkg", note="hello", author="alice"))
    save_annotations(store, path)

    ns = _make_namespace(file=path, annotation_cmd="list", project=None, package=None, format="text")
    result = _run_annotation(ns)
    assert result == 0
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "alice" in captured.out


def test_run_annotation_list_json(tmp_path, capsys):
    path = str(tmp_path / "a.json")
    store = AnnotationStore()
    store.add(Annotation(project="p", package="pkg", note="json-note", author="ci"))
    save_annotations(store, path)

    ns = _make_namespace(file=path, annotation_cmd="list", project=None, package=None, format="json")
    result = _run_annotation(ns)
    assert result == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["note"] == "json-note"
