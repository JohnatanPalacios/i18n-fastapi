"""Tests for individual locale resolvers (path_prefix, cookie)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from i18n_fastapi import I18n, I18nConfig, get_locale

FIXTURES = Path(__file__).parent / "fixtures"
LOCALES = str(FIXTURES / "locales")


def _app_with_resolvers(resolvers: list[str]) -> FastAPI:
    app = FastAPI()
    config = I18nConfig(
        default_locale="en",
        supported_locales=["en", "es"],
        locale_dirs=[LOCALES],
        auto_discover=False,
        locale_resolvers=resolvers,
        enable_languages_endpoint=False,
    )
    I18n(app, config=config)

    @app.get("/info")
    @app.get("/{lang_prefix}/info")
    async def info() -> dict[str, str]:
        return {"locale": get_locale()}

    return app


@pytest.mark.asyncio()
async def test_path_prefix_resolver() -> None:
    app = _app_with_resolvers(["path_prefix"])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/es/info")
        assert resp.json()["locale"] == "es"


@pytest.mark.asyncio()
async def test_path_prefix_fallback_on_non_locale_path() -> None:
    app = _app_with_resolvers(["path_prefix"])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/info")
        assert resp.json()["locale"] == "en"


@pytest.mark.asyncio()
async def test_cookie_resolver() -> None:
    app = _app_with_resolvers(["cookie"])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        client.cookies.set("lang", "es")
        resp = await client.get("/info")
        assert resp.json()["locale"] == "es"


@pytest.mark.asyncio()
async def test_cookie_resolver_missing_cookie() -> None:
    app = _app_with_resolvers(["cookie"])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/info")
        assert resp.json()["locale"] == "en"


@pytest.mark.asyncio()
async def test_combined_resolver_order() -> None:
    """Cookie should win over path_prefix when cookie is first."""
    app = _app_with_resolvers(["cookie", "path_prefix"])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        client.cookies.set("lang", "en")
        resp = await client.get("/es/info")
        assert resp.json()["locale"] == "en"
