"""CLI sub-command: depwatch provenance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from depwatch.provenance import load_provenance


def add_provenance_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("provenance", help="Show first-seen provenance for packages")
    p.add_argument("--provenance-file", default=".depwatch/provenance.json",
                   help="Path to provenance store (default: .depwatch/provenance.json)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--project", default=None, help="Filter by project name")
    p.set_defaults(func=_run_provenance)


def _run_provenance(args: argparse.Namespace) -> int:
    path = Path(args.provenance_file)
    if not path.exists():
        print(f"No provenance file found at {path}")
        return 1

    store = load_provenance(path)
    entries = list(store.values())

    if args.project:
        entries = [e for e in entries if e.project == args.project]

    if not entries:
        print("No provenance entries found.")
        return 0

    if args.format == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        for e in sorted(entries, key=lambda x: x.first_seen):
            print(f"[{e.language}] {e.project}/{e.package} "
                  f"first seen {e.first_seen} "
                  f"(latest={e.latest_version}, source={e.source})")
    return 0
