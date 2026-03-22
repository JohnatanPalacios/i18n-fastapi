# Publishing Guide

How to release new versions of i18n-fastapi to PyPI.

## Table of Contents

- [Semantic Versioning](#semantic-versioning)
- [Pre-release Checklist](#pre-release-checklist)
- [Publishing to TestPyPI](#publishing-to-testpypi)
- [Publishing to PyPI](#publishing-to-pypi)
- [Automated Publishing (GitHub Actions)](#automated-publishing-github-actions)
- [GitHub Releases](#github-releases)
- [Troubleshooting](#troubleshooting)

---

## Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

| Increment | When | Example |
|-----------|------|---------|
| **MAJOR** | Breaking API changes | `1.0.0 → 2.0.0` |
| **MINOR** | New features, backward compatible | `0.1.0 → 0.2.0` |
| **PATCH** | Bug fixes, backward compatible | `0.1.0 → 0.1.1` |

### Where to update the version

Both files must have the same version:

1. `pyproject.toml` → `[project] version`
2. `rust/Cargo.toml` → `[package] version`

## Pre-release Checklist

Before every release:

- [ ] All tests pass: `pytest`
- [ ] Lint is clean: `ruff check python/ tests/`
- [ ] Rust tests pass: `cargo test --manifest-path rust/Cargo.toml`
- [ ] Version bumped in `pyproject.toml` and `rust/Cargo.toml`
- [ ] `CHANGELOG.md` updated: move `[Unreleased]` items under the new version heading
- [ ] README and docs are up to date

## Publishing to TestPyPI

Test your release before pushing to the real PyPI.

### 1. Create a TestPyPI account

Sign up at [test.pypi.org](https://test.pypi.org/account/register/).

### 2. Generate an API token

Go to **Account Settings → API tokens → Add API token**. Set scope to "Entire account" or the specific project.

### 3. Build locally

```bash
# Build the source distribution and wheel for your platform
maturin build --release --out dist/
```

This creates files in `dist/`:
```
dist/
├── i18n_fastapi-0.1.0.tar.gz           # source distribution
└── i18n_fastapi-0.1.0-cp311-...-....whl  # compiled wheel
```

### 4. Upload to TestPyPI

Install twine if you don't have it:

```bash
pip install twine
```

Upload:

```bash
twine upload --repository testpypi dist/*
```

When prompted, use `__token__` as the username and your API token as the password.

### 5. Test the install

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ i18n-fastapi
```

The `--extra-index-url` is needed so that dependencies (fastapi, pydantic, etc.) can still be found on the real PyPI.

### 6. Verify

```python
import i18n_fastapi
print(i18n_fastapi.__all__)
```

## Publishing to PyPI

### Manual method

#### 1. Create a PyPI account

Sign up at [pypi.org](https://pypi.org/account/register/).

#### 2. Generate an API token

Go to **Account Settings → API tokens → Add API token**.

#### 3. Build and upload

```bash
# Clean previous builds
rm -rf dist/

# Build
maturin build --release --out dist/

# Upload to PyPI
twine upload dist/*
```

Or use maturin's built-in publish:

```bash
maturin publish
```

When prompted, enter your API token.

#### 4. Verify

```bash
pip install i18n-fastapi
python -c "from i18n_fastapi import I18n; print('OK')"
```

### Important

The wheel built by `maturin build` only covers your current platform. For cross-platform wheels (Linux, macOS, Windows), use the automated CI/CD pipeline described below.

## Automated Publishing (GitHub Actions)

The recommended way to publish. The CI builds wheels for all supported platforms and publishes them automatically.

### How it works

The workflow at `.github/workflows/release.yml` triggers on version tags (`v*`):

1. **build-wheels** — compiles wheels on Linux, macOS, and Windows using `maturin-action`
2. **build-sdist** — creates the source distribution
3. **publish** — downloads all artifacts and publishes to PyPI using trusted publishing (OIDC)

### Setup (one-time)

#### Option A: Trusted Publishing (recommended)

No API token needed. PyPI verifies the GitHub Actions identity directly.

1. Go to [pypi.org](https://pypi.org) → Your project → **Publishing** → **Add a new publisher**
2. Fill in:
   - **Owner**: your GitHub username
   - **Repository**: `i18n-fastapi`
   - **Workflow**: `release.yml`
   - **Environment**: `release`
3. Create a GitHub environment called `release` in your repo settings (**Settings → Environments → New environment**)

#### Option B: API Token

1. Generate a PyPI API token scoped to your project
2. Add it as a repository secret: **Settings → Secrets → Actions → New secret**
   - Name: `PYPI_API_TOKEN`
   - Value: your token
3. Modify `.github/workflows/release.yml` to use the token:
   ```yaml
   - name: Publish to PyPI
     uses: pypa/gh-action-pypi-publish@release/v1
     with:
       password: ${{ secrets.PYPI_API_TOKEN }}
   ```

### Creating a release

```bash
# Bump version in pyproject.toml and rust/Cargo.toml
# Update CHANGELOG.md

# Commit and tag
git add -A
git commit -m "chore: release v0.2.0"
git tag v0.2.0
git push origin main --tags
```

The CI pipeline will:
1. Build wheels for Linux (x86_64), macOS (universal2), and Windows (x86_64)
2. Build the source distribution
3. Publish all artifacts to PyPI

Monitor progress in the **Actions** tab of your GitHub repository.

### Supported platforms

| Platform | Target | Architecture |
|----------|--------|--------------|
| Linux | `x86_64-unknown-linux-gnu` | x86_64 |
| macOS | `universal2-apple-darwin` | x86_64 + ARM64 |
| Windows | `x86_64-pc-windows-msvc` | x86_64 |

Users on other platforms will get the source distribution and need Rust installed to compile.

## GitHub Releases

After the tag is pushed and PyPI publication succeeds, create a GitHub Release:

1. Go to **Releases → Draft a new release**
2. Select the tag (e.g., `v0.2.0`)
3. Title: `v0.2.0`
4. Description: copy the relevant section from `CHANGELOG.md`
5. Publish

Alternatively, use the GitHub CLI:

```bash
gh release create v0.2.0 --title "v0.2.0" --notes "$(sed -n '/## \[0.2.0\]/,/## \[/p' CHANGELOG.md | head -n -1)"
```

## Troubleshooting

### "File already exists" error

PyPI does not allow re-uploading the same version. Bump the version number and try again.

### "Invalid API token" error

- Verify the token is correctly set in GitHub Secrets
- Check if the token is scoped to the correct project
- For trusted publishing, verify the environment name matches (`release`)

### Build fails on a specific platform

Check the CI logs in GitHub Actions. Common issues:
- **Linux**: missing system dependencies → check the manylinux container
- **macOS**: Xcode command line tools not installed → `xcode-select --install`
- **Windows**: MSVC build tools not installed

### Source distribution fails to install

Users installing from sdist need:
- Rust toolchain installed
- `maturin` build backend

The error message will guide them:
```
error: can't find Rust compiler
```

This is expected for platforms without pre-compiled wheels. The Python fallback will be used instead if they install without the Rust extension.

### Testing a release locally before tagging

```bash
maturin build --release --out dist/
twine check dist/*
```

`twine check` validates the package metadata and README rendering.
