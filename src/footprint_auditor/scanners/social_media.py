"""Social media search: no platform developer credentials are configured for
this tool, so every platform falls into tasks.md's own "otherwise" branch —
manual search links, automated=False.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import quote_plus

from footprint_auditor.models import Finding, Target

_PLATFORMS: list[tuple[str, str]] = [
    ("linkedin", "https://www.linkedin.com/search/results/all/?keywords={q}"),
    ("x_twitter", "https://twitter.com/search?q={q}"),
    ("facebook", "https://www.facebook.com/search/people/?q={q}"),
]

_MANUAL_ONLY: list[tuple[str, str]] = [
    ("instagram", "https://www.instagram.com/"),
]


class SocialMediaScanner:
    """Builds manual social-media search links across a fixed set of platforms."""

    def scan(self, target: Target) -> list[Finding]:
        query = quote_plus(target.name)
        now = datetime.now(UTC)
        findings = [
            Finding(
                source=platform,
                category="social_media",
                url=template.format(q=query),
                summary=(
                    f"Manual social-media search for {target.name} on {platform} "
                    f"(no API integration configured)."
                ),
                risk_score=0,
                discovered_at=now,
                automated=False,
            )
            for platform, template in _PLATFORMS
        ]
        findings.extend(
            Finding(
                source=platform,
                category="social_media",
                url=url,
                summary=(
                    f"{platform} has no name-search deep link — search manually "
                    f"within the app for {target.name}."
                ),
                risk_score=0,
                discovered_at=now,
                automated=False,
            )
            for platform, url in _MANUAL_ONLY
        )
        return findings
