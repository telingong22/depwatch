"""CLI sub-command: depwatch label — show labeled updates."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.config import load_config
from depwatch.runner import _collect_updates
from depwatch.labeling import label_all


def add_label_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("label", help="Show labeled dependency updates")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument(
        "--security",
        nargs="*",
        metavar="PKG",
        default=[],
        help="Package names to tag as security-sensitive",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=_run_label)


def _run_label(args: argparse.Namespace) -> None:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    updates = _collect_updates(cfg)
    labeled = label_all(updates, security_packages=args.security or [])

    if args.format == "json":
        print(json.dumps([lu.to_dict() for lu in labeled], indent=2))
        return

    if not labeled:
        print("No updates found.")
        return

    for lu in labeled:
        tag_str = ", ".join(lu.labels) if lu.labels else "(none)"
        print(
            f"{lu.update.project_name} / {lu.update.package_name}: "
            f"{lu.update.current_version} -> {lu.update.latest_version}  "
            f"[{tag_str}]"
        )
