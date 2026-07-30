"""Deterministic, structured summary of what's discoverable about a target.

No AI/LLM is used here, deliberately — see EP-2026-07-30-007's scope note:
sending consolidated personal findings to a third-party API would be a real
cost and a real new privacy boundary, and Harry chose not to cross it.
"""

from __future__ import annotations

from footprint_auditor.models import Finding
from footprint_auditor.scoring import score_finding


def generate_profile(findings: list[Finding]) -> str:
    if not findings:
        return "# Profile Summary\n\nNo findings.\n"

    by_category = _group_by_category(findings)
    lines = ["# Profile Summary", "", "## Overview", "", f"- Total findings: {len(findings)}"]
    for category in sorted(by_category):
        items = by_category[category]
        automated_count = sum(1 for f in items if f.automated)
        lines.append(
            f"- {category.replace('_', ' ').title()}: {len(items)} total "
            f"({automated_count} automatically confirmed, "
            f"{len(items) - automated_count} need manual review)"
        )
    lines.append("")

    breaches = by_category.get("breach", [])
    lines.append("## Breach exposure")
    lines.append("")
    lines.extend(
        [f"- {f.summary}" for f in breaches] if breaches else ["No confirmed breaches found."]
    )
    lines.append("")

    confirmed = [
        f
        for f in findings
        if f.automated and f.category in ("name_search", "social_media", "data_broker")
    ]
    lines.append("## Confirmed online activity")
    lines.append("")
    lines.append(
        "These matched the target's exact name, but automated search can still surface "
        "unrelated pages that happen to contain it — review before treating as confirmed."
    )
    lines.append("")
    if confirmed:
        lines.extend(
            f"- **{f.category.replace('_', ' ')}** via {f.source}: {f.summary} — {f.url}"
            for f in confirmed
        )
    else:
        lines.append(
            "No automatically confirmed matches this run — see the manual-review links in "
            "report.md."
        )
    lines.append("")

    lines.append("## Highest-risk findings")
    lines.append("")
    ranked = sorted(findings, key=score_finding, reverse=True)[:5]
    lines.extend(f"- ({score_finding(f)}) {f.category} / {f.source}: {f.summary}" for f in ranked)
    lines.append("")

    return "\n".join(lines)


def _group_by_category(findings: list[Finding]) -> dict[str, list[Finding]]:
    groups: dict[str, list[Finding]] = {}
    for finding in findings:
        groups.setdefault(finding.category, []).append(finding)
    return groups
