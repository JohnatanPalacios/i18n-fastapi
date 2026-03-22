"""I18n middleware: detects locale from the request and sets the ContextVar."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from i18n_fastapi.context import language_ctx


async def _resolve_query(
    request: Request, *, param_name: str = "lang", **_: Any
) -> str | None:
    return request.query_params.get(param_name)


async def _resolve_cookie(
    request: Request, *, cookie_name: str = "lang", **_: Any
) -> str | None:
    return request.cookies.get(cookie_name)


async def _resolve_custom_header(
    request: Request, *, header_name: str = "X-Language", **_: Any
) -> str | None:
    return request.headers.get(header_name)


async def _resolve_accept_language(request: Request, **_: Any) -> str | None:
    header = request.headers.get("Accept-Language")
    if not header:
        return None
    return header.split(",")[0].split("-")[0].strip()


async def _resolve_path_prefix(request: Request, **_: Any) -> str | None:
    parts = request.url.path.strip("/").split("/")
    if parts and len(parts[0]) == 2:
        return parts[0]
    return None


RESOLVER_MAP: dict[
    str,
    Callable[..., Awaitable[str | None]],
] = {
    "query": _resolve_query,
    "cookie": _resolve_cookie,
    "custom_header": _resolve_custom_header,
    "accept_language": _resolve_accept_language,
    "path_prefix": _resolve_path_prefix,
}


class I18nMiddleware(BaseHTTPMiddleware):
    """Detect the request locale and expose it via ContextVar."""

    def __init__(
        self,
        app: Any,
        *,
        resolver_order: list[str] | None = None,
        default_locale: str = "en",
        supported_locales: list[str] | None = None,
        set_content_language_header: bool = True,
        query_param_name: str = "lang",
        cookie_name: str = "lang",
        custom_header_name: str = "X-Language",
    ) -> None:
        super().__init__(app)
        self.resolver_order = resolver_order or list(RESOLVER_MAP.keys())
        self.default_locale = default_locale
        self.supported_locales = set(supported_locales) if supported_locales else None
        self.set_content_language_header = set_content_language_header
        self.query_param_name = query_param_name
        self.cookie_name = cookie_name
        self.custom_header_name = custom_header_name

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Resolve locale, set ContextVar, call handler, add header."""
        locale = await self._resolve_locale(request)
        token = language_ctx.set(locale)

        try:
            response = await call_next(request)
            if self.set_content_language_header:
                response.headers["Content-Language"] = locale
            return response
        finally:
            language_ctx.reset(token)

    async def _resolve_locale(self, request: Request) -> str:
        for resolver_name in self.resolver_order:
            resolver = RESOLVER_MAP.get(resolver_name)
            if resolver is None:
                continue

            result = await resolver(
                request,
                param_name=self.query_param_name,
                cookie_name=self.cookie_name,
                header_name=self.custom_header_name,
            )

            if result and self._is_supported(result):
                return result

        return self.default_locale

    def _is_supported(self, locale: str) -> bool:
        if self.supported_locales is None:
            return True
        return locale in self.supported_locales
