"""Configuration model for i18n-fastapi."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class I18nConfig(BaseModel):
    """Configuration for the i18n plugin.

    All fields have sensible defaults so the plugin works with zero configuration.
    """

    model_config = ConfigDict(frozen=True)

    default_locale: str = Field(
        default="en",
        description="Fallback locale when the requested one is not available.",
    )

    supported_locales: list[str] | None = Field(
        default=None,
        description=("Allowed locale codes. None means accept any loaded locale."),
    )

    locales_dir: str = Field(
        default="locales",
        description="Name of the directory that holds translation files.",
    )

    locale_dirs: list[str] = Field(
        default_factory=list,
        description=(
            "Explicit list of locale directory paths to load. "
            "Used in addition to auto_discover."
        ),
    )

    auto_discover: bool = Field(
        default=True,
        description=("Scan the project tree for directories matching locales_dir."),
    )

    locale_resolvers: list[str] = Field(
        default_factory=lambda: [
            "query",
            "cookie",
            "custom_header",
            "accept_language",
            "path_prefix",
        ],
        description=(
            "Ordered list of strategies for detecting the request locale. "
            "First match wins. Available: query, cookie, custom_header, "
            "accept_language, path_prefix."
        ),
    )

    query_param_name: str = Field(
        default="lang",
        description="Query parameter name for locale detection.",
    )

    cookie_name: str = Field(
        default="lang",
        description="Cookie name for locale detection.",
    )

    custom_header_name: str = Field(
        default="X-Language",
        description="Custom HTTP header name for locale detection.",
    )

    raise_on_duplicate_keys: bool = Field(
        default=True,
        description=(
            "Raise DuplicateKeyError when two files define the same "
            "translation key for the same locale."
        ),
    )

    raise_on_missing_key: bool = Field(
        default=False,
        description="Raise an error when a translation key is not found.",
    )

    log_missing_keys: bool = Field(
        default=True,
        description="Log a warning when a translation key is not found.",
    )

    set_content_language_header: bool = Field(
        default=True,
        description="Add Content-Language header to HTTP responses.",
    )

    hot_reload: bool = Field(
        default=False,
        description=(
            "Watch translation files for changes and reload automatically. "
            "Recommended only for development."
        ),
    )

    enable_languages_endpoint: bool = Field(
        default=True,
        description="Register GET endpoint listing available locales.",
    )

    languages_endpoint_path: str = Field(
        default="/i18n/languages",
        description="Path for the languages endpoint.",
    )
