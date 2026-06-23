#!/usr/bin/env python3
"""Convenience script to run the paper trading cycle."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from octane_capital.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["paper"]))
