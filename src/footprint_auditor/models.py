"""Core data models: scan targets, findings, and remediation state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


@dataclass
class Target:
    """A person or entity to run a footprint audit against."""

    name: str
    images: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    org_affiliations: list[str] = field(default_factory=list)


@dataclass
class Finding:
    """A single piece of publicly discoverable exposure about a Target."""

    source: str
    category: str
    url: str
    summary: str
    risk_score: int
    discovered_at: datetime
    id: int | None = None
    """Set by Storage once the finding has been saved; None for freshly-scanned findings."""


class RemediationStatus(StrEnum):
    """Lifecycle of a remediation request for a single Finding."""

    FOUND = "found"
    REQUESTED = "requested"
    PENDING = "pending"
    REMOVED = "removed"
    DENIED = "denied"


@dataclass
class RemediationRecord:
    """Tracks remediation progress for a single Finding over time."""

    finding_id: int
    status: RemediationStatus
    status_history: list[tuple[RemediationStatus, datetime]]
    notes: str | None = None


_VALID_TRANSITIONS: frozenset[tuple[RemediationStatus, RemediationStatus]] = frozenset(
    {
        (RemediationStatus.FOUND, RemediationStatus.REQUESTED),
        (RemediationStatus.REQUESTED, RemediationStatus.PENDING),
        (RemediationStatus.PENDING, RemediationStatus.REMOVED),
        (RemediationStatus.PENDING, RemediationStatus.DENIED),
    }
)


def can_transition(from_status: RemediationStatus, to_status: RemediationStatus) -> bool:
    """Whether a remediation record may move from from_status to to_status.

    Only forward, single-step transitions are valid: FOUND -> REQUESTED ->
    PENDING -> {REMOVED, DENIED}. Skips, backward moves, and no-ops are all
    rejected — e.g. FOUND -> REMOVED directly is invalid.
    """
    return (from_status, to_status) in _VALID_TRANSITIONS
