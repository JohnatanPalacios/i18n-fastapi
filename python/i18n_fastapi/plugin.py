"""I18n plugin: one-line integration for FastAPI applications."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from i18n_fastapi._engine import TranslationEngine
from i18n_fastapi.config import I18nConfig
from i18n_fastapi.context import _init_context
from i18n_fastapi.middleware import I18nMiddleware
from i18n_fastapi.router import create_i18n_router

logger = logging.getLogger("i18n_fastapi")


class I18n:
    """FastAPI i18n plugin.

    Usage::

        app = FastAPI()
        i18n = I18n(app)

    Or with custom configuration::

        config = I18nConfig(default_locale="es", locales_dir="translations")
        i18n = I18n(app, config=config)
    """

    def __init__(
        self,
        app: FastAPI,
        config: I18nConfig | None = None,
    ) -> None:
        self.config = config or I18nConfig()
        self.engine = TranslationEngine(
            default_locale=self.config.default_locale,
            raise_on_duplicate=self.config.raise_on_duplicate_keys,
            locale_dir_name=self.config.locales_dir,
        )

        _init_context(
            self.engine,
            self.config.default_locale,
            self.config.log_missing_keys,
        )

        self._load_translations()
        self._wrap_lifespan(app)

        app.add_middleware(
            I18nMiddleware,
            resolver_order=self.config.locale_resolvers,
            default_locale=self.config.default_locale,
            supported_locales=self.config.supported_locales,
            set_content_language_header=self.config.set_content_language_header,
            query_param_name=self.config.query_param_name,
            cookie_name=self.config.cookie_name,
            custom_header_name=self.config.custom_header_name,
        )

        if self.config.enable_languages_endpoint:
            router = create_i18n_router(self.engine, self.config)
            app.include_router(router)

    def add_locale_dir(self, path: str) -> None:
        """Register an additional locale directory at runtime."""
        self.engine.load_locale_dir(str(Path(path).resolve()))

    def _load_translations(self) -> None:
        for locale_dir in self.config.locale_dirs:
            resolved = str(Path(locale_dir).resolve())
            self.engine.load_locale_dir(resolved)

        if self.config.auto_discover:
            root = str(Path.cwd())
            self.engine.auto_discover(root)

        loaded = self.engine.available_locales()
        logger.info(
            "i18n-fastapi: loaded %d locale(s): %s",
            len(loaded),
            ", ".join(loaded),
        )

    def _wrap_lifespan(self, app: FastAPI) -> None:
        original_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def lifespan_wrapper(
            application: FastAPI,
        ) -> AsyncGenerator[dict[str, Any], None]:
            self._start_watcher()

            if original_lifespan is not None:
                async with original_lifespan(application) as state:
                    yield state if state else {}
            else:
                yield {}

            self._stop_watcher()

        app.router.lifespan_context = lifespan_wrapper

    def _start_watcher(self) -> None:
        if not self.config.hot_reload:
            return

        try:
            from i18n_fastapi._watcher import start_watcher

            self._watcher_stop = start_watcher(self.engine)
            logger.info("i18n-fastapi: hot reload enabled")
        except ImportError:
            logger.warning(
                "i18n-fastapi: hot_reload requires 'watchfiles'. "
                "Install with: pip install i18n-fastapi[reload]"
            )
        except Exception:
            logger.exception("i18n-fastapi: failed to start watcher")

    def _stop_watcher(self) -> None:
        stop_fn = getattr(self, "_watcher_stop", None)
        if stop_fn is not None:
            stop_fn()
