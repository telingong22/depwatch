"""Tests for depwatch.parser."""

from __future__ import annotations

import pytest
from pathlib import Path

from depwatch.parser import (
    parse_requirements_txt,
    parse_go_mod,
    parse_dependencies,
)


# ---------------------------------------------------------------------------
# parse_requirements_txt
# ---------------------------------------------------------------------------

def test_parse_requirements_txt_pinned(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.31.0\nflask==3.0.1\n")
    result = parse_requirements_txt(req)
    assert result == {"requests": "2.31.0", "flask": "3.0.1"}


def test_parse_requirements_txt_unpinned(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("requests\nflask>=2.0\n")
    result = parse_requirements_txt(req)
    assert "requests" in result
    assert result["requests"] == ""
    assert "flask" in result


def test_parse_requirements_txt_skips_comments(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("# this is a comment\nrequests==2.31.0\n")
    result = parse_requirements_txt(req)
    assert list(result.keys()) == ["requests"]


def test_parse_requirements_txt_skips_blank_lines(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("\nrequests==2.31.0\n\n")
    result = parse_requirements_txt(req)
    assert len(result) == 1


def test_parse_requirements_txt_normalises_name(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("Requests==2.31.0\n")
    result = parse_requirements_txt(req)
    assert "requests" in result


# ---------------------------------------------------------------------------
# parse_go_mod
# ---------------------------------------------------------------------------

GO_MOD_CONTENT = """\
module github.com/example/myapp

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    golang.org/x/net v0.20.0 // indirect
)
"""


def test_parse_go_mod_direct_deps(tmp_path: Path) -> None:
    go_mod = tmp_path / "go.mod"
    go_mod.write_text(GO_MOD_CONTENT)
    result = parse_go_mod(go_mod)
    assert result.get("github.com/gin-gonic/gin") == "v1.9.1"


def test_parse_go_mod_indirect_deps(tmp_path: Path) -> None:
    go_mod = tmp_path / "go.mod"
    go_mod.write_text(GO_MOD_CONTENT)
    result = parse_go_mod(go_mod)
    assert result.get("golang.org/x/net") == "v0.20.0"


# ---------------------------------------------------------------------------
# parse_dependencies dispatch
# ---------------------------------------------------------------------------

def test_parse_dependencies_python(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("httpx==0.27.0\n")
    result = parse_dependencies("python", str(tmp_path))
    assert result == {"httpx": "0.27.0"}


def test_parse_dependencies_go(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text(GO_MOD_CONTENT)
    result = parse_dependencies("go", str(tmp_path))
    assert "github.com/gin-gonic/gin" in result


def test_parse_dependencies_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_dependencies("python", str(tmp_path))


def test_parse_dependencies_unsupported_language(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported language"):
        parse_dependencies("ruby", str(tmp_path))
