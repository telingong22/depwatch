"""Parsers for extracting dependencies from Python and Go project files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict


def parse_requirements_txt(path: Path) -> Dict[str, str]:
    """Parse a requirements.txt file and return {package: version} mapping.

    Supports pinned versions (==) only; unpinned entries are stored with
    an empty string so they can still be checked for the latest release.
    """
    deps: Dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Strip extras / environment markers
        line = re.split(r"[;\s]", line)[0]
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s,]+)", line)
        if match:
            name, version = match.group(1), match.group(2)
        else:
            name_match = re.match(r"^([A-Za-z0-9_.-]+)", line)
            if not name_match:
                continue
            name, version = name_match.group(1), ""
        deps[name.lower()] = version
    return deps


def parse_go_mod(path: Path) -> Dict[str, str]:
    """Parse a go.mod file and return {module: version} mapping.

    Only direct and indirect *require* entries are captured.
    """
    deps: Dict[str, str] = {}
    text = path.read_text(encoding="utf-8")
    # Match both single-line and block require statements
    for line in text.splitlines():
        line = line.strip().rstrip(")")
        # Strip inline comments
        line = re.sub(r"//.*", "", line).strip()
        match = re.match(r"^([^\s]+)\s+(v[^\s]+)", line)
        if match:
            module, version = match.group(1), match.group(2)
            deps[module] = version
    return deps


def parse_dependencies(language: str, project_path: str) -> Dict[str, str]:
    """Dispatch to the correct parser based on *language*.

    Returns a {name: current_version} mapping.
    Raises FileNotFoundError if the expected dependency file is missing.
    """
    root = Path(project_path)
    if language == "python":
        candidates = [root / "requirements.txt"]
        for candidate in candidates:
            if candidate.exists():
                return parse_requirements_txt(candidate)
        raise FileNotFoundError(
            f"No requirements.txt found in {project_path}"
        )
    elif language == "go":
        go_mod = root / "go.mod"
        if not go_mod.exists():
            raise FileNotFoundError(f"No go.mod found in {project_path}")
        return parse_go_mod(go_mod)
    else:
        raise ValueError(f"Unsupported language: {language}")
