"""
Octane Capital Lab - CLI
Safe entry points for research, paper trading, and execution (later phases).
"""

import argparse
import sys

from octane_capital.config import config


def cmd_research(_args: argparse.Namespace) -> int:
    """Run the research cycle (Scout → CIO → Auditor → Vault)."""
    try:
        from octane_capital.engine import OctaneCapitalEngine

        engine = OctaneCapitalEngine()
        engine.run_research_cycle()
        return 0
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Research cycle failed: {e}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="octane_capital",
        description="Octane Capital Lab — research, paper trading, and risk-limited execution.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    research_parser = subparsers.add_parser(
        "research",
        help="Run Scout/Auditor research cycle (no trading)",
    )
    research_parser.set_defaults(func=cmd_research)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
