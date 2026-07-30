"""Generates a per-source manual opt-out instruction document for the operator.

This tool never submits an ID-verified removal request automatically — the
operator must complete that step personally. This module only produces the
instructions; sending them is on the operator.
"""

from __future__ import annotations

from pathlib import Path

from footprint_auditor.data.broker_list import BrokerEntry
from footprint_auditor.models import Finding

_TEMPLATE = """\
# Manual Opt-Out Instructions — {broker_name}

Finding ID: {finding_id}
Source: {broker_name}
Check/opt-out page: {broker_url}

Steps:
1. Visit {broker_url}
2. Search for the target and confirm whether they're listed.
3. Follow {broker_name}'s own opt-out/removal process from that page — this
   generally requires submitting a request directly on their site. Some
   brokers require ID verification; the operator must complete that step
   personally (this tool never submits ID-verified requests automatically).
4. Once you've sent the request, run:
   footprint-auditor remediate --finding-id {finding_id} --confirm-sent
"""


def write_manual_instructions(finding: Finding, broker: BrokerEntry, data_dir: Path) -> Path:
    """Write the instruction document to <data_dir>/remediation/ and return its path."""
    instructions_dir = data_dir / "remediation"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    safe_broker_name = broker.name.replace(" ", "_").replace("'", "")
    path = instructions_dir / f"{safe_broker_name}_finding_{finding.id}.md"
    content = _TEMPLATE.format(
        broker_name=broker.name,
        finding_id=finding.id,
        broker_url=broker.url,
    )
    path.write_text(content, encoding="utf-8")
    return path
