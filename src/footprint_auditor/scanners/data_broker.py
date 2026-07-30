"""Data broker presence check: parsing arbitrary broker-site HTML for a reliable
"listed" signal is fragile per-site scraping, not a documented API, so this
generates a manual check link per broker instead (automated=False), per the
2026-07-30 decision recorded in EP-2026-07-30-002.
"""

from __future__ import annotations

from datetime import UTC, datetime

from footprint_auditor.data.broker_list import BROKERS
from footprint_auditor.models import Finding, Target


class DataBrokerScanner:
    """Builds one manual-check finding per vendored data-broker entry."""

    def scan(self, target: Target) -> list[Finding]:
        now = datetime.now(UTC)
        return [
            Finding(
                source=broker.name,
                category="data_broker",
                url=broker.url,
                summary=f"Manually check whether {target.name} is listed at {broker.name}.",
                risk_score=0,
                discovered_at=now,
                automated=False,
            )
            for broker in BROKERS
        ]
