"""Markdown output generation: full report, actionable checklist, scored risk list.

All three are pure functions over list[Finding] — no I/O, no Storage access.
A clean scan with zero findings is a valid, expected outcome, not an error, so
each function returns a short "no findings" document rather than raising.
"""

from __future__ import annotations

from footprint_auditor.models import Finding
from footprint_auditor.scoring import score_finding


def generate_report(findings: list[Finding]) -> str:
    """Full narrative report, one section per category."""
    if not findings:
        return "# Footprint Audit Report\n\nNo findings.\n"

    lines = ["# Footprint Audit Report", ""]
    by_category = _group_by_category(findings)
    for category in sorted(by_category):
        lines.append(f"## {category.replace('_', ' ').title()}")
        lines.append("")
        for finding in by_category[category]:
            marker = "Automated" if finding.automated else "Manual review needed"
            lines.append(f"- **{finding.source}** ({marker}): {finding.summary} — {finding.url}")
        lines.append("")
    return "\n".join(lines)


def generate_checklist(findings: list[Finding]) -> str:
    """Actionable checklist, one line per finding.

    A bare list[Finding] carries no remediation status — that lives in
    RemediationRecord, keyed separately in Storage, and isn't available here.
    Every finding passed in is, by construction, freshly scanned and not yet
    acted on, so everything groups under one heading rather than fabricating
    status buckets the input doesn't support. A richer version that reads
    real remediation state belongs to the CLI (Phase 5), which has Storage
    access — not this module.
    """
    if not findings:
        return "# Remediation Checklist\n\nNo findings.\n"

    lines = ["# Remediation Checklist", "", "## Found — not yet actioned", ""]
    for finding in findings:
        lines.append(f"- [ ] {finding.category}: {finding.summary} ({finding.url})")
    lines.append("")
    return "\n".join(lines)


def generate_risk_list(findings: list[Finding]) -> str:
    """Findings ranked by score_finding, descending, as a Markdown table.

    The Status column is the literal text "Found" for every row — real
    remediation status isn't available at this layer (see generate_checklist).
    """
    if not findings:
        return "# Risk List\n\nNo findings.\n"

    ranked = sorted(findings, key=score_finding, reverse=True)
    lines = [
        "# Risk List",
        "",
        "| Source | Category | Score | Status |",
        "| :--- | :--- | ---: | :--- |",
    ]
    for finding in ranked:
        lines.append(
            f"| {finding.source} | {finding.category} | {score_finding(finding)} | Found |"
        )
    lines.append("")
    return "\n".join(lines)


def _group_by_category(findings: list[Finding]) -> dict[str, list[Finding]]:
    groups: dict[str, list[Finding]] = {}
    for finding in findings:
        groups.setdefault(finding.category, []).append(finding)
    return groups
