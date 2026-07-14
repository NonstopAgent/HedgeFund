# AGENTS.md

## Cursor Cloud specific instructions

Octane Capital Lab is a **Python 3.12 CLI application** (no web server, no Docker, no
frontend). It orchestrates a research + risk-limited paper-trading pipeline. See
`README.md` for the command reference and `CURSOR_ROBINHOOD_CLAUDE_PLAN.md` for the roadmap.

### Environment
- Dependencies are installed into a virtualenv at `.venv/` (the startup update script
  runs `python3 -m venv .venv` + `pip install -r requirements.txt`). Always invoke the app
  and tests via `.venv/bin/python` (e.g. `.venv/bin/python -m pytest tests/ -q`).
- The app degrades gracefully: with no `SUPABASE_URL`/`SUPABASE_KEY` the Vault falls back
  to local JSON under `.data/vault/` (you'll see a `THE VAULT ... STANDBY` line — this is
  normal, not an error). With no `ANTHROPIC_API_KEY` the Proposal CIO uses a deterministic
  rule-based fallback.

### Running / testing
- Tests: `.venv/bin/python -m pytest tests/ -q`. **Gotcha:** run the suite with **no
  populated `.env` present** (or without an empty `PERPLEXITY_API_KEY=` line).
  `test_config_safety.py::test_no_fallback_api_keys` reloads `config` which re-runs
  `load_dotenv()`; a `.env` containing `PERPLEXITY_API_KEY=` injects an empty string and
  makes that one test fail (`'' is not None`). This is an env artifact, not a code bug.
- Commands that work fully offline / without any API key: `backtest`, `proposals`,
  `risk-check`, `approve`, `cancel`, `execute` (dry-run preview), `grade`, `scoreboard`,
  and `print_risk_config.py`.
- `swing` and live-price `execute` need outbound internet to Yahoo Finance (`yfinance`);
  `MarketData` raises rather than faking a price if the fetch fails.
- `research`, `paper`, and the legacy `predator_engine.py` entry point require
  `PERPLEXITY_API_KEY` — `OctaneCapitalEngine.__init__` calls `config.require_perplexity_key()`
  and raises `ValueError` without it. Add the key as a secret to exercise those flows.

### Lint
- There is **no configured linter** (no ruff/flake8/pylint/pyproject config in the repo).
  For a quick sanity check use `.venv/bin/python -m compileall -q octane_capital scripts predator_engine.py`.

### Safety
- Live trading is OFF by default and multiply guarded. Do not set `ENABLE_LIVE_TRADING=true`
  or `TRADING_MODE=live_manual` unless a task explicitly requires it.
