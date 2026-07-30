"""Data broker presence check: parsing arbitrary broker-site HTML for a reliable
"listed" signal is fragile per-site scraping, not a documented API. Instead,
this tries a real automated site:-filtered search per broker via a
self-hosted SearXNG instance first (see EP-2026-07-30-006), falling back —
per broker — to the manual-check-link behavior from EP-2026-07-30-002 when
SearXNG is unavailable or that specific broker's query genuinely finds
nothing. A zero-hit search doesn't mean "not listed", only "not found via
this search" — so the manual link is always still offered in that case.
"""

from __future__ import annotations

from datetime import UTC, datetime

from footprint_auditor.data.broker_list import BROKERS
from footprint_auditor.models import Finding, Target
from footprint_auditor.searxng import SearxngClient


class DataBrokerScanner:
    """Automated per-broker search via SearXNG, with manual links as a fallback."""

    def __init__(self, searxng: SearxngClient | None) -> None:
        self._searxng = searxng

    def scan(self, target: Target) -> list[Finding]:
        now = datetime.now(UTC)
        findings: list[Finding] = []

        for broker in BROKERS:
            automated_hits: list[Finding] = []
            if self._searxng is not None:
                results = self._searxng.search(
                    f'site:{broker.domain} "{target.name}"', must_contain=target.name
                )
                automated_hits = [
                    Finding(
                        source=broker.name,
                        category="data_broker",
                        url=result["url"],
                        summary=result.get("title", "")[:300],
                        risk_score=0,
                        discovered_at=now,
                        automated=True,
                    )
                    for result in results
                ]

            if automated_hits:
                findings.extend(automated_hits)
            else:
                findings.append(
                    Finding(
                        source=broker.name,
                        category="data_broker",
                        url=broker.url,
                        summary=f"Manually check whether {target.name} is listed at {broker.name}.",
                        risk_score=0,
                        discovered_at=now,
                        automated=False,
                    )
                )

        return findings
