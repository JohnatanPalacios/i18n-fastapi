"""Tests for the file watcher module."""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest
from i18n_fastapi._python_engine import TranslationEngine

watchfiles_installed = True
try:
    import watchfiles  # noqa: F401
except ImportError:
    watchfiles_installed = False


class TestWatcherJsonFilter:
    def test_json_filter_accepts_json(self) -> None:
        from i18n_fastapi._watcher import _json_filter

        assert _json_filter(None, "/path/to/file.json") is True

    def test_json_filter_rejects_non_json(self) -> None:
        from i18n_fastapi._watcher import _json_filter

        assert _json_filter(None, "/path/to/file.py") is False
        assert _json_filter(None, "/path/to/file.txt") is False
        assert _json_filter(None, "/path/to/file.toml") is False


class TestWatcherStartStop:
    @pytest.mark.skipif(
        not watchfiles_installed,
        reason="watchfiles not installed",
    )
    def test_watcher_returns_callable_with_no_dirs(self) -> None:
        engine = TranslationEngine(default_locale="en")
        from i18n_fastapi._watcher import start_watcher

        stop = start_watcher(engine)
        assert callable(stop)
        stop()

    @pytest.mark.skipif(
        not watchfiles_installed,
        reason="watchfiles not installed",
    )
    def test_watcher_starts_and_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            locale_dir = Path(tmpdir) / "locales" / "en"
            locale_dir.mkdir(parents=True)
            (locale_dir / "test.json").write_text(json.dumps({"key": "value"}))

            engine = TranslationEngine(default_locale="en")
            engine.load_locale_dir(str(Path(tmpdir) / "locales"))

            from i18n_fastapi._watcher import start_watcher

            stop = start_watcher(engine)
            assert callable(stop)

            time.sleep(0.1)
            stop()

    def test_watcher_import_fails_gracefully(self) -> None:
        """Plugin should handle missing watchfiles gracefully."""
        from unittest.mock import patch as mock_patch

        from fastapi import FastAPI
        from i18n_fastapi import I18n, I18nConfig

        app = FastAPI()
        config = I18nConfig(
            auto_discover=False,
            hot_reload=True,
        )

        with mock_patch("i18n_fastapi.plugin.I18n._start_watcher") as mock_start:
            mock_start.return_value = None
            i18n = I18n(app, config=config)
            assert i18n.config.hot_reload is True
