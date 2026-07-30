"""HIBP breach detection: the one Phase 2 scanner that makes a real automated
API call. See https://haveibeenpwned.com/API/v3 (verified 2026-07-30).
"""

from __future__ import annotations

from datetime import UTC, datetime

from footprint_auditor.http import RateLimitedClient
from footprint_auditor.models import Finding, Target

_BASE_URL = "https://haveibeenpwned.com/api/v3/breachedAccount/{email}"

# HIBP's documented guidance: don't query at exactly the rate limit, add a short
# delay on top of it. 1.6s is deliberately more conservative than the default.
_HIBP_MIN_INTERVAL = 1.6


class BreachScanner:
    """Checks a target's emails against Have I Been Pwned's breach database."""

    def __init__(self, api_key: str, client: RateLimitedClient | None = None) -> None:
        self._api_key = api_key
        self._client = client or RateLimitedClient(min_interval=_HIBP_MIN_INTERVAL)

    def scan(self, target: Target) -> list[Finding]:
        findings: list[Finding] = []
        for email in target.emails:
            url = _BASE_URL.format(email=email)
            response = self._client.get(
                url,
                headers={"hibp-api-key": self._api_key},
                params={"truncateResponse": "false"},
            )
            if response.status_code == 404:
                continue
            if response.status_code == 401:
                raise RuntimeError(
                    "HIBP API key rejected (401). HIBP's API is paid-only — see the "
                    "PRD's one-time-subscription workflow: subscribe for a month, "
                    "run scans, cancel afterward."
                )
            response.raise_for_status()

            now = datetime.now(UTC)
            for breach in response.json():
                findings.append(
                    Finding(
                        source="hibp",
                        category="breach",
                        url="https://haveibeenpwned.com/PwnedWebsites#" + breach["Name"],
                        summary=(
                            f"{email} found in breach: {breach['Title']} "
                            f"({breach.get('BreachDate', 'date unknown')})"
                        ),
                        risk_score=0,
                        discovered_at=now,
                        automated=True,
                    )
                )
        return findings
