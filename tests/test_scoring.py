from datetime import UTC, datetime

from footprint_auditor.models import Finding
from footprint_auditor.scoring import score_finding


def _finding(category: str, automated: bool, summary: str = "generic finding") -> Finding:
    return Finding(
        source="test",
        category=category,
        url="https://example.com",
        summary=summary,
        risk_score=0,
        discovered_at=datetime.now(UTC),
        automated=automated,
    )


def test_category_base_score_ordering() -> None:
    breach = score_finding(_finding("breach", automated=True))
    data_broker = score_finding(_finding("data_broker", automated=True))
    social_media = score_finding(_finding("social_media", automated=True))
    reverse_image = score_finding(_finding("reverse_image", automated=True))
    name_search = score_finding(_finding("name_search", automated=True))
    assert breach > data_broker > social_media > reverse_image > name_search


def test_unknown_category_uses_default_base_score() -> None:
    assert score_finding(_finding("something_new", automated=True)) == 10


def test_manual_lead_scores_lower_than_automated_same_category() -> None:
    automated = score_finding(_finding("breach", automated=True))
    manual = score_finding(_finding("breach", automated=False))
    assert manual < automated


def test_sensitive_keyword_adds_bonus() -> None:
    plain = _finding("breach", automated=True, summary="found in a breach")
    with_password = _finding(
        "breach", automated=True, summary="found in a breach, password exposed"
    )
    assert score_finding(with_password) > score_finding(plain)


def test_score_stays_within_bounds() -> None:
    # Current weights top out at breach(70) + bonus(20) = 90 for automated=True;
    # the min(base, 100) clamp isn't structurally reachable with today's constants.
    # This asserts the invariant (never exceeds 100), not a specific clamp trigger.
    worst_case = _finding(
        "breach",
        automated=True,
        summary="password credit card ssn social security all exposed",
    )
    assert 0 <= score_finding(worst_case) <= 100

    best_case_manual = _finding("name_search", automated=False)
    assert 0 <= score_finding(best_case_manual) <= 100
