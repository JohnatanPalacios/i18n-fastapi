# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-03-21

### Added

- Rust-powered translation engine via PyO3 with HashMap-based lookups.
- Pure Python fallback engine with identical API for platforms without pre-compiled wheels.
- Automatic engine selection: Rust native if available, Python fallback otherwise.
- `I18n(app)` plugin pattern for one-line FastAPI integration.
- `I18nConfig` Pydantic model with sensible defaults for zero-config setup.
- Locale detection middleware with configurable resolver chain:
  - `query` — query parameter (`?lang=es`)
  - `cookie` — cookie value
  - `custom_header` — custom HTTP header (`X-Language`)
  - `accept_language` — standard `Accept-Language` header
  - `path_prefix` — URL path prefix (`/es/api/...`)
- `t()` global translation function with string interpolation (`{param}`).
- ICU plural support: `zero`, `one`, `two`, `few`, `many`, `other` forms.
- Multiple locale directory support with explicit paths and auto-discovery.
- Filename-based key namespacing (`messages.json` → `messages.*`).
- Duplicate key detection with clear error messages including conflicting file paths.
- `Content-Language` response header (configurable).
- Built-in `GET /i18n/languages` endpoint with customizable path.
- `Locale` and `TranslateFunc` FastAPI dependencies for injection.
- Hot reload via `watchfiles` for development (`pip install i18n-fastapi[reload]`).
- Missing key tracking and logging.
- `has_key()`, `reload()`, `get_missing_keys()`, `clear_missing_keys()` engine methods.
- `add_locale_dir()` for runtime locale directory registration.
- GitHub Actions CI: tests on Python 3.11–3.13, Rust engine + Python fallback, lint.
- GitHub Actions release: cross-platform wheel builds (Linux, macOS, Windows) + PyPI publish.
- Comprehensive test suite (65 tests).
