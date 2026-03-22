"""FastAPI dependencies for injecting locale and translation functions."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends

from i18n_fastapi.context import get_locale, t


def _get_locale() -> str:
    return get_locale()


def _get_translate_func() -> Any:
    return t


Locale = Annotated[str, Depends(_get_locale)]
"""Inject the current request locale as a string."""

TranslateFunc = Annotated[Any, Depends(_get_translate_func)]
"""Inject the translation function `t` bound to the current request locale."""
