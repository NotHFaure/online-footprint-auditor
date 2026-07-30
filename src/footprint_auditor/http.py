"""Shared rate-limited HTTP client used by scanners that make real API calls."""

from __future__ import annotations

import time
from types import TracebackType
from typing import Any, Self
from urllib.parse import urlparse

import httpx

DEFAULT_USER_AGENT = (
    "footprint-auditor/0.1 (+https://github.com/NotHFaure/online-footprint-auditor)"
)


def _seconds_to_wait(last_request_at: float | None, min_interval: float, now: float) -> float:
    """How long to sleep before the next request to a host, given the last one.

    Pure and side-effect-free so it can be tested without any real I/O.
    """
    if last_request_at is None:
        return 0.0
    elapsed = now - last_request_at
    return max(0.0, min_interval - elapsed)


class RateLimitedClient:
    """Thin httpx.Client wrapper enforcing a minimum interval between requests per host."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        min_interval: float = 1.0,
    ) -> None:
        self._client = httpx.Client(headers={"User-Agent": user_agent}, timeout=10.0)
        self._min_interval = min_interval
        self._last_request_at: dict[str, float] = {}

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        host = urlparse(url).netloc
        now = time.monotonic()
        wait = _seconds_to_wait(self._last_request_at.get(host), self._min_interval, now)
        if wait > 0:
            time.sleep(wait)
        response = self._client.get(url, **kwargs)
        self._last_request_at[host] = time.monotonic()
        return response

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
