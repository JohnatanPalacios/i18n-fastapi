"""Tests for the I18n plugin class."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from i18n_fastapi import I18n, I18nConfig, t

FIXTURES = Path(__file__).parent / "fixtures"
LOCALES = str(FIXTURES / "locales")
LOCALES2 = str(FIXTURES / "locales2")


class TestAddLocaleDir:
    def test_add_locale_dir_at_runtime(self) -> None:
        app = FastAPI()
        config = I18nConfig(
            locale_dirs=[LOCALES],
            auto_discover=False,
        )
        i18n = I18n(app, config=config)

        assert t("extra.welcome") == "extra.welcome"

        i18n.add_locale_dir(LOCALES2)

        assert t("extra.welcome") == "Welcome to the app"


class TestDisableLanguagesEndpoint:
    @pytest.mark.asyncio()
    async def test_no_languages_endpoint(self) -> None:
        app = FastAPI()
        config = I18nConfig(
            locale_dirs=[LOCALES],
            auto_discover=False,
            enable_languages_endpoint=False,
        )
        I18n(app, config=config)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/i18n/languages")
            assert resp.status_code == 404


class TestCustomEndpointPath:
    @pytest.mark.asyncio()
    async def test_custom_languages_path(self) -> None:
        app = FastAPI()
        config = I18nConfig(
            locale_dirs=[LOCALES],
            auto_discover=False,
            languages_endpoint_path="/api/locales",
        )
        I18n(app, config=config)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/locales")
            assert resp.status_code == 200
            data = resp.json()
            assert "en" in data["locales"]


class TestDefaultConfig:
    def test_plugin_with_no_config(self) -> None:
        app = FastAPI()
        i18n = I18n(app, config=I18nConfig(auto_discover=False))
        assert i18n.config.default_locale == "en"
        assert i18n.config.locales_dir == "locales"


class TestPreservesOriginalLifespan:
    @pytest.mark.asyncio()
    async def test_user_lifespan_runs(self) -> None:
        lifespan_ran = {"startup": False, "shutdown": False}

        from collections.abc import AsyncGenerator
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def user_lifespan(
            _app: FastAPI,
        ) -> AsyncGenerator[dict[str, str], None]:
            lifespan_ran["startup"] = True
            yield {"custom": "state"}
            lifespan_ran["shutdown"] = True

        app = FastAPI(lifespan=user_lifespan)
        I18n(
            app,
            config=I18nConfig(locale_dirs=[LOCALES], auto_discover=False),
        )

        @app.get("/check")
        async def check() -> dict[str, str]:
            return {"ok": "true"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/check")
            assert resp.status_code == 200
