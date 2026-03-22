"""Pure Python fallback translation engine.

Provides the same interface as the Rust-native TranslationEngine.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import orjson

logger = logging.getLogger("i18n_fastapi")

ICU_KEYS = frozenset({"zero", "one", "two", "few", "many", "other"})

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def _interpolate(template: str, params: dict[str, str]) -> str:
    if not params or "{" not in template:
        return template

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return params.get(key, match.group(0))

    return _PLACEHOLDER_RE.sub(_replace, template)


def _select_plural(forms: dict[str, str], count: int) -> str:
    if count == 0 and "zero" in forms:
        return forms["zero"]
    if count == 1 and "one" in forms:
        return forms["one"]
    if count == 2 and "two" in forms:
        return forms["two"]
    if 3 <= count <= 10 and "few" in forms:
        return forms["few"]
    if 11 <= count <= 99 and "many" in forms:
        return forms["many"]
    return forms["other"]


def _is_plural_object(obj: dict[str, Any]) -> bool:
    keys = set(obj.keys())
    return "other" in keys and keys <= ICU_KEYS and len(keys) >= 2


def _find_project_root(start_path: Path) -> Path:
    current = start_path if start_path.is_dir() else start_path.parent

    while True:
        if (
            (current / ".git").exists()
            or (current / "pyproject.toml").exists()
            or (current / "setup.py").exists()
            or (current / "setup.cfg").exists()
        ):
            return current

        parent = current.parent
        if parent == current:
            return start_path
        current = parent


_SKIP_DIRS = frozenset(
    {
        "__pycache__",
        "venv",
        ".venv",
        "env",
        "node_modules",
        "dist",
        "target",
    }
)


def _scan_locale_dirs(root: Path, dir_name: str) -> list[Path]:
    results: list[Path] = []
    _scan_recursive(root, dir_name, results)
    return results


def _scan_recursive(directory: Path, target_name: str, results: list[Path]) -> None:
    try:
        entries = list(directory.iterdir())
    except PermissionError:
        return

    for entry in entries:
        if not entry.is_dir():
            continue

        name = entry.name
        if name.startswith(".") or name in _SKIP_DIRS:
            continue

        if name == target_name:
            results.append(entry)
        else:
            _scan_recursive(entry, target_name, results)


class TranslationEngine:
    """Pure Python translation engine (fallback when Rust is unavailable)."""

    def __init__(
        self,
        default_locale: str,
        raise_on_duplicate: bool = True,
        locale_dir_name: str = "locales",
    ) -> None:
        self.default_locale = default_locale
        self.raise_on_duplicate = raise_on_duplicate
        self.locale_dir_name = locale_dir_name
        self._translations: dict[str, dict[str, Any]] = {}
        self._loaded_dirs: list[Path] = []
        self._missing_keys: list[tuple[str, str]] = []

    def auto_discover(self, root_path: str) -> None:
        """Auto-discover locale directories starting from root_path."""
        root = Path(root_path)
        project_root = _find_project_root(root)
        dirs = _scan_locale_dirs(project_root, self.locale_dir_name)
        for d in dirs:
            self._load_dir(d)

    def load_locale_dir(self, path: str) -> None:
        """Load a specific locale directory."""
        self._load_dir(Path(path))

    def translate(
        self,
        key: str,
        locale: str,
        params: dict[str, str] | None = None,
    ) -> str:
        """Translate a key with optional parameters."""
        if params is None:
            params = {}

        val = self._lookup(key, locale)

        if val is None:
            self._missing_keys.append((key, locale))
            return key

        if isinstance(val, dict) and _is_plural_object(val):
            count = int(params.get("count", "0"))
            template = _select_plural(val, count)
            return _interpolate(template, params)

        if isinstance(val, str):
            return _interpolate(val, params)

        return str(val)

    def available_locales(self) -> list[str]:
        """Return all loaded locale codes."""
        return sorted(self._translations.keys())

    def reload(self) -> None:
        """Reload all previously loaded directories."""
        dirs = list(self._loaded_dirs)
        self._translations.clear()
        self._missing_keys.clear()
        for d in dirs:
            self._load_dir(d)

    def get_missing_keys(self) -> list[tuple[str, str]]:
        """Return accumulated missing key lookups."""
        return list(self._missing_keys)

    def clear_missing_keys(self) -> None:
        """Clear the missing keys log."""
        self._missing_keys.clear()

    def has_key(self, key: str, locale: str) -> bool:
        """Check if a translation key exists for a locale."""
        return self._lookup(key, locale) is not None

    def loaded_directories(self) -> list[str]:
        """Return loaded directory paths."""
        return [str(p) for p in self._loaded_dirs]

    def _load_dir(self, locale_dir: Path) -> None:
        if not locale_dir.exists() or not locale_dir.is_dir():
            return

        for lang_dir in sorted(locale_dir.iterdir()):
            if not lang_dir.is_dir():
                continue

            lang = lang_dir.name
            lang_map = self._translations.setdefault(lang, {})

            for json_file in sorted(lang_dir.rglob("*.json")):
                relative = json_file.relative_to(lang_dir)
                namespace = ".".join(relative.with_suffix("").parts)

                try:
                    raw = json_file.read_bytes()
                    data = orjson.loads(raw)
                except Exception:
                    logger.exception("Failed to load %s", json_file)
                    continue

                self._flatten(data, namespace, lang_map, lang, str(json_file))

        if locale_dir not in self._loaded_dirs:
            self._loaded_dirs.append(locale_dir)

    def _flatten(
        self,
        value: Any,
        prefix: str,
        target: dict[str, Any],
        lang: str,
        source_file: str,
    ) -> None:
        if isinstance(value, dict):
            if _is_plural_object(value):
                if self.raise_on_duplicate and prefix in target:
                    msg = (
                        f'DuplicateKeyError: Key "{prefix}" for locale '
                        f'"{lang}" already loaded, '
                        f'conflicting file: "{source_file}"'
                    )
                    raise ValueError(msg)
                target[prefix] = {k: str(v) for k, v in value.items()}
            else:
                for k, v in value.items():
                    full_key = f"{prefix}.{k}" if prefix else k
                    self._flatten(v, full_key, target, lang, source_file)
        elif isinstance(value, str):
            if self.raise_on_duplicate and prefix in target:
                msg = (
                    f'DuplicateKeyError: Key "{prefix}" for locale '
                    f'"{lang}" already loaded, '
                    f'conflicting file: "{source_file}"'
                )
                raise ValueError(msg)
            target[prefix] = value
        else:
            target[prefix] = str(value)

    def _lookup(self, key: str, locale: str) -> Any | None:
        lang_map = self._translations.get(locale)
        if lang_map and key in lang_map:
            return lang_map[key]

        if locale != self.default_locale:
            default_map = self._translations.get(self.default_locale)
            if default_map and key in default_map:
                return default_map[key]

        return None
