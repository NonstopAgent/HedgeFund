"""Config safety tests."""

import os
import importlib


def reload_config():
    import octane_capital.config as cfg_module

    return importlib.reload(cfg_module)


def test_default_trading_mode_is_research(monkeypatch):
    monkeypatch.delenv("TRADING_MODE", raising=False)
    cfg = reload_config()
    assert cfg.config.TRADING_MODE == "research"


def test_live_trading_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_LIVE_TRADING", raising=False)
    cfg = reload_config()
    assert cfg.config.ENABLE_LIVE_TRADING is False


def test_no_fallback_api_keys(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    cfg = reload_config()
    assert cfg.config.PERPLEXITY_API_KEY is None


def test_require_perplexity_key_raises(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    cfg = reload_config()
    try:
        cfg.config.require_perplexity_key()
        assert False, "expected ValueError"
    except ValueError as e:
        assert "PERPLEXITY_API_KEY" in str(e)
