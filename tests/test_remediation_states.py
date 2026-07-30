import pytest

from footprint_auditor.models import RemediationStatus, can_transition

VALID_TRANSITIONS = {
    (RemediationStatus.FOUND, RemediationStatus.REQUESTED),
    (RemediationStatus.REQUESTED, RemediationStatus.PENDING),
    (RemediationStatus.PENDING, RemediationStatus.REMOVED),
    (RemediationStatus.PENDING, RemediationStatus.DENIED),
}


@pytest.mark.parametrize("from_status,to_status", sorted(VALID_TRANSITIONS, key=str))
def test_documented_transitions_are_allowed(
    from_status: RemediationStatus, to_status: RemediationStatus
) -> None:
    assert can_transition(from_status, to_status) is True


def test_skip_transition_rejected() -> None:
    assert can_transition(RemediationStatus.FOUND, RemediationStatus.REMOVED) is False


def test_backward_transition_rejected() -> None:
    assert can_transition(RemediationStatus.REQUESTED, RemediationStatus.FOUND) is False


def test_no_op_transition_rejected() -> None:
    assert can_transition(RemediationStatus.FOUND, RemediationStatus.FOUND) is False


@pytest.mark.parametrize("from_status", list(RemediationStatus))
@pytest.mark.parametrize("to_status", list(RemediationStatus))
def test_only_documented_transitions_are_valid(
    from_status: RemediationStatus, to_status: RemediationStatus
) -> None:
    expected = (from_status, to_status) in VALID_TRANSITIONS
    assert can_transition(from_status, to_status) is expected
