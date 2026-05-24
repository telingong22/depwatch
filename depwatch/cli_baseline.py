"""CLI sub-command: baseline — capture or diff dependency baselines."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from depwatch.baseline import BaselineEntry, diff_baseline, load_baseline, save_baseline
from depwatch.config import load_config
from depwatch.parser import parse_dependencies


def add_baseline_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("baseline", help="Capture or diff dependency baselines")
    p.add_argument("--config", default="depwatch.yml", help="Config file path")
    p.add_argument("--file", default="baseline.json", help="Baseline storage file")
    p.add_argument(
        "--action",
        choices=["capture", "diff"],
        default="capture",
        help="Action to perform",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for diff",
    )
    p.set_defaults(func=_run_baseline)


def _run_baseline(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"error: config file not found: {args.config}", file=sys.stderr)
        return 1

    if args.action == "capture":
        entries: list[BaselineEntry] = []
        for proj in cfg.projects:
            deps = parse_dependencies(proj)
            for pkg, ver in deps.items():
                entries.append(
                    BaselineEntry(
                        package=pkg,
                        version=ver or "",
                        project=proj.name,
                        recorded_at=datetime.now(timezone.utc).isoformat(),
                    )
                )
        save_baseline(args.file, entries)
        print(f"Baseline captured: {len(entries)} package(s) written to {args.file}")
        return 0

    # diff
    old = load_baseline(args.file)
    new_entries: list[BaselineEntry] = []
    for proj in cfg.projects:
        deps = parse_dependencies(proj)
        for pkg, ver in deps.items():
            new_entries.append(
                BaselineEntry(package=pkg, version=ver or "", project=proj.name)
            )
    changed = diff_baseline(old, new_entries)
    if args.format == "json":
        print(json.dumps(changed, indent=2))
    else:
        if not changed:
            print("No changes detected since last baseline.")
        else:
            for key, versions in changed.items():
                old_v = versions["old"] or "(new)"
                new_v = versions["new"] or "(removed)"
                print(f"  {key}: {old_v} -> {new_v}")
    return 0
