"""CLI sub-command: depwatch graph — show cross-project dependency graph."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.config import Config, load_config
from depwatch.dependency_graph import build_graph
from depwatch.digest import build_all_digests
from depwatch.runner import _collect_updates
from depwatch.state import load_state


def add_graph_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("graph", help="Show cross-project dependency graph")
    p.add_argument("--config", default="depwatch.yml", help="Config file path")
    p.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    p.add_argument(
        "--shared-only",
        action="store_true",
        help="Only show packages shared across multiple projects",
    )
    p.set_defaults(func=_run_graph)


def _print_text(graph, shared_only: bool) -> None:
    nodes = graph.shared_packages() if shared_only else list(graph.nodes.values())
    if not nodes:
        print("No packages found.")
        return
    for node in sorted(nodes, key=lambda n: n.package):
        projects = ", ".join(sorted(node.projects))
        shared_tag = " [shared]" if len(node.projects) > 1 else ""
        print(
            f"{node.package} ({node.language}) {node.current_version} -> "
            f"{node.latest_version}  projects=[{projects}]{shared_tag}"
        )


def _run_graph(args: argparse.Namespace) -> int:
    try:
        cfg: Config = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    state = load_state(cfg.state_file if hasattr(cfg, "state_file") else "depwatch_state.json")
    all_updates = _collect_updates(cfg, state)
    digests = build_all_digests(cfg, all_updates)
    graph = build_graph(digests)

    if args.format == "json":
        data = graph.to_dict()
        if args.shared_only:
            data["nodes"] = [n.to_dict() for n in graph.shared_packages()]
        print(json.dumps(data, indent=2))
    else:
        _print_text(graph, args.shared_only)
    return 0
