"""CLI sub-command: depwatch webhook — fire a test webhook from the current config."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from depwatch.config import load_config
from depwatch.notifier import DigestPayload
from depwatch.webhook import WebhookConfig, send_webhook

logger = logging.getLogger(__name__)


def add_webhook_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("webhook", help="send a test webhook notification")
    p.add_argument("--config", default="depwatch.yml", help="path to depwatch.yml")
    p.add_argument("--url", required=True, help="webhook endpoint URL")
    p.add_argument("--secret", default=None, help="optional shared secret header")
    p.add_argument("--timeout", type=int, default=10, help="HTTP timeout in seconds")
    p.set_defaults(func=_run_webhook)


def _build_test_payload(cfg) -> DigestPayload:
    """Build a synthetic DigestPayload for testing, using the first configured project.

    If no projects are defined in the config, a placeholder project name is used
    so the webhook still fires with a realistic-looking payload.
    """
    from depwatch.checker import UpdateInfo  # local import to avoid cycles

    project_name = cfg.projects[0].name if cfg.projects else "<no-project>"
    test_updates = [
        UpdateInfo(
            project=project_name,
            package="depwatch-test",
            current_version="0.0.0",
            latest_version="1.0.0",
        )
    ]
    return DigestPayload(updates=test_updates)


def _run_webhook(ns: argparse.Namespace) -> int:
    config_path = Path(ns.config)
    if not config_path.exists():
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        return 1

    try:
        cfg = load_config(config_path)
    except Exception as exc:  # noqa: BLE001
        print(f"error: failed to load config: {exc}", file=sys.stderr)
        return 1

    try:
        wh_cfg = WebhookConfig(url=ns.url, secret=ns.secret, timeout=ns.timeout)
    except ValueError as exc:
        print(f"error: invalid webhook config: {exc}", file=sys.stderr)
        return 1

    payload = _build_test_payload(cfg)

    ok = send_webhook(wh_cfg, payload)
    if ok:
        print(f"webhook delivered successfully to {ns.url}")
        return 0
    else:
        print("error: webhook delivery failed", file=sys.stderr)
        return 2
