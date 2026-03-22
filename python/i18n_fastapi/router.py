"""Optional router that exposes translation metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter

if TYPE_CHECKING:
    from i18n_fastapi._engine import TranslationEngine
    from i18n_fastapi.config import I18nConfig


def create_i18n_router(engine: TranslationEngine, config: I18nConfig) -> APIRouter:
    """Build an APIRouter with the languages endpoint."""
    router = APIRouter(tags=["i18n"])

    @router.get(config.languages_endpoint_path)
    async def get_languages() -> dict[str, Any]:
        from i18n_fastapi.context import get_locale

        return {
            "locales": engine.available_locales(),
            "default": config.default_locale,
            "current": get_locale(),
        }

    return router
