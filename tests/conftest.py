"""Shared fixtures for i18n-fastapi tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from i18n_fastapi._python_engine import TranslationEngine

FIXTURES_DIR = Path(__file__).parent / "fixtures"
LOCALES_DIR = FIXTURES_DIR / "locales"
LOCALES2_DIR = FIXTURES_DIR / "locales2"


@pytest.fixture()
def engine() -> TranslationEngine:
    """Create a fresh engine loaded with the test fixtures."""
    eng = TranslationEngine(default_locale="en")
    eng.load_locale_dir(str(LOCALES_DIR))
    return eng


@pytest.fixture()
def empty_engine() -> TranslationEngine:
    """Create an engine with no translations loaded."""
    return TranslationEngine(default_locale="en")
