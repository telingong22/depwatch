"""CLI sub-command: depwatch heatmap — show package update frequency."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.heatmap import build_heatmap
from depwatch.history import load_history


def add_heatmap_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("heatmap", help="Show packages ranked by update frequency")
    p.add_argument("--history-file", default="depwatch-history.json", metavar="FILE")
    p.add_argument("--top", type=int, default=10, metavar="N", help="Show top N packages")
    p.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")
    p.set_defaults(func=_run_heatmap)


def _run_heatmap(args: argparse.Namespace) -> int:
    history = load_history(args.history_file)

    if not history:
        if args.fmt == "json":
            print(json.dumps({"entries": []}))
        else:
            print("No history entries found.")
        return 0

    report = build_heatmap(history)
    top_entries = report.top(args.top)

    if args.fmt == "json":
        print(json.dumps({"entries": [e.to_dict() for e in top_entries]}, indent=2))
    else:
        if not top_entries:
            print("No update frequency data available.")
        else:
            print(f"Top {len(top_entries)} most-updated packages:")
            for i, entry in enumerate(top_entries, 1):
                print(f"  {i:>3}. {entry}")
    return 0
