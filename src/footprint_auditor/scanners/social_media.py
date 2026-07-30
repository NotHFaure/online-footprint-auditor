"""Social media search: tries a real automated site:-filtered search via a
self-hosted SearXNG instance first, per platform (see EP-2026-07-30-006).
No platform's own API is called directly — no developer credentials are
configured for any of them. Falls back, per platform, to the manual-link
behavior from EP-2026-07-30-002 when SearXNG is unavailable or that specific
platform's query genuinely finds nothing.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import quote_plus

from footprint_auditor.models import Finding, Target
from footprint_auditor.searxng import SearxngClient

_PLATFORM_DOMAINS: list[tuple[str, str]] = [
    ("linkedin", "linkedin.com"),
    ("x_twitter", "twitter.com"),
    ("facebook", "facebook.com"),
    ("instagram", "instagram.com"),
]

_DEEP_LINK_TEMPLATES: dict[str, str] = {
    "linkedin": "https://www.linkedin.com/search/results/all/?keywords={q}",
    "x_twitter": "https://twitter.com/search?q={q}",
    "facebook": "https://www.facebook.com/search/people/?q={q}",
}

_MANUAL_ONLY_URLS: dict[str, str] = {
    "instagram": "https://www.instagram.com/",
}


class SocialMediaScanner:
    """Automated per-platform search via SearXNG, with manual links as a fallback."""

    def __init__(self, searxng: SearxngClient | None) -> None:
        self._searxng = searxng

    def scan(self, target: Target) -> list[Finding]:
        now = datetime.now(UTC)
        findings: list[Finding] = []

        for platform, domain in _PLATFORM_DOMAINS:
            automated_hits: list[Finding] = []
            if self._searxng is not None:
                results = self._searxng.search(
                    f'site:{domain} "{target.name}"', must_contain=target.name
                )
                automated_hits = [
                    Finding(
                        source=platform,
                        category="social_media",
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
                findings.append(_manual_fallback_finding(platform, target, now))

        return findings


def _manual_fallback_finding(platform: str, target: Target, now: datetime) -> Finding:
    if platform in _DEEP_LINK_TEMPLATES:
        query = quote_plus(target.name)
        return Finding(
            source=platform,
            category="social_media",
            url=_DEEP_LINK_TEMPLATES[platform].format(q=query),
            summary=(
                f"Manual social-media search for {target.name} on {platform} "
                f"(no API integration configured)."
            ),
            risk_score=0,
            discovered_at=now,
            automated=False,
        )
    return Finding(
        source=platform,
        category="social_media",
        url=_MANUAL_ONLY_URLS[platform],
        summary=(
            f"{platform} has no name-search deep link — search manually "
            f"within the app for {target.name}."
        ),
        risk_score=0,
        discovered_at=now,
        automated=False,
    )
