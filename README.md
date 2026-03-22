# i18n-fastapi

[![PyPI version](https://img.shields.io/pypi/v/i18n-fastapi.svg)](https://pypi.org/project/i18n-fastapi/)
[![Python versions](https://img.shields.io/pypi/pyversions/i18n-fastapi.svg)](https://pypi.org/project/i18n-fastapi/)
[![License](https://img.shields.io/pypi/l/i18n-fastapi.svg)](https://github.com/johnatanpalacios/i18n-fastapi/blob/main/LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/johnatanpalacios/i18n-fastapi/ci.yml?branch=main&label=CI)](https://github.com/johnatanpalacios/i18n-fastapi/actions)

High-performance internationalization for FastAPI, powered by a Rust translation engine with automatic Python fallback.

## Features

- **Rust-powered engine** — blazing-fast translation lookups via PyO3, with pure Python fallback
- **ICU plural support** — zero / one / two / few / many / other
- **Configurable locale detection** — query params, cookies, headers, path prefix, in any priority order
- **Plugin pattern** — one-line setup with `I18n(app)`
- **Multiple locale directories** — shared + per-module translations with filename-based namespacing
- **Duplicate key detection** — catch conflicts at startup, not at runtime
- **Hot reload** — watch translation files during development
- **Built-in endpoint** — `GET /i18n/languages` returns available locales
- **FastAPI dependencies** — inject `Locale` and `TranslateFunc` into route handlers

## Installation

```bash
pip install i18n-fastapi
```

For hot reload during development:

```bash
pip install "i18n-fastapi[reload]"
```

## Quick Start

Create translation files:

```
locales/
├── en/
│   └── messages.json    # {"greeting": "Hello {name}"}
└── es/
    └── messages.json    # {"greeting": "Hola {name}"}
```

Set up your app:

```python
from fastapi import FastAPI
from i18n_fastapi import I18n, t

app = FastAPI()
I18n(app)

@app.get("/greet")
async def greet():
    return {"message": t("messages.greeting", name="World")}
```

Request with `?lang=es` or `Accept-Language: es` and the response adapts automatically.

## Documentation

- **[Usage Guide](docs/USAGE.md)** — configuration, locale detection, pluralization, and more
- **[Contributing](CONTRIBUTING.md)** — how to set up the dev environment, run tests, and submit PRs
- **[Publishing](docs/PUBLISHING.md)** — how to publish releases to PyPI
- **[Changelog](CHANGELOG.md)** — version history
- **[Code of Conduct](CODE_OF_CONDUCT.md)** — community standards

## Author

Johnatan Palacios Londoño — [johnatan.palacios@utp.edu.co](mailto:johnatan.palacios@utp.edu.co)

## License

[MIT](LICENSE)
