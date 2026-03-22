# Usage Guide

Complete reference for using i18n-fastapi in your FastAPI applications.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Project Setup](#project-setup)
- [Configuration Reference](#configuration-reference)
- [Locale Detection](#locale-detection)
- [Translation Functions](#translation-functions)
- [Pluralization (ICU)](#pluralization-icu)
- [Multiple Locale Directories](#multiple-locale-directories)
- [Duplicate Key Detection](#duplicate-key-detection)
- [Hot Reload](#hot-reload)
- [FastAPI Dependencies](#fastapi-dependencies)
- [Built-in Endpoints](#built-in-endpoints)
- [Rust Engine vs Python Fallback](#rust-engine-vs-python-fallback)

---

## Overview

i18n-fastapi is an internationalization library for FastAPI that uses a plugin pattern for one-line integration. The translation engine is implemented in Rust (via PyO3) for maximum performance, with a pure Python fallback that activates automatically when no pre-compiled wheel is available.

Architecture:

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Your App   │────▶│  I18n Plugin     │────▶│  Rust Engine     │
│  (FastAPI)  │     │  (middleware,    │     │  (PyO3, HashMap) │
│             │     │   lifespan,      │     │  or              │
│             │     │   router)        │     │  Python Fallback │
└─────────────┘     └──────────────────┘     └──────────────────┘
```

## Installation

### Standard install

```bash
pip install i18n-fastapi
```

### With hot reload support (development)

```bash
pip install "i18n-fastapi[reload]"
```

### Development install (from source)

```bash
git clone https://github.com/johnatanpalacios/i18n-fastapi.git
cd i18n-fastapi
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
maturin develop  # compile the Rust engine
```

### Verify the engine

```python
from i18n_fastapi._engine import RUST_AVAILABLE
print(f"Rust engine active: {RUST_AVAILABLE}")
```

## Project Setup

### Directory structure

Translation files are plain JSON organized by locale:

```
your-project/
├── locales/
│   ├── en/
│   │   ├── messages.json
│   │   └── errors.json
│   └── es/
│       ├── messages.json
│       └── errors.json
├── main.py
└── ...
```

### JSON file format

Each JSON file contains a flat or nested object. The filename becomes the first segment of the translation key.

`locales/en/messages.json`:
```json
{
  "greeting": "Hello {name}",
  "farewell": "Goodbye {name}",
  "errors": {
    "notFound": "Resource {id} not found",
    "unauthorized": "You are not authorized"
  }
}
```

### Key convention

Keys are built as `filename.path.to.value`:

| File | JSON Path | Translation Key |
|------|-----------|-----------------|
| `messages.json` | `greeting` | `messages.greeting` |
| `messages.json` | `errors.notFound` | `messages.errors.notFound` |
| `errors.json` | `server` | `errors.server` |

## Configuration Reference

All fields have sensible defaults. The plugin works with zero configuration:

```python
from i18n_fastapi import I18n
app = FastAPI()
I18n(app)  # uses all defaults
```

Full configuration:

```python
from i18n_fastapi import I18n, I18nConfig

config = I18nConfig(
    default_locale="en",
    supported_locales=["en", "es", "pt"],
    locales_dir="locales",
    locale_dirs=[],
    auto_discover=True,
    locale_resolvers=["query", "cookie", "custom_header", "accept_language", "path_prefix"],
    query_param_name="lang",
    cookie_name="lang",
    custom_header_name="X-Language",
    raise_on_duplicate_keys=True,
    raise_on_missing_key=False,
    log_missing_keys=True,
    set_content_language_header=True,
    hot_reload=False,
    enable_languages_endpoint=True,
    languages_endpoint_path="/i18n/languages",
)

I18n(app, config=config)
```

### Field reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_locale` | `str` | `"en"` | Fallback locale when the requested one is not available |
| `supported_locales` | `list[str] \| None` | `None` | Allowed locale codes. `None` = accept any loaded locale |
| `locales_dir` | `str` | `"locales"` | Directory name used for auto-discovery |
| `locale_dirs` | `list[str]` | `[]` | Explicit locale directory paths to load |
| `auto_discover` | `bool` | `True` | Scan project tree for directories matching `locales_dir` |
| `locale_resolvers` | `list[str]` | `["query", "cookie", ...]` | Ordered locale detection strategies (first match wins) |
| `query_param_name` | `str` | `"lang"` | Query parameter name for the `query` resolver |
| `cookie_name` | `str` | `"lang"` | Cookie name for the `cookie` resolver |
| `custom_header_name` | `str` | `"X-Language"` | Header name for the `custom_header` resolver |
| `raise_on_duplicate_keys` | `bool` | `True` | Raise error when duplicate keys are found across files |
| `raise_on_missing_key` | `bool` | `False` | Raise error when a translation key is not found |
| `log_missing_keys` | `bool` | `True` | Log a warning when a translation key is not found |
| `set_content_language_header` | `bool` | `True` | Add `Content-Language` header to responses |
| `hot_reload` | `bool` | `False` | Watch files for changes (development only) |
| `enable_languages_endpoint` | `bool` | `True` | Register `GET` endpoint listing available locales |
| `languages_endpoint_path` | `str` | `"/i18n/languages"` | Path for the languages endpoint |

## Locale Detection

The middleware detects the request locale using a configurable chain of resolvers. The first match wins.

### Available resolvers

#### `query` — Query parameter

```
GET /api/items?lang=es
```

Reads from the query parameter specified by `query_param_name` (default: `lang`).

#### `cookie` — Cookie

```
Cookie: lang=es
```

Reads from the cookie specified by `cookie_name` (default: `lang`).

#### `custom_header` — Custom HTTP header

```
X-Language: es
```

Reads from the header specified by `custom_header_name` (default: `X-Language`).

#### `accept_language` — Accept-Language header

```
Accept-Language: es-MX,es;q=0.9,en;q=0.8
```

Extracts the primary language from the standard `Accept-Language` header.

#### `path_prefix` — URL path prefix

```
GET /es/api/items
```

Checks if the first path segment is a 2-letter locale code. You must define routes with an optional prefix for this to work:

```python
@app.get("/items")
@app.get("/{lang_prefix}/items")
async def get_items():
    return {"locale": get_locale()}
```

### Customizing resolver order

```python
config = I18nConfig(
    locale_resolvers=["cookie", "accept_language"],  # only these two, in this order
)
```

### How fallback works

If no resolver matches or the detected locale is not in `supported_locales`, the `default_locale` is used.

## Translation Functions

### The `t()` function

The global `t()` function translates a key using the current request locale:

```python
from i18n_fastapi import t

@app.get("/greet")
async def greet():
    return {"message": t("messages.greeting", name="World")}
```

Keyword arguments become interpolation parameters. In the JSON, use `{param_name}`:

```json
{"greeting": "Hello {name}, you have {count} messages"}
```

```python
t("messages.greeting", name="Alice", count=5)
# → "Hello Alice, you have 5 messages"
```

### The `get_locale()` function

Returns the current request locale as a string:

```python
from i18n_fastapi import get_locale

@app.get("/info")
async def info():
    return {"current_locale": get_locale()}
```

### Missing keys

When a key is not found:
- The key itself is returned as the translation (e.g., `"messages.unknown_key"`)
- A warning is logged if `log_missing_keys=True`
- An error is raised if `raise_on_missing_key=True`

## Pluralization (ICU)

Use the ICU plural categories as JSON keys: `zero`, `one`, `two`, `few`, `many`, `other`.

```json
{
  "items": {
    "count": {
      "zero": "No items",
      "one": "{count} item",
      "two": "{count} items",
      "other": "{count} items"
    }
  }
}
```

The `count` parameter triggers plural selection:

```python
t("messages.items.count", count=0)   # → "No items"
t("messages.items.count", count=1)   # → "1 item"
t("messages.items.count", count=2)   # → "2 items"
t("messages.items.count", count=42)  # → "42 items"
```

### Plural rules

| count | Selected form |
|-------|---------------|
| 0 | `zero` (falls back to `other`) |
| 1 | `one` (falls back to `other`) |
| 2 | `two` (falls back to `other`) |
| 3–10 | `few` (falls back to `other`) |
| 11+ | `other` |

The `other` form is required and serves as the fallback for any missing category.

## Multiple Locale Directories

### Explicit directories

```python
config = I18nConfig(
    locale_dirs=[
        "locales",
        "src/modules/billing/locales",
        "src/modules/auth/locales",
    ],
    auto_discover=False,
)
```

### Auto-discovery

When `auto_discover=True` (the default), the plugin scans the project tree for any directory named `locales` (or whatever `locales_dir` is set to). It skips common directories like `.venv`, `node_modules`, `.git`, and `__pycache__`.

### Runtime registration

```python
i18n = I18n(app)
i18n.add_locale_dir("plugins/my_plugin/locales")
```

### Namespace isolation

Each JSON file's name becomes the key prefix, preventing collisions:

```
locales/en/messages.json      → messages.*
locales/en/errors.json        → errors.*
billing/locales/en/invoice.json → invoice.*
```

## Duplicate Key Detection

When `raise_on_duplicate_keys=True` (the default), loading stops with a clear error if two files define the same key for the same locale:

```
ValueError: Key "errors.notFound" for locale "en" already loaded
from "locales/en/errors.json", conflicting file: "modules/auth/locales/en/errors.json"
```

To allow merging (last file wins), set `raise_on_duplicate_keys=False`.

## Hot Reload

Enable automatic reloading of translation files during development:

```python
config = I18nConfig(hot_reload=True)
```

Requires the `watchfiles` package:

```bash
pip install "i18n-fastapi[reload]"
```

When enabled, a background thread watches all loaded locale directories. Any change to a `.json` file triggers a full reload of the translation engine.

> **Warning**: Do not enable `hot_reload` in production. It adds filesystem polling overhead.

## FastAPI Dependencies

Inject locale and translation functions into route handlers using FastAPI's dependency injection:

```python
from i18n_fastapi import Locale, TranslateFunc

@app.get("/items")
async def get_items(locale: Locale, translate: TranslateFunc):
    return {
        "locale": locale,                                    # "es"
        "message": translate("messages.greeting", name="FastAPI"),  # "Hola FastAPI"
    }
```

- `Locale` — resolves to the current request locale string
- `TranslateFunc` — resolves to the `t()` function bound to the current request context

## Built-in Endpoints

### Languages endpoint

When `enable_languages_endpoint=True` (default), a `GET` endpoint is registered:

```
GET /i18n/languages
```

Response:

```json
{
  "locales": ["en", "es"],
  "default": "en",
  "current": "es"
}
```

### Custom path

```python
config = I18nConfig(languages_endpoint_path="/api/v1/locales")
```

### Disable

```python
config = I18nConfig(enable_languages_endpoint=False)
```

## Rust Engine vs Python Fallback

The library ships pre-compiled wheels with a native Rust engine for Linux, macOS, and Windows. If no wheel matches your platform, a pure Python fallback activates automatically.

Both engines have identical behavior and API. The Rust engine is faster for large translation dictionaries and high-throughput applications.

### Check which engine is active

```python
from i18n_fastapi._engine import RUST_AVAILABLE
print(f"Rust engine: {RUST_AVAILABLE}")
```

### Force Python fallback (testing)

Set `PYTHONDONTWRITEBYTECODE=1` does not affect engine selection. To test the Python fallback, uninstall the compiled extension or run tests with the `test-fallback` CI job configuration.

### Performance characteristics

| Operation | Rust Engine | Python Fallback |
|-----------|-------------|-----------------|
| Key lookup | ~100ns | ~1μs |
| Interpolation | ~200ns | ~2μs |
| Directory scan | ~500μs | ~5ms |

Performance varies by machine and dictionary size. The Rust engine provides the most benefit with large translation files and high request volumes.
