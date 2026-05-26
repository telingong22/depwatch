"""CLI subcommand: lifecycle — view and update dependency lifecycle stages."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.config import load_config
from depwatch.lifecycle import STAGES, entries_by_stage, load_lifecycle, save_lifecycle, upsert_entry
from depwatch.runner import _collect_updates


def add_lifecycle_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("lifecycle", help="View or update dependency lifecycle stages")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument("--state", default=".depwatch_state.json", help="State file path")
    p.add_argument("--lifecycle-file", default=".depwatch_lifecycle.json", help="Lifecycle store path")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--stage-filter", choices=list(STAGES) + ["all"], default="all",
                   help="Filter entries by stage")
    p.add_argument("--set-stage", choices=list(STAGES), default=None,
                   help="Transition all current updates to this stage")
    p.add_argument("--note", default="", help="Optional note when setting stage")
    p.set_defaults(func=_run_lifecycle)


def _run_lifecycle(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    store = load_lifecycle(args.lifecycle_file)

    if args.set_stage:
        updates = _collect_updates(cfg, args.state)
        for u in updates:
            upsert_entry(store, u, stage=args.set_stage, note=args.note)
        save_lifecycle(args.lifecycle_file, store)
        print(f"Updated {len(updates)} entr(ies) to stage '{args.set_stage}'.")
        return 0

    entries = (
        list(store.values())
        if args.stage_filter == "all"
        else entries_by_stage(store, args.stage_filter)
    )

    if args.format == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        if not entries:
            print("No lifecycle entries found.")
        else:
            for e in entries:
                print(f"[{e.stage.upper()}] {e.project} / {e.package} "
                      f"{e.current_version} -> {e.latest_version}"
                      + (f"  # {e.note}" if e.note else ""))
    return 0
