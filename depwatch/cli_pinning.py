"""CLI subcommand: depwatch pin — show pin suggestions for outdated deps."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from depwatch.config import load_config
from depwatch.digest import build_all_digests
from depwatch.pinning import build_pin_suggestions, suggestions_to_text
from depwatch.runner import _collect_updates


def add_pin_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("pin", help="Show pin suggestions for outdated dependencies")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=_run_pin)


def _run_pin(args: argparse.Namespace) -> None:
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    updates = _collect_updates(config)
    digests = build_all_digests(config, updates)
    suggestions = build_pin_suggestions(digests)

    if args.format == "json":
        print(json.dumps([s.to_dict() for s in suggestions], indent=2))
    else:
        print(suggestions_to_text(suggestions))
