"""Tests for depwatch.annotation."""
from __future__ import annotations

import json
import os
import pytest

from depwatch.annotation import (
    Annotation,
    AnnotationStore,
    annotate_update,
    load_annotations,
    save_annotations,
)


def _make_annotation(project="myapp", package="requests", note="check CVE", author="alice") -> Annotation:
    return Annotation(project=project, package=package, note=note, author=author)


def test_annotation_to_dict_keys():
    ann = _make_annotation()
    d = ann.to_dict()
    assert set(d.keys()) == {"project", "package", "note", "author"}


def test_annotation_round_trip():
    ann = _make_annotation()
    restored = Annotation.from_dict(ann.to_dict())
    assert restored.project == ann.project
    assert restored.package == ann.package
    assert restored.note == ann.note
    assert restored.author == ann.author


def test_annotation_default_author():
    ann = Annotation.from_dict({"project": "p", "package": "pkg", "note": "n"})
    assert ann.author == "depwatch"


def test_store_is_empty_initially():
    store = AnnotationStore()
    assert store.is_empty()


def test_store_add_and_get():
    store = AnnotationStore()
    ann = _make_annotation()
    store.add(ann)
    results = store.get("myapp", "requests")
    assert len(results) == 1
    assert results[0].note == "check CVE"


def test_store_get_filters_by_project():
    store = AnnotationStore()
    store.add(_make_annotation(project="a", package="pkg"))
    store.add(_make_annotation(project="b", package="pkg"))
    assert len(store.get("a", "pkg")) == 1
    assert len(store.get("b", "pkg")) == 1


def test_store_to_dict_structure():
    store = AnnotationStore()
    store.add(_make_annotation())
    d = store.to_dict()
    assert "annotations" in d
    assert len(d["annotations"]) == 1


def test_load_annotations_missing_file(tmp_path):
    store = load_annotations(str(tmp_path / "missing.json"))
    assert store.is_empty()


def test_load_annotations_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json")
    store = load_annotations(str(p))
    assert store.is_empty()


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "annotations.json")
    store = AnnotationStore()
    store.add(_make_annotation(note="important"))
    save_annotations(store, path)
    loaded = load_annotations(path)
    assert not loaded.is_empty()
    assert loaded.entries[0].note == "important"


def test_save_creates_file(tmp_path):
    path = str(tmp_path / "sub" / "annotations.json")
    store = AnnotationStore()
    store.add(_make_annotation())
    save_annotations(store, path)
    assert os.path.exists(path)


def test_annotate_update_helper():
    store = AnnotationStore()
    ann = annotate_update(store, "proj", "flask", "upgrade soon")
    assert ann.project == "proj"
    assert ann.package == "flask"
    assert len(store.entries) == 1


def test_load_annotations_wrong_structure(tmp_path):
    p = tmp_path / "wrong.json"
    p.write_text(json.dumps(["not", "a", "dict"]))
    store = load_annotations(str(p))
    assert store.is_empty()
