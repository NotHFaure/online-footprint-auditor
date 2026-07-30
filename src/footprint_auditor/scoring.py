"""Risk scoring for findings.

See EP-2026-07-30-003's scope note for why this doesn't score per-field
exposure detail (e.g. "address" vs "phone number") for data-broker/social
findings: Phase 2's manual-assisted scanners don't produce that detail, only
a "go check this" link, so scoring anything more granular there would be
fabricated, not derived from real data.
"""

from __future__ import annotations

from footprint_auditor.models import Finding

_CATEGORY_BASE_SCORE: dict[str, int] = {
    "breach": 70,
    "data_broker": 50,
    "social_media": 30,
    "reverse_image": 25,
    "name_search": 20,
}
_DEFAULT_BASE_SCORE = 10
_SENSITIVE_KEYWORDS = ("password", "credit card", "ssn", "social security")
_SPECIFICITY_BONUS = 20


def score_finding(finding: Finding) -> int:
    """Weight by category sensitivity, confirmed-vs-manual-lead status, and
    keyword-detected specificity in the summary. Clamped to [0, 100].
    """
    base = _CATEGORY_BASE_SCORE.get(finding.category, _DEFAULT_BASE_SCORE)
    if not finding.automated:
        base //= 2  # an unconfirmed manual-check lead, not a verified finding
    if any(keyword in finding.summary.lower() for keyword in _SENSITIVE_KEYWORDS):
        base += _SPECIFICITY_BONUS
    return min(base, 100)
