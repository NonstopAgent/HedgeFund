"""Position sizing helpers — deterministic, not LLM-driven."""


def calculate_max_notional(
    account_equity: float,
    max_position_pct: float,
    max_single_trade_dollars: float,
) -> float:
    return min(account_equity * max_position_pct, max_single_trade_dollars)


def confidence_size_multiplier(confidence: float) -> float:
    if confidence >= 9.0:
        return 1.0
    if confidence >= 8.0:
        return 0.65
    if confidence >= 7.5:
        return 0.35
    return 0.0


def risk_level_multiplier(risk_level: str) -> float:
    level = risk_level.strip().lower()
    if level == "low":
        return 1.0
    if level == "medium":
        return 0.7
    if level == "high":
        return 0.35
    return 0.7
