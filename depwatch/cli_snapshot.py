"""CLI sub-command: snapshot — capture and diff dependency snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from depwatch.config import load_config
from depwatch.parser import parse_dependencies
from depwatch.snapshot import (
    Snapshot,
    SnapshotEntry,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def add_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("snapshot", help="Capture or diff dependency snapshots")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument(
        "--output", default=".depwatch_snapshot.json", help="Snapshot file path"
    )
    p.add_argument(
        "--diff",
        action="store_true",
        help="Show diff against previous snapshot instead of saving",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for --diff",
    )
    p.set_defaults(func=_run_snapshot)


def _run_snapshot(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    all_entries: list[SnapshotEntry] = []
    for project in cfg.projects:
        deps = parse_dependencies(project)
        for pkg, ver in deps.items():
            all_entries.append(SnapshotEntry(package=f"{project.name}/{pkg}", version=ver))

    new_snap = Snapshot(
        project="_all",
        entries=all_entries,
    )

    if args.diff:
        old_snap = load_snapshot(args.output)
        changes = diff_snapshots(old_snap, new_snap)
        if args.format == "json":
            print(json.dumps({k: {"from": v[0], "to": v[1]} for k, v in changes.items()}, indent=2))
        else:
            if not changes:
                print("No changes detected.")
            else:
                for pkg, (old_v, new_v) in sorted(changes.items()):
                    old_label = old_v if old_v else "(new)"
                    print(f"  {pkg}: {old_label} -> {new_v}")
        return 0

    save_snapshot(args.output, new_snap)
    print(f"Snapshot saved to {args.output} ({len(all_entries)} packages).")
    return 0
