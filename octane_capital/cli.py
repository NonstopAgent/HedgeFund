"""Command line interface for Octane Capital Lab."""

from __future__ import annotations

import argparse
import sys

from octane_capital.config import ConfigError, config


def run_research(_: argparse.Namespace) -> int:
    """Run a research-only cycle."""
    try:
        from octane_capital.engine import OctaneCapitalEngine
    except ImportError as exc:
        print(
            "Missing dependency while loading the research engine. "
            "Install dependencies with: pip install -r requirements.txt"
        )
        print(f"Details: {exc}")
        return 2

    try:
        engine = OctaneCapitalEngine()
        engine.run_research_cycle()
        return 0
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        prog="octane-capital",
        description=(
            "Octane Capital Lab CLI. Phase 1 supports research mode only; "
            "live trading is not implemented."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    research = subparsers.add_parser(
        "research",
        help="Run the research-only Scout/CIO/Auditor cycle.",
    )
    research.set_defaults(func=run_research)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    config.validate_live_trading_disabled_by_default()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
