"""Translation context: ContextVar for per-request locale and the t() helper."""

from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from i18n_fastapi._engine import TranslationEngine

logger = logging.getLogger("i18n_fastapi")

language_ctx: ContextVar[str] = ContextVar("language_ctx", default="en")

_engine: TranslationEngine | None = None
_log_missing: bool = True


def _init_context(
    engine: TranslationEngine,
    default_locale: str,
    log_missing: bool,
) -> None:
    """Called once by the plugin to bind the engine to this module."""
    global _engine, _log_missing
    _engine = engine
    _log_missing = log_missing
    language_ctx.set(default_locale)


def get_locale() -> str:
    """Return the current request locale."""
    return language_ctx.get()


def t(key: str, **kwargs: Any) -> str:
    """Translate a key using the current request locale.

    Keyword arguments are passed as interpolation parameters.
    If a `count` kwarg is present, ICU plural selection is applied.
    """
    if _engine is None:
        return key

    locale = language_ctx.get()
    params = {k: str(v) for k, v in kwargs.items()}
    result = _engine.translate(key, locale, params)

    if result == key and _log_missing:
        logger.warning("i18n missing key: '%s' [locale=%s]", key, locale)

    return result
