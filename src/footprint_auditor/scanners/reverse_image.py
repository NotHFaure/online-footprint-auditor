"""Reverse-image search: no free automated API exists for Google/Bing/Yandex, so
this generates manual search links (automated=False), per the 2026-07-30 decision
recorded in EP-2026-07-30-002.

Hosted images (a URL) get a direct "search by image URL" link per engine. Local
file paths have no URL-only search mechanism — the operator is pointed at each
engine's homepage with an instruction to upload the file manually.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import quote_plus

from footprint_auditor.models import Finding, Target

_HOSTED_ENGINES: list[tuple[str, str]] = [
    ("google", "https://www.google.com/searchbyimage?image_url={q}"),
    ("bing", "https://www.bing.com/images/search?q=imgurl:{q}&view=detailv2&iss=sbi"),
    ("yandex", "https://yandex.com/images/search?rpt=imageview&url={q}"),
]

_MANUAL_UPLOAD_ENGINES: list[tuple[str, str]] = [
    ("google", "https://images.google.com/"),
    ("bing", "https://www.bing.com/visualsearch"),
    ("yandex", "https://yandex.com/images/"),
]


class ReverseImageScanner:
    """Builds manual reverse-image-search links for each of a target's images."""

    def scan(self, target: Target) -> list[Finding]:
        now = datetime.now(UTC)
        findings: list[Finding] = []
        for image in target.images:
            if image.startswith(("http://", "https://")):
                encoded = quote_plus(image)
                findings.extend(
                    Finding(
                        source=engine,
                        category="reverse_image",
                        url=template.format(q=encoded),
                        summary=(
                            f"Manual reverse-image search for {image} — review results at {engine}."
                        ),
                        risk_score=0,
                        discovered_at=now,
                        automated=False,
                    )
                    for engine, template in _HOSTED_ENGINES
                )
            else:
                findings.extend(
                    Finding(
                        source=engine,
                        category="reverse_image",
                        url=url,
                        summary=(
                            f"Local file {image} must be uploaded manually at "
                            f"{engine} to search it."
                        ),
                        risk_score=0,
                        discovered_at=now,
                        automated=False,
                    )
                    for engine, url in _MANUAL_UPLOAD_ENGINES
                )
        return findings
