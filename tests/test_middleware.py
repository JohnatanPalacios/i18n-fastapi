"""Tests for the i18n middleware and locale resolvers."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from i18n_fastapi import I18n, I18nConfig, get_locale, t

FIXTURES = Path(__file__).parent / "fixtures"
LOCALES = str(FIXTURES / "locales")


def _create_app(
    resolvers: list[str] | None = None,
    supported_locales: list[str] | None = None,
) -> FastAPI:
    app = FastAPI()
    config = I18nConfig(
        default_locale="en",
        supported_locales=supported_locales or ["en", "es"],
        locale_dirs=[LOCALES],
        auto_discover=False,
        locale_resolvers=resolvers
        or ["query", "cookie", "custom_header", "accept_language"],
        enable_languages_endpoint=True,
    )
    I18n(app, config=config)

    @app.get("/test")
    async def test_route() -> dict[str, str]:
        return {
            "locale": get_locale(),
            "message": t("messages.farewell"),
        }

    return app


@pytest.fixture()
def app() -> FastAPI:
    return _create_app()


@pytest.mark.asyncio()
async def test_default_locale(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["locale"] == "en"
        assert data["message"] == "Goodbye"


@pytest.mark.asyncio()
async def test_accept_language_header(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/test", headers={"Accept-Language": "es"})
        data = resp.json()
        assert data["locale"] == "es"
        assert data["message"] == "Adiós"


@pytest.mark.asyncio()
async def test_query_param(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/test?lang=es")
        data = resp.json()
        assert data["locale"] == "es"


@pytest.mark.asyncio()
async def test_custom_header(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/test", headers={"X-Language": "es"})
        data = resp.json()
        assert data["locale"] == "es"


@pytest.mark.asyncio()
async def test_content_language_header(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/test", headers={"Accept-Language": "es"})
        assert resp.headers.get("content-language") == "es"


@pytest.mark.asyncio()
async def test_unsupported_locale_falls_back(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/test", headers={"Accept-Language": "fr"})
        data = resp.json()
        assert data["locale"] == "en"


@pytest.mark.asyncio()
async def test_languages_endpoint(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/i18n/languages")
        assert resp.status_code == 200
        data = resp.json()
        assert "en" in data["locales"]
        assert "es" in data["locales"]
        assert data["default"] == "en"


@pytest.mark.asyncio()
async def test_resolver_priority() -> None:
    """Query param should override Accept-Language when query is first."""
    app = _create_app(
        resolvers=["query", "accept_language"],
        supported_locales=["en", "es"],
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/test?lang=en",
            headers={"Accept-Language": "es"},
        )
        data = resp.json()
        assert data["locale"] == "en"
