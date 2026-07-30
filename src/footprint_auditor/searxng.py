"""Client for a self-hosted SearXNG instance — the free, ToS-clean way to get
real automated search results, after direct scraping of DuckDuckGo was
empirically found to be blocked (see EP-2026-07-30-006).
"""

from __future__ import annotations

import httpx

from footprint_auditor.http import RateLimitedClient

DEFAULT_BASE_URL = "http://localhost:8080"
MAX_RESULTS_PER_QUERY = 5


class SearxngClient:
    """Queries a self-hosted SearXNG instance's JSON API."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, min_interval: float = 1.5) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = RateLimitedClient(min_interval=min_interval)

    def is_available(self) -> bool:
        try:
            response = self._client.get(self._base_url + "/", timeout=3.0)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def search(self, query: str) -> list[dict]:
        """Return up to MAX_RESULTS_PER_QUERY result dicts, or [] on any failure.

        Failing soft (never raising) is deliberate: every caller already
        treats zero results as "fall back to manual", so a SearXNG hiccup
        mid-scan degrades gracefully instead of crashing the whole scan.
        """
        try:
            response = self._client.get(
                self._base_url + "/search",
                params={"q": query, "format": "json"},
                timeout=15.0,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            return results[:MAX_RESULTS_PER_QUERY]
        except httpx.HTTPError:
            return []
