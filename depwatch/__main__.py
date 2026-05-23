"""Entry point: load config and start the depwatch scheduler daemon."""

import argparse
import logging
import sys
from pathlib import Path

from depwatch.config import load_config
from depwatch.scheduler import Scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("depwatch")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="depwatch",
        description="Monitor Python/Go dependencies and send digest alerts.",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="depwatch.yml",
        help="Path to configuration file (default: depwatch.yml)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single check cycle and exit instead of looping.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)

    if not config_path.exists():
        logger.error("Config file not found: %s", config_path)
        return 1

    try:
        config = load_config(config_path)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to load config: %s", exc)
        return 1

    scheduler = Scheduler(config)

    if args.once:
        logger.info("Running single check cycle (--once mode)")
        payload = scheduler.run_once()
        if payload.is_empty():
            logger.info("No updates found.")
        else:
            print(payload.format_text())
        return 0

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        scheduler.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
