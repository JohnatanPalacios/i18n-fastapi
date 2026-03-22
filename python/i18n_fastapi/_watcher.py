"""File watcher for hot-reloading translation files during development."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from i18n_fastapi._engine import TranslationEngine

logger = logging.getLogger("i18n_fastapi")


def start_watcher(engine: TranslationEngine) -> Callable[[], None]:
    """Start a background thread that watches loaded locale dirs for changes.

    Returns a stop function that terminates the watcher thread.
    Requires the `watchfiles` package (install via `pip install i18n-fastapi[reload]`).
    """
    from watchfiles import watch

    dirs = engine.loaded_directories()
    if not dirs:
        logger.warning("i18n-fastapi watcher: no directories to watch")
        return lambda: None

    stop_event = threading.Event()

    def _watch_loop() -> None:
        try:
            for _changes in watch(
                *dirs,
                stop_event=stop_event,
                watch_filter=_json_filter,
            ):
                logger.info("i18n-fastapi: translation files changed, reloading...")
                try:
                    engine.reload()
                    logger.info("i18n-fastapi: translations reloaded")
                except Exception:
                    logger.exception("i18n-fastapi: failed to reload translations")
        except Exception:
            if not stop_event.is_set():
                logger.exception("i18n-fastapi: watcher crashed")

    thread = threading.Thread(
        target=_watch_loop,
        daemon=True,
        name="i18n-fastapi-watcher",
    )
    thread.start()

    def stop() -> None:
        stop_event.set()
        thread.join(timeout=2)

    return stop


def _json_filter(change: Any, path: str) -> bool:
    """Only react to .json file changes."""
    return path.endswith(".json")
