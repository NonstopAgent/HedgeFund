"""Walk-forward validation — placeholder for future parameter tuning."""

from typing import Any


def walk_forward_split(data: list, train_ratio: float = 0.7) -> tuple[list, list]:
    """Simple train/test split for walk-forward backtests."""
    split = int(len(data) * train_ratio)
    return data[:split], data[split:]
