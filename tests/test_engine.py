"""Tests for the translation engine (Python fallback)."""

from __future__ import annotations

from pathlib import Path

import pytest
from i18n_fastapi._python_engine import TranslationEngine

FIXTURES = Path(__file__).parent / "fixtures"
LOCALES = FIXTURES / "locales"
LOCALES2 = FIXTURES / "locales2"


class TestLoadAndTranslate:
    def test_simple_translation(self, engine: TranslationEngine) -> None:
        result = engine.translate("messages.farewell", "en")
        assert result == "Goodbye"

    def test_translation_with_interpolation(self, engine: TranslationEngine) -> None:
        result = engine.translate("messages.greeting", "en", {"name": "World"})
        assert result == "Hello World"

    def test_spanish_translation(self, engine: TranslationEngine) -> None:
        result = engine.translate("messages.farewell", "es")
        assert result == "Adiós"

    def test_nested_key(self, engine: TranslationEngine) -> None:
        result = engine.translate("messages.errors.notFound", "en", {"id": "42"})
        assert result == "Resource 42 not found"

    def test_fallback_to_default_locale(self, engine: TranslationEngine) -> None:
        result = engine.translate("messages.farewell", "fr")
        assert result == "Goodbye"

    def test_missing_key_returns_key(self, engine: TranslationEngine) -> None:
        result = engine.translate("nonexistent.key", "en")
        assert result == "nonexistent.key"


class TestPluralization:
    def test_zero(self, engine: TranslationEngine) -> None:
        result = engine.translate("messages.items.count", "en", {"count": "0"})
        assert result == "No items"

    def test_one(self, engine: TranslationEngine) -> None:
        result = engine.translate("messages.items.count", "en", {"count": "1"})
        assert result == "1 item"

    def test_other(self, engine: TranslationEngine) -> None:
        result = engine.translate("messages.items.count", "en", {"count": "5"})
        assert result == "5 items"

    def test_plural_spanish(self, engine: TranslationEngine) -> None:
        result = engine.translate("messages.items.count", "es", {"count": "0"})
        assert result == "Sin elementos"


class TestAvailableLocales:
    def test_returns_sorted_locales(self, engine: TranslationEngine) -> None:
        assert engine.available_locales() == ["en", "es"]


class TestMissingKeys:
    def test_tracks_missing_keys(self, engine: TranslationEngine) -> None:
        engine.translate("missing.one", "en")
        engine.translate("missing.two", "es")
        missing = engine.get_missing_keys()
        assert ("missing.one", "en") in missing
        assert ("missing.two", "es") in missing

    def test_clear_missing_keys(self, engine: TranslationEngine) -> None:
        engine.translate("missing.x", "en")
        engine.clear_missing_keys()
        assert engine.get_missing_keys() == []


class TestDuplicateKeys:
    def test_duplicate_key_raises(self) -> None:
        eng = TranslationEngine(default_locale="en", raise_on_duplicate=True)
        eng.load_locale_dir(str(LOCALES))

        with pytest.raises(ValueError, match="DuplicateKeyError"):
            eng.load_locale_dir(str(LOCALES))

    def test_duplicate_key_allowed_when_disabled(self) -> None:
        eng = TranslationEngine(default_locale="en", raise_on_duplicate=False)
        eng.load_locale_dir(str(LOCALES))
        eng.load_locale_dir(str(LOCALES))
        assert eng.translate("messages.farewell", "en") == "Goodbye"


class TestHasKey:
    def test_existing_key(self, engine: TranslationEngine) -> None:
        assert engine.has_key("messages.farewell", "en") is True

    def test_nonexistent_key(self, engine: TranslationEngine) -> None:
        assert engine.has_key("nope", "en") is False

    def test_fallback_key(self, engine: TranslationEngine) -> None:
        assert engine.has_key("messages.farewell", "fr") is True


class TestReload:
    def test_reload_reloads_translations(self, engine: TranslationEngine) -> None:
        assert engine.translate("messages.farewell", "en") == "Goodbye"
        engine.reload()
        assert engine.translate("messages.farewell", "en") == "Goodbye"


class TestMultipleDirectories:
    def test_load_second_directory(self) -> None:
        eng = TranslationEngine(default_locale="en")
        eng.load_locale_dir(str(LOCALES))
        eng.load_locale_dir(str(LOCALES2))
        assert eng.translate("extra.welcome", "en") == "Welcome to the app"
        assert eng.translate("messages.farewell", "en") == "Goodbye"
