"""SQLite persistence for scan results and the remediation tracker.

The caller decides where the database file lives — normally
`config.get_data_dir() / "results.db"` in real use, or ":memory:" in tests —
so this module stays testable without touching the real private data
directory.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from footprint_auditor.models import (
    Finding,
    RemediationRecord,
    RemediationStatus,
    Target,
    can_transition,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_name TEXT NOT NULL,
    source TEXT NOT NULL,
    category TEXT NOT NULL,
    url TEXT,
    summary TEXT,
    risk_score INTEGER NOT NULL,
    discovered_at TEXT NOT NULL,
    automated INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS remediation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id INTEGER NOT NULL REFERENCES findings(id),
    status TEXT NOT NULL,
    status_history TEXT NOT NULL,
    notes TEXT
);
"""


class Storage:
    """Wraps a sqlite3 connection for findings and remediation tracking."""

    def __init__(self, db_path: Path | str) -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def save_findings(self, target: Target, findings: list[Finding]) -> list[Finding]:
        """Persist findings for a target, seeding a FOUND remediation record each.

        Skips re-inserting a finding that already exists for this exact
        (target, source, category, url) — the original id and its full
        remediation history are preserved, not reset, so re-scanning the
        same target repeatedly doesn't accumulate duplicate rows or wipe out
        remediation progress already tracked for something still present.
        """
        saved: list[Finding] = []
        for finding in findings:
            existing = self._conn.execute(
                """
                SELECT id, source, category, url, summary, risk_score, discovered_at, automated
                FROM findings
                WHERE target_name = ? AND source = ? AND category = ? AND url = ?
                """,
                (target.name, finding.source, finding.category, finding.url),
            ).fetchone()
            if existing is not None:
                saved.append(
                    Finding(
                        id=existing[0],
                        source=existing[1],
                        category=existing[2],
                        url=existing[3],
                        summary=existing[4],
                        risk_score=existing[5],
                        discovered_at=datetime.fromisoformat(existing[6]),
                        automated=bool(existing[7]),
                    )
                )
                continue

            cursor = self._conn.execute(
                """
                INSERT INTO findings
                    (target_name, source, category, url, summary, risk_score,
                     discovered_at, automated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target.name,
                    finding.source,
                    finding.category,
                    finding.url,
                    finding.summary,
                    finding.risk_score,
                    finding.discovered_at.isoformat(),
                    int(finding.automated),
                ),
            )
            finding_id = cursor.lastrowid
            history = [(RemediationStatus.FOUND, datetime.now(UTC))]
            self._conn.execute(
                """
                INSERT INTO remediation (finding_id, status, status_history, notes)
                VALUES (?, ?, ?, ?)
                """,
                (
                    finding_id,
                    RemediationStatus.FOUND,
                    _encode_history(history),
                    None,
                ),
            )
            saved.append(
                Finding(
                    source=finding.source,
                    category=finding.category,
                    url=finding.url,
                    summary=finding.summary,
                    risk_score=finding.risk_score,
                    discovered_at=finding.discovered_at,
                    automated=finding.automated,
                    id=finding_id,
                )
            )
        self._conn.commit()
        return saved

    def get_findings_by_target(self, target_name: str) -> list[Finding]:
        """Return all findings previously saved for target_name."""
        rows = self._conn.execute(
            """
            SELECT id, source, category, url, summary, risk_score, discovered_at, automated
            FROM findings
            WHERE target_name = ?
            """,
            (target_name,),
        ).fetchall()
        return [
            Finding(
                id=row[0],
                source=row[1],
                category=row[2],
                url=row[3],
                summary=row[4],
                risk_score=row[5],
                discovered_at=datetime.fromisoformat(row[6]),
                automated=bool(row[7]),
            )
            for row in rows
        ]

    def get_finding_by_id(self, finding_id: int) -> Finding | None:
        """Return a single finding by its storage-assigned id, or None if it doesn't exist."""
        row = self._conn.execute(
            """
            SELECT id, source, category, url, summary, risk_score, discovered_at, automated
            FROM findings
            WHERE id = ?
            """,
            (finding_id,),
        ).fetchone()
        if row is None:
            return None
        return Finding(
            id=row[0],
            source=row[1],
            category=row[2],
            url=row[3],
            summary=row[4],
            risk_score=row[5],
            discovered_at=datetime.fromisoformat(row[6]),
            automated=bool(row[7]),
        )

    def get_remediation_status(self, finding_id: int) -> RemediationRecord | None:
        """Return the remediation record for a finding, or None if it doesn't exist."""
        row = self._conn.execute(
            "SELECT status, status_history, notes FROM remediation WHERE finding_id = ?",
            (finding_id,),
        ).fetchone()
        if row is None:
            return None
        return RemediationRecord(
            finding_id=finding_id,
            status=RemediationStatus(row[0]),
            status_history=_decode_history(row[1]),
            notes=row[2],
        )

    def update_remediation_status(
        self,
        finding_id: int,
        new_status: RemediationStatus,
        notes: str | None = None,
    ) -> None:
        """Move a finding's remediation status forward, or raise on an invalid transition."""
        row = self._conn.execute(
            "SELECT status, status_history FROM remediation WHERE finding_id = ?",
            (finding_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"No remediation record exists for finding_id={finding_id}")

        current_status = RemediationStatus(row[0])
        if not can_transition(current_status, new_status):
            raise ValueError(
                f"Invalid remediation transition for finding_id={finding_id}: "
                f"{current_status} -> {new_status}"
            )

        history = _decode_history(row[1])
        history.append((new_status, datetime.now(UTC)))
        self._conn.execute(
            "UPDATE remediation SET status = ?, status_history = ?, notes = ? WHERE finding_id = ?",
            (new_status, _encode_history(history), notes, finding_id),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def _encode_history(history: list[tuple[RemediationStatus, datetime]]) -> str:
    return json.dumps([[status.value, ts.isoformat()] for status, ts in history])


def _decode_history(raw: str) -> list[tuple[RemediationStatus, datetime]]:
    return [
        (RemediationStatus(status), datetime.fromisoformat(ts)) for status, ts in json.loads(raw)
    ]
