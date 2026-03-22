"""Tests for configuration defaults and validation."""

from __future__ import annotations

from i18n_fastapi.config import I18nConfig


class TestDefaults:
    def test_default_locale(self) -> None:
        config = I18nConfig()
        assert config.default_locale == "en"

    def test_default_locales_dir(self) -> None:
        config = I18nConfig()
        assert config.locales_dir == "locales"

    def test_default_resolvers(self) -> None:
        config = I18nConfig()
        assert config.locale_resolvers == [
            "query",
            "cookie",
            "custom_header",
            "accept_language",
            "path_prefix",
        ]

    def test_default_query_param(self) -> None:
        config = I18nConfig()
        assert config.query_param_name == "lang"

    def test_default_raise_on_duplicate(self) -> None:
        config = I18nConfig()
        assert config.raise_on_duplicate_keys is True

    def test_default_hot_reload_off(self) -> None:
        config = I18nConfig()
        assert config.hot_reload is False


class TestCustomConfig:
    def test_custom_locale(self) -> None:
        config = I18nConfig(default_locale="es")
        assert config.default_locale == "es"

    def test_custom_resolvers(self) -> None:
        config = I18nConfig(locale_resolvers=["accept_language", "query"])
        assert config.locale_resolvers == ["accept_language", "query"]

    def test_supported_locales(self) -> None:
        config = I18nConfig(supported_locales=["en", "es", "fr"])
        assert config.supported_locales == ["en", "es", "fr"]

    def test_frozen_config(self) -> None:
        config = I18nConfig()
        import pytest
        from pydantic import ValidationError

        with pytest.raises((ValidationError, TypeError)):
            config.default_locale = "fr"  # type: ignore[misc]
