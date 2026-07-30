from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from footprint_auditor.models import Finding, RemediationStatus, Target
from footprint_auditor.storage import Storage


@pytest.fixture
def storage() -> Iterator[Storage]:
    s = Storage(":memory:")
    yield s
    s.close()


def _finding(
    category: str = "data_broker", automated: bool = False, url: str = "https://example.com"
) -> Finding:
    return Finding(
        source="TestBroker",
        category=category,
        url=url,
        summary="test finding",
        risk_score=0,
        discovered_at=datetime.now(UTC),
        automated=automated,
    )


def test_save_findings_assigns_unique_ids_to_distinct_findings(storage: Storage) -> None:
    target = Target(name="Test Person")
    saved = storage.save_findings(
        target, [_finding(url="https://example.com/a"), _finding(url="https://example.com/b")]
    )
    assert all(f.id is not None for f in saved)
    assert len({f.id for f in saved}) == 2


def test_save_findings_deduplicates_identical_finding(storage: Storage) -> None:
    target = Target(name="Test Person")
    first = storage.save_findings(target, [_finding()])
    second = storage.save_findings(target, [_finding()])

    assert first[0].id == second[0].id
    assert len(storage.get_findings_by_target("Test Person")) == 1


def test_save_findings_does_not_dedupe_across_different_urls(storage: Storage) -> None:
    target = Target(name="Test Person")
    storage.save_findings(target, [_finding(url="https://example.com/a")])
    storage.save_findings(target, [_finding(url="https://example.com/b")])

    assert len(storage.get_findings_by_target("Test Person")) == 2


def test_save_findings_dedup_preserves_remediation_progress(storage: Storage) -> None:
    target = Target(name="Test Person")
    saved = storage.save_findings(target, [_finding()])
    storage.update_remediation_status(saved[0].id, RemediationStatus.REQUESTED)

    storage.save_findings(target, [_finding()])

    record = storage.get_remediation_status(saved[0].id)
    assert record is not None
    assert record.status == RemediationStatus.REQUESTED
    assert len(record.status_history) == 2


def test_get_findings_by_target_round_trips(storage: Storage) -> None:
    target = Target(name="Test Person")
    saved = storage.save_findings(target, [_finding(category="breach", automated=True)])

    fetched = storage.get_findings_by_target("Test Person")

    assert len(fetched) == 1
    assert fetched[0].id == saved[0].id
    assert fetched[0].category == "breach"
    assert fetched[0].automated is True


def test_get_findings_by_target_empty_for_unknown_target(storage: Storage) -> None:
    assert storage.get_findings_by_target("Nobody") == []


def test_get_finding_by_id(storage: Storage) -> None:
    target = Target(name="Test Person")
    saved = storage.save_findings(target, [_finding()])

    fetched = storage.get_finding_by_id(saved[0].id)

    assert fetched is not None
    assert fetched.id == saved[0].id
    assert fetched.category == "data_broker"


def test_get_finding_by_id_returns_none_for_missing(storage: Storage) -> None:
    assert storage.get_finding_by_id(999) is None


def test_save_findings_seeds_found_status(storage: Storage) -> None:
    target = Target(name="Test Person")
    saved = storage.save_findings(target, [_finding()])

    record = storage.get_remediation_status(saved[0].id)

    assert record is not None
    assert record.status == RemediationStatus.FOUND
    assert len(record.status_history) == 1


def test_update_remediation_status_valid_transition(storage: Storage) -> None:
    target = Target(name="Test Person")
    saved = storage.save_findings(target, [_finding()])

    storage.update_remediation_status(saved[0].id, RemediationStatus.REQUESTED)

    record = storage.get_remediation_status(saved[0].id)
    assert record is not None
    assert record.status == RemediationStatus.REQUESTED
    assert len(record.status_history) == 2


def test_update_remediation_status_invalid_transition_raises_and_does_not_mutate(
    storage: Storage,
) -> None:
    target = Target(name="Test Person")
    saved = storage.save_findings(target, [_finding()])

    with pytest.raises(ValueError):
        storage.update_remediation_status(saved[0].id, RemediationStatus.REMOVED)

    record = storage.get_remediation_status(saved[0].id)
    assert record is not None
    assert record.status == RemediationStatus.FOUND
    assert len(record.status_history) == 1


def test_update_remediation_status_missing_finding_raises(storage: Storage) -> None:
    with pytest.raises(ValueError):
        storage.update_remediation_status(999, RemediationStatus.REQUESTED)


def test_get_remediation_status_returns_none_for_missing(storage: Storage) -> None:
    assert storage.get_remediation_status(999) is None
