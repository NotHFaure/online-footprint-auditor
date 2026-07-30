"""Name search: no free automated search API exists, so this generates
ready-to-click search links for the operator to review by hand (automated=False),
per the 2026-07-30 decision recorded in EP-2026-07-30-002.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import quote_plus

from footprint_auditor.models import Finding, Target

_ENGINES: list[tuple[str, str]] = [
    ("duckduckgo", "https://duckduckgo.com/html/?q={q}"),
    ("google", "https://www.google.com/search?q={q}"),
    ("bing", "https://www.bing.com/search?q={q}"),
]


class NameSearchScanner:
    """Builds manual name-search links for a target across several search engines."""

    def scan(self, target: Target) -> list[Finding]:
        query = quote_plus(f'"{target.name}"')
        now = datetime.now(UTC)
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
