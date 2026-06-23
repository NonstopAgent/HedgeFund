"""Legacy entry point for the Octane Capital Lab research engine."""

from octane_capital.engine import OctaneCapitalEngine, PredatorEngine, main


__all__ = ["OctaneCapitalEngine", "PredatorEngine", "main"]


if __name__ == "__main__":
    main()
