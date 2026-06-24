"""Async httpx client for the Irish Statute Book (irishstatutebook.ie) with cache.

ISB is keyless and serves XML / HTML at ELI-based URLs. We keep our own backoff + cache.
"""

from __future__ import annotations

import anyio
import httpx

from .cache import HttpCache
from .citations import content_url

DEFAULT_BASE_URL = "https://www.irishstatutebook.ie"
DEFAULT_TIMEOUT = httpx.Timeout(45.0, connect=10.0)
USER_AGENT = "ie-eli-mcp/0.1.0 (+https://github.com/matematicsolutions/ie-eli-mcp)"

_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 3


class IsbClient:
    """Async client. Use as ``async with IsbClient() as c: ...``."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        cache: HttpCache | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._cache = cache or HttpCache()
        self._http = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": USER_AGENT})

    async def __aenter__(self) -> IsbClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()
        self._cache.close()

    async def get_content(
        self, year: int, number: int, doc_type: str, fmt: str
    ) -> tuple[str, str | None, str]:
        """Fetch act content in a given format. Returns (text, content_type, source_url)."""
        url = content_url(year, number, doc_type, fmt)
        # ISB ignores the configured base_url override only matters for testing; build via helper
        if self.base_url != DEFAULT_BASE_URL:
            url = url.replace(DEFAULT_BASE_URL, self.base_url)
        key = f"{fmt}::{url}"
        cached = self._cache.get(key)
        if cached is not None and isinstance(cached, list) and len(cached) == 2:
            return cached[0], cached[1], url
        accept = "application/xml" if fmt == "xml" else "text/html"
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = await self._http.get(url, headers={"Accept": accept})
                resp.raise_for_status()
                self._cache.set(key, [resp.text, resp.headers.get("content-type")],
                                ttl=HttpCache.ttl_for("act"))
                return resp.text, resp.headers.get("content-type"), url
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code not in _RETRY_STATUS or attempt == _MAX_ATTEMPTS - 1:
                    raise
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt == _MAX_ATTEMPTS - 1:
                    raise
            await anyio.sleep(0.5 * (2**attempt))
        assert last_exc is not None
        raise last_exc
