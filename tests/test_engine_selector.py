"""Tests for the engine selector module (_engine.py)."""

from __future__ import annotations


class TestEngineSelector:
    def test_rust_available_is_bool(self) -> None:
        from i18n_fastapi._engine import RUST_AVAILABLE

        assert isinstance(RUST_AVAILABLE, bool)

    def test_translation_engine_is_importable(self) -> None:
        from i18n_fastapi._engine import TranslationEngine

        assert TranslationEngine is not None

    def test_engine_has_required_interface(self) -> None:
        from i18n_fastapi._engine import TranslationEngine

        engine = TranslationEngine(default_locale="en")
        assert hasattr(engine, "translate")
        assert hasattr(engine, "load_locale_dir")
        assert hasattr(engine, "auto_discover")
        assert hasattr(engine, "available_locales")
        assert hasattr(engine, "reload")
        assert hasattr(engine, "get_missing_keys")
        assert hasattr(engine, "clear_missing_keys")
        assert hasattr(engine, "has_key")
        assert hasattr(engine, "loaded_directories")

    def test_python_fallback_engine_exists(self) -> None:
        from i18n_fastapi._python_engine import (
            TranslationEngine as PyEngine,
        )

        engine = PyEngine(default_locale="en")
        assert engine.available_locales() == []
