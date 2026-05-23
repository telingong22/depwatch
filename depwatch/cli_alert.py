"""CLI sub-command: depwatch alert — evaluate thresholds and print decision."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from depwatch.alerting import AlertThreshold, evaluate_threshold
from depwatch.config import Config, load_config
from depwatch.digest import build_all_digests
from depwatch.filter import FilterConfig
from depwatch.runner import _collect_updates
from depwatch.state import load_state


def add_alert_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("alert", help="Evaluate alert thresholds and show decision")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument("--min-updates", type=int, default=1, dest="min_updates")
    p.add_argument(
        "--require-major", action="store_true", dest="require_major",
        help="Only alert when a major-version bump is present",
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text", dest="fmt",
    )
    p.set_defaults(func=_run_alert)


def _print_text_decision(decision) -> None:  # type: ignore[no-untyped-def]
    """Print a human-readable summary of the alert decision to stdout."""
    status = "ALERT" if decision.should_alert else "SUPPRESS"
    print(f"[{status}] {decision.reason}")
    for d in decision.digests:
        print(f"  {d.project}: {len(d.updates)} update(s)")


def _print_json_decision(decision) -> None:  # type: ignore[no-untyped-def]
    """Print a JSON-formatted summary of the alert decision to stdout."""
    out = {
        "should_alert": decision.should_alert,
        "reason": decision.reason,
        "projects": [
            {"project": d.project, "updates": len(d.updates)}
            for d in decision.digests
        ],
    }
    print(json.dumps(out, indent=2))


def _run_alert(args: argparse.Namespace) -> int:
    """Entry point for the ``alert`` sub-command.

    Loads configuration and state, collects pending updates, evaluates the
    configured alert threshold, and prints the decision.  Exit codes:

    * ``0`` — threshold met, alert should fire.
    * ``1`` — configuration or runtime error.
    * ``2`` — threshold not met, alert suppressed.
    """
    try:
        cfg: Config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    state = load_state(cfg.state_file if hasattr(cfg, "state_file") else "depwatch_state.json")
    updates_by_project = _collect_updates(cfg, state)
    digests = build_all_digests(cfg, updates_by_project)

    threshold = AlertThreshold(
        min_updates=args.min_updates,
        require_major=args.require_major,
        filter=FilterConfig(),
    )
    decision = evaluate_threshold(digests, threshold)

    if args.fmt == "json":
        _print_json_decision(decision)
    else:
        _print_text_decision(decision)

    return 0 if decision.should_alert else 2
