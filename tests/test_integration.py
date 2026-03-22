"""Integration tests: full plugin lifecycle with FastAPI TestClient."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from i18n_fastapi import I18n, I18nConfig, Locale, TranslateFunc, t

FIXTURES = Path(__file__).parent / "fixtures"
LOCALES = str(FIXTURES / "locales")
LOCALES2 = str(FIXTURES / "locales2")


def _create_full_app() -> FastAPI:
    app = FastAPI()
    config = I18nConfig(
        default_locale="en",
        supported_locales=["en", "es"],
        locale_dirs=[LOCALES, LOCALES2],
        auto_discover=False,
        locale_resolvers=[
            "query",
            "cookie",
            "custom_header",
            "accept_language",
        ],
    )
    I18n(app, config=config)

    @app.get("/greet")
    async def greet(locale: Locale, translate: TranslateFunc) -> dict[str, str]:
        return {
            "locale": locale,
            "greeting": translate("messages.greeting", name="FastAPI"),
            "welcome": translate("extra.welcome"),
        }

    @app.get("/plural")
    async def plural() -> dict[str, str]:
        return {
            "zero": t("messages.items.count", count=0),
            "one": t("messages.items.count", count=1),
            "many": t("messages.items.count", count=42),
        }

    return app


@pytest.fixture()
def app() -> FastAPI:
    return _create_full_app()


@pytest.mark.asyncio()
async def test_full_translation_flow(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/greet?lang=en")
        assert resp.status_code == 200
        data = resp.json()
        assert data["locale"] == "en"
        assert data["greeting"] == "Hello FastAPI"
        assert data["welcome"] == "Welcome to the app"


@pytest.mark.asyncio()
async def test_spanish_flow(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/greet", headers={"Accept-Language": "es"})
        data = resp.json()
        assert data["locale"] == "es"
        assert data["greeting"] == "Hola FastAPI"
        # extra.welcome only exists in "en", should fallback
        assert data["welcome"] == "Welcome to the app"


@pytest.mark.asyncio()
async def test_pluralization_endpoint(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/plural")
        data = resp.json()
        assert data["zero"] == "No items"
        assert data["one"] == "1 item"
        assert data["many"] == "42 items"


@pytest.mark.asyncio()
async def test_dependency_injection(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/greet", headers={"X-Language": "es"})
        data = resp.json()
        assert data["locale"] == "es"
