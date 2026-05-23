"""CLI sub-command: ``depwatch history`` — view recorded update history."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from depwatch.history import HistoryEntry, load_history


_DEFAULT_HISTORY_PATH = ".depwatch_history.json"


def add_history_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("history", help="Show recorded dependency update history")
    p.add_argument(
        "--history-file",
        default=_DEFAULT_HISTORY_PATH,
        metavar="PATH",
        help="Path to history JSON file (default: .depwatch_history.json)",
    )
    p.add_argument(
        "--project",
        default=None,
        metavar="NAME",
        help="Filter by project name",
    )
    p.add_argument(
        "--package",
        default=None,
        metavar="NAME",
        help="Filter by package name",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output as JSON array",
    )
    p.set_defaults(func=_run_history)


def _filter(entries: List[HistoryEntry], project: str | None, package: str | None) -> List[HistoryEntry]:
    if project:
        entries = [e for e in entries if e.project == project]
    if package:
        entries = [e for e in entries if e.package == package]
    return entries


def _run_history(args: argparse.Namespace) -> int:
    entries = load_history(args.history_file)
    entries = _filter(entries, args.project, args.package)

    if not entries:
        print("No history entries found.", file=sys.stderr)
        return 0

    if args.as_json:
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        for e in entries:
            from_ver = e.from_version or "unknown"
            print(f"{e.detected_at}  [{e.project}] {e.package} ({e.language})  {from_ver} -> {e.to_version}")

    return 0
