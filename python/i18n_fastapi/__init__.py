"""i18n-fastapi: High-performance i18n for FastAPI with Rust-powered engine."""

from i18n_fastapi.config import I18nConfig
from i18n_fastapi.context import get_locale, t
from i18n_fastapi.dependencies import Locale, TranslateFunc
from i18n_fastapi.plugin import I18n

__all__ = [
    "I18n",
    "I18nConfig",
    "Locale",
    "TranslateFunc",
    "get_locale",
    "t",
]
