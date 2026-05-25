"""CLI sub-command: depwatch escalation"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from depwatch.config import load_config
from depwatch.digest import build_all_digests
from depwatch.escalation import EscalationRule, escalate_all
from depwatch.runner import _collect_updates
from depwatch.state import load_state


def add_escalation_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("escalation", help="Show updates that are overdue for action")
    p.add_argument("--config", default="depwatch.yml")
    p.add_argument("--min-days", type=int, default=7,
                   help="Days overdue before escalating (default: 7)")
    p.add_argument("--major-only", action="store_true",
                   help="Only escalate major version bumps")
    p.add_argument("--channel", default="email",
                   help="Channel label to attach (default: email)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=_run_escalation)


def _run_escalation(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config not found: {args.config}", file=sys.stderr)
        return 1

    try:
        rule = EscalationRule(
            min_overdue_days=args.min_days,
            require_major=args.major_only,
            channel=args.channel,
        )
    except ValueError as exc:
        print(f"Invalid escalation rule: {exc}", file=sys.stderr)
        return 1

    state = load_state(cfg.state_file)
    updates_by_project = _collect_updates(cfg, state)
    digests = build_all_digests(cfg, updates_by_project)
    now = datetime.now(timezone.utc)
    escalated = escalate_all(digests, rule, now)

    if args.format == "json":
        print(json.dumps([e.to_dict() for e in escalated], indent=2))
    else:
        if not escalated:
            print("No escalations.")
        else:
            for e in escalated:
                print(
                    f"[{e.rule.channel.upper()}] {e.project}/{e.update.package} "
                    f"{e.update.current} -> {e.update.latest} "
                    f"(overdue {e.overdue_days}d)"
                )
    return 0
