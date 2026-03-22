# Contributing to i18n-fastapi

Thank you for your interest in contributing! This document explains how to set up the development environment, run tests, and submit changes.

## Table of Contents

- [Types of Contributions](#types-of-contributions)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Rules](#testing-rules)
- [Pull Request Process](#pull-request-process)
- [Rust Development](#rust-development)
- [Reporting Bugs](#reporting-bugs)

---

## Types of Contributions

All contributions are welcome:

- **Bug reports** — found something broken? Open an issue.
- **Bug fixes** — submit a PR with a failing test and the fix.
- **Features** — propose in an issue first, then implement.
- **Documentation** — typos, examples, guides.
- **Translations** — help translate the test fixtures or docs.

## Getting Started

### Prerequisites

- Python 3.11+
- Rust toolchain ([rustup.rs](https://rustup.rs/)) — only needed if modifying the Rust engine
- Git

### Setup

```bash
# Fork and clone the repository
git clone https://github.com/<your-username>/i18n-fastapi.git
cd i18n-fastapi

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install development dependencies
pip install -e ".[dev]"

# Compile the Rust engine (optional, requires Rust toolchain)
maturin develop

# Verify everything works
pytest
```

If you skip `maturin develop`, tests will run against the Python fallback engine. Both engines are tested in CI.

## Development Workflow

This project uses **GitHub Flow** — a simple branching model:

1. **Create a branch** from `main`
2. **Make your changes** with tests
3. **Open a Pull Request** against `main`
4. **CI runs** (tests + lint)
5. **Review and merge**

### Branch naming

Use prefixes to indicate the type of change:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/` | New feature | `feat/add-yaml-support` |
| `fix/` | Bug fix | `fix/plural-zero-fallback` |
| `docs/` | Documentation | `docs/update-usage-guide` |
| `refactor/` | Code refactoring | `refactor/simplify-resolver` |
| `test/` | Test improvements | `test/add-edge-cases` |
| `chore/` | Maintenance | `chore/update-dependencies` |

### Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add YAML translation file support
fix: handle empty plural forms gracefully
docs: add hot reload section to usage guide
test: add edge cases for path prefix resolver
chore: bump pyo3 to 0.24
```

The format is:

```
<type>: <short description>

<optional body explaining the why>
```

## Code Standards

### Linting

All Python code must pass `ruff` without errors:

```bash
ruff check python/ tests/
```

Auto-fix common issues:

```bash
ruff check python/ tests/ --fix
```

### Formatting

```bash
ruff format python/ tests/
```

### Type checking (recommended)

```bash
mypy python/
```

### Style rules

- Line length: 88 characters
- Quote style: double quotes
- Imports: sorted by `isort` rules (enforced by `ruff`)
- Type annotations: required on all public functions

## Testing Rules

**Every code change must include tests.** PRs without tests for new functionality will not be merged.

### Running tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_engine.py

# Run a specific test
pytest tests/test_engine.py::TestPluralization::test_zero
```

### Test structure

Tests mirror the source structure:

| Source | Test File |
|--------|-----------|
| `plugin.py` | `tests/test_plugin.py` |
| `middleware.py` | `tests/test_middleware.py` |
| `_python_engine.py` | `tests/test_engine.py` |
| `config.py` | `tests/test_config.py` |
| `_engine.py` | `tests/test_engine_selector.py` |
| `_watcher.py` | `tests/test_watcher.py` |

### Test fixtures

Translation fixtures live in `tests/fixtures/`:

```
tests/fixtures/
├── locales/
│   ├── en/messages.json
│   └── es/messages.json
└── locales2/
    └── en/extra.json
```

Add new fixtures there if your tests need additional translation files.

### What to test

- **Happy path**: the feature works as expected
- **Edge cases**: empty inputs, missing keys, unsupported locales
- **Error cases**: duplicate keys, invalid config, malformed JSON
- **Both engines**: ensure behavior is identical for Rust and Python fallback

### CI test matrix

CI runs tests on:
- Python 3.11, 3.12, 3.13
- With Rust engine compiled
- With Python fallback only (no Rust)

## Pull Request Process

1. **Create your branch**: `git checkout -b feat/my-feature`
2. **Write code and tests**
3. **Verify locally**:
   ```bash
   ruff check python/ tests/
   ruff format python/ tests/
   pytest
   ```
4. **Push**: `git push origin feat/my-feature`
5. **Open a PR** against `main` on GitHub
6. **Fill in the PR description**:
   - What does this change?
   - Why is it needed?
   - How was it tested?
7. **Wait for CI** — all checks must pass
8. **Address review feedback** if any
9. **Merge** — squash-and-merge is preferred

### PR checklist

Before requesting review, confirm:

- [ ] Tests pass locally (`pytest`)
- [ ] Lint passes (`ruff check python/ tests/`)
- [ ] New code has tests
- [ ] Documentation is updated if the public API changed
- [ ] CHANGELOG.md is updated under `[Unreleased]`

## Rust Development

If you are modifying the Rust engine in `rust/src/`:

### Build and test

```bash
# Compile and install into the venv
maturin develop

# Run Rust unit tests
cargo test --manifest-path rust/Cargo.toml

# Run clippy lints
cargo clippy --manifest-path rust/Cargo.toml -- -D warnings
```

### Project structure

```
rust/
├── Cargo.toml
└── src/
    ├── lib.rs             # PyO3 module definition
    ├── engine.rs          # TranslationEngine (exposed to Python)
    ├── loader.rs          # File scanning and JSON loading
    ├── interpolation.rs   # String interpolation ({param})
    └── pluralization.rs   # ICU plural form selection
```

### Important notes

- Any change to the Rust engine API must be mirrored in `python/i18n_fastapi/_python_engine.py` to keep the fallback in sync.
- Always run both `cargo test` and `pytest` after Rust changes.

## Reporting Bugs

Open an issue with the following information:

- **i18n-fastapi version**: `pip show i18n-fastapi`
- **Python version**: `python --version`
- **Operating system**: macOS / Linux / Windows
- **Engine**: Rust or Python fallback (`from i18n_fastapi._engine import RUST_AVAILABLE; print(RUST_AVAILABLE)`)
- **Steps to reproduce**: minimal code example that triggers the bug
- **Expected behavior**: what should happen
- **Actual behavior**: what happens instead

---

Thank you for contributing!
