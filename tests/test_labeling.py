"""Unit tests for depwatch.labeling."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from depwatch.labeling import (
    LabeledUpdate,
    label_update,
    label_all,
    LABEL_SECURITY,
    LABEL_MAJOR,
    LABEL_MINOR,
    LABEL_PATCH,
    LABEL_PRE_RELEASE,
    LABEL_PYTHON,
    LABEL_GO,
    _is_pre_release,
)


def _make_update(pkg="requests", current="1.0.0", latest="2.0.0", language="python", project="myapp"):
    u = MagicMock()
    u.package_name = pkg
    u.current_version = current
    u.latest_version = latest
    u.language = language
    u.project_name = project
    return u


def test_label_python_language():
    u = _make_update(language="python")
    lu = label_update(u)
    assert LABEL_PYTHON in lu.labels
    assert LABEL_GO not in lu.labels


def test_label_go_language():
    u = _make_update(language="go", pkg="github.com/gin-gonic/gin", current="v1.8.0", latest="v2.0.0")
    lu = label_update(u)
    assert LABEL_GO in lu.labels
    assert LABEL_PYTHON not in lu.labels


def test_label_major_bump():
    u = _make_update(current="1.0.0", latest="2.0.0")
    lu = label_update(u)
    assert LABEL_MAJOR in lu.labels
    assert LABEL_MINOR not in lu.labels
    assert LABEL_PATCH not in lu.labels


def test_label_minor_bump():
    u = _make_update(current="1.0.0", latest="1.1.0")
    lu = label_update(u)
    assert LABEL_MINOR in lu.labels
    assert LABEL_MAJOR not in lu.labels


def test_label_patch_bump():
    u = _make_update(current="1.0.1", latest="1.0.2")
    lu = label_update(u)
    assert LABEL_PATCH in lu.labels
    assert LABEL_MAJOR not in lu.labels


def test_label_pre_release():
    u = _make_update(current="1.0.0", latest="2.0.0b1")
    lu = label_update(u)
    assert LABEL_PRE_RELEASE in lu.labels


def test_label_not_pre_release():
    u = _make_update(current="1.0.0", latest="1.1.0")
    lu = label_update(u)
    assert LABEL_PRE_RELEASE not in lu.labels


def test_label_security_match():
    u = _make_update(pkg="requests")
    lu = label_update(u, security_packages=["requests", "urllib3"])
    assert LABEL_SECURITY in lu.labels


def test_label_security_case_insensitive():
    u = _make_update(pkg="Requests")
    lu = label_update(u, security_packages=["requests"])
    assert LABEL_SECURITY in lu.labels


def test_label_security_no_match():
    u = _make_update(pkg="flask")
    lu = label_update(u, security_packages=["requests"])
    assert LABEL_SECURITY not in lu.labels


def test_label_all_returns_same_count():
    updates = [_make_update(pkg=f"pkg{i}") for i in range(4)]
    result = label_all(updates)
    assert len(result) == 4


def test_labeled_update_to_dict_keys():
    u = _make_update()
    lu = label_update(u)
    d = lu.to_dict()
    assert set(d.keys()) == {"project", "package", "current", "latest", "labels"}


def test_is_pre_release_rc():
    assert _is_pre_release("2.0.0rc1") is True


def test_is_pre_release_stable():
    assert _is_pre_release("2.0.0") is False


def test_is_pre_release_v_prefix():
    assert _is_pre_release("v2.0.0alpha1") is True
