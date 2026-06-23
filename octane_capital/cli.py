"""Octane Capital Lab - command line interface.

Phase 1 exposes a single ``research`` command. Trading-related commands
(paper, proposals, execute, ...) are intentionally not implemented yet and
will be added in later phases once the risk engine and broker layer exist.

Usage:
    python -m octane_capital.cli research
"""

import argparse
import sys


def _cmd_research(_args: argparse.Namespace) -> int:
    """Run the research cycle (Scout -> CIO -> Auditor -> Vault)."""
    from .config import config
    from .octane_branding import print_agent_status

    if not config.has_perplexity():
        print_agent_status(
            "SYSTEM",
            "ERROR",
            "PERPLEXITY_API_KEY is not set. Copy .env.example to .env and add your key.",
        )
        return 1

    # Import the engine lazily so `--help` and config validation do not pay the
    # cost of importing CrewAI and friends.
    from .engine import OctaneCapitalEngine

    engine = OctaneCapitalEngine()
    engine.run_research_cycle()
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="octane_capital",
        description="Octane Capital Lab - AI investment research engine.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    research = subparsers.add_parser(
        "research",
        help="Run the research cycle (Scout -> CIO -> Auditor -> Vault).",
    )
    research.set_defaults(func=_cmd_research)

    return parser


def main(argv=None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
