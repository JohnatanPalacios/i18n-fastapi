"""Engine selector: imports Rust native engine or falls back to pure Python."""

from __future__ import annotations

import logging
import warnings

logger = logging.getLogger("i18n_fastapi")

RUST_AVAILABLE: bool

try:
    from i18n_fastapi._native import TranslationEngine  # type: ignore[import-not-found]

    RUST_AVAILABLE = True
except ImportError:
    from i18n_fastapi._python_engine import (
        TranslationEngine,  # type: ignore[assignment]
    )

    RUST_AVAILABLE = False
    warnings.warn(
        "i18n-fastapi: Rust engine not available, using Python fallback. "
        "Install from a pre-compiled wheel for best performance.",
        RuntimeWarning,
        stacklevel=2,
    )

__all__ = ["RUST_AVAILABLE", "TranslationEngine"]
