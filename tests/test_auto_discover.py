"""Tests for auto_discover functionality."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from i18n_fastapi._python_engine import TranslationEngine


class TestAutoDiscover:
    def test_auto_discover_finds_locale_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text("")
            locale_dir = root / "locales" / "en"
            locale_dir.mkdir(parents=True)
            (locale_dir / "greet.json").write_text(json.dumps({"hello": "Hello"}))

            engine = TranslationEngine(default_locale="en", locale_dir_name="locales")
            engine.auto_discover(str(root))

            assert engine.translate("greet.hello", "en") == "Hello"
            assert "en" in engine.available_locales()

    def test_auto_discover_finds_nested_locale_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text("")

            shared = root / "shared" / "locales" / "en"
            shared.mkdir(parents=True)
            (shared / "common.json").write_text(json.dumps({"ok": "OK"}))

            module = root / "modules" / "billing" / "locales" / "en"
            module.mkdir(parents=True)
            (module / "billing.json").write_text(json.dumps({"paid": "Paid"}))

            engine = TranslationEngine(
                default_locale="en",
                raise_on_duplicate=False,
                locale_dir_name="locales",
            )
            engine.auto_discover(str(root))

            assert engine.translate("common.ok", "en") == "OK"
            assert engine.translate("billing.paid", "en") == "Paid"

    def test_auto_discover_skips_venv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text("")

            venv_locale = root / ".venv" / "locales" / "en"
            venv_locale.mkdir(parents=True)
            (venv_locale / "hidden.json").write_text(json.dumps({"secret": "nope"}))

            engine = TranslationEngine(default_locale="en", locale_dir_name="locales")
            engine.auto_discover(str(root))

            assert engine.translate("hidden.secret", "en") == "hidden.secret"

    def test_auto_discover_custom_dir_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text("")

            custom = root / "translations" / "en"
            custom.mkdir(parents=True)
            (custom / "app.json").write_text(json.dumps({"title": "My App"}))

            engine = TranslationEngine(
                default_locale="en",
                locale_dir_name="translations",
            )
            engine.auto_discover(str(root))

            assert engine.translate("app.title", "en") == "My App"
