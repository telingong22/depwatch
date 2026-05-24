"""CLI sub-command: depwatch diff — compare two dependency lock-file snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from depwatch.diffing import diff_dependency_sets
from depwatch.parser import parse_dependencies
from depwatch.config import load_config


def add_diff_parser(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("diff", help="Diff two dependency files or snapshots")
    p.add_argument("before", help="Path to the 'before' requirements/go.mod file")
    p.add_argument("after", help="Path to the 'after' requirements/go.mod file")
    p.add_argument("--language", choices=["python", "go"], required=True,
                   help="Language of the dependency files")
    p.add_argument("--project", default="unknown", help="Project label for output")
    p.add_argument("--format", choices=["text", "json"], default="text",
                   help="Output format (default: text)")
    p.add_argument("--skip-unchanged", action="store_true",
                   help="Omit packages with no version change")
    p.set_defaults(func=_run_diff)


def _run_diff(args: argparse.Namespace) -> None:
    before_path = Path(args.before)
    after_path = Path(args.after)

    for p in (before_path, after_path):
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            sys.exit(1)

    before_deps = parse_dependencies(str(before_path), args.language)
    after_deps = parse_dependencies(str(after_path), args.language)

    result = diff_dependency_sets(
        project=args.project,
        language=args.language,
        before=before_deps,
        after=after_deps,
    )

    entries = result.entries
    if args.skip_unchanged:
        entries = [e for e in entries if e.change != "unchanged"]

    if args.format == "json":
        data = result.to_dict()
        if args.skip_unchanged:
            data["entries"] = [e.to_dict() for e in entries]
        print(json.dumps(data, indent=2))
        return

    # text output
    if not entries:
        print("No differences found.")
        return

    print(result.summary())
    print()
    symbols = {"added": "+", "removed": "-", "upgraded": "^", "downgraded": "v", "unchanged": "="}
    for e in entries:
        sym = symbols.get(e.change, "?")
        old = e.old_version or "(none)"
        new = e.new_version or "(none)"
        print(f"  [{sym}] {e.package}: {old} -> {new}  ({e.change})")
