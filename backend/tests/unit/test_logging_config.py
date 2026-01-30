import logging

import pytest

from app.core.logging_config import _resolve_log_level


def test_resolve_log_level_defaults_to_info(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert _resolve_log_level() == logging.INFO


def test_resolve_log_level_uses_env_value(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    assert _resolve_log_level() == logging.DEBUG


def test_resolve_log_level_rejects_invalid_value(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "NOTALEVEL")
    with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
        _resolve_log_level()
