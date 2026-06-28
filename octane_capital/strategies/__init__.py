"""Strategy package.

Intentionally light: import submodules directly (e.g.
`from octane_capital.strategies.swing import generate_swing_proposals`) so that
importing one strategy helper does not pull in market data / yfinance unless the
caller actually needs it.
"""
