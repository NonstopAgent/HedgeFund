"""
Backward-compatible entry point.
Prefer: python -m octane_capital.cli research
"""

from octane_capital.engine import OctaneCapitalEngine


def main():
    engine = OctaneCapitalEngine()
    engine.run_research_cycle()


if __name__ == "__main__":
    main()
