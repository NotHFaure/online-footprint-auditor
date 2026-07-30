"""Name search: tries a real automated search via a self-hosted SearXNG
instance first (see EP-2026-07-30-006); falls back to the manual-link
behavior from EP-2026-07-30-002 when SearXNG is unavailable or genuinely
finds nothing.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import quote_plus

from footprint_auditor.models import Finding, Target
from footprint_auditor.searxng import SearxngClient

_ENGINES: list[tuple[str, str]] = [
    ("duckduckgo", "https://duckduckgo.com/html/?q={q}"),
    ("google", "https://www.google.com/search?q={q}"),
    ("bing", "https://www.bing.com/search?q={q}"),
]


class NameSearchScanner:
    """Automated name search via SearXNG, with manual links as a fallback."""

    def __init__(self, searxng: SearxngClient | None) -> None:
        self._searxng = searxng

    def scan(self, target: Target) -> list[Finding]:
        now = datetime.now(UTC)

        if self._searxng is not None:
            results = self._searxng.search(f'"{target.name}"')
            if results:
                return [
                    Finding(
                        source=result.get("engine", "searxng"),
                        category="name_search",
                        url=result["url"],
                        summary=result.get("title", "")[:300],
                        risk_score=0,
                        discovered_at=now,
                        automated=True,
                    )
                    for result in results
                ]

        # SearXNG unavailable, or found nothing — offer manual links instead.
        query = quote_plus(f'"{target.name}"')
        return [
            Finding(
                source=engine,
                category="name_search",
                url=template.format(q=query),
                summary=f"Manual name search for {target.name} — review results at {engine}.",
                risk_score=0,
                discovered_at=now,
                automated=False,
            )
            for engine, template in _ENGINES
        ]
