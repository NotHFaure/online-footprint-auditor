"""CLI entrypoint: scan, status, remediate.

The real logic lives in plain _run_* functions, kept free of click and free of
config/Storage construction — the click commands are thin wrappers around
them. This is what makes the orchestration testable with fake scanners, an
in-memory Storage, and a temp directory, without any real I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import click

from footprint_auditor.config import get_data_dir, load_config
from footprint_auditor.data.broker_list import BROKERS
from footprint_auditor.models import RemediationStatus, Target
from footprint_auditor.profile import generate_profile
from footprint_auditor.remediation.automated import AUTOMATED_SUBMITTERS
from footprint_auditor.remediation.manual import write_manual_instructions
from footprint_auditor.report import generate_checklist, generate_report, generate_risk_list
from footprint_auditor.scanners.base import Scanner
from footprint_auditor.scanners.breach import BreachScanner
from footprint_auditor.scanners.data_broker import DataBrokerScanner
from footprint_auditor.scanners.name_search import NameSearchScanner
from footprint_auditor.scanners.reverse_image import ReverseImageScanner
from footprint_auditor.scanners.social_media import SocialMediaScanner
from footprint_auditor.scoring import score_finding
from footprint_auditor.searxng import DEFAULT_BASE_URL, SearxngClient
from footprint_auditor.storage import Storage


@dataclass
class ScanSummary:
    finding_count: int
    output_dir: Path


def _run_scan(
    target: Target,
    scanners: list[Scanner],
    storage: Storage,
    output_dir: Path,
) -> ScanSummary:
    """Run every scanner, score the results for real, persist, and write output files."""
    all_findings = []
    for scanner in scanners:
        all_findings.extend(scanner.scan(target))

    for finding in all_findings:
        finding.risk_score = score_finding(finding)

    saved = storage.save_findings(target, all_findings)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.md").write_text(generate_report(saved), encoding="utf-8")
    (output_dir / "checklist.md").write_text(generate_checklist(saved), encoding="utf-8")
    (output_dir / "risk_list.md").write_text(generate_risk_list(saved), encoding="utf-8")
    (output_dir / "profile.md").write_text(generate_profile(saved), encoding="utf-8")

    return ScanSummary(finding_count=len(saved), output_dir=output_dir)


def _run_status(target_name: str, storage: Storage) -> str:
    """Read-only view of every finding's current remediation status."""
    findings = storage.get_findings_by_target(target_name)
    if not findings:
        return f"No findings recorded for '{target_name}'."

    lines = [f"Remediation status for '{target_name}':", ""]
    for finding in findings:
        record = storage.get_remediation_status(finding.id) if finding.id is not None else None
        status = record.status if record is not None else "unknown"
        lines.append(f"- [{finding.id}] {finding.category} / {finding.source}: {status}")
    return "\n".join(lines)


def _run_remediate(
    finding_id: int,
    storage: Storage,
    data_dir: Path,
    confirm_sent: bool,
) -> str:
    """Route a finding to automated or manual remediation, or confirm it was sent."""
    finding = storage.get_finding_by_id(finding_id)
    if finding is None:
        raise ValueError(f"No finding with id={finding_id}")

    if finding.category != "data_broker":
        raise ValueError(
            f"Remediation isn't defined for category '{finding.category}' — "
            f"only data_broker findings support opt-out requests currently."
        )

    if confirm_sent:
        storage.update_remediation_status(finding_id, RemediationStatus.REQUESTED)
        return f"Marked finding {finding_id} as REQUESTED."

    broker = next((b for b in BROKERS if b.name == finding.source), None)
    if broker is None:
        raise ValueError(f"No vendored broker entry matches source '{finding.source}'")

    if broker.supports_automated_optout:
        submit = AUTOMATED_SUBMITTERS.get(broker.name)
        if submit is None:
            raise RuntimeError(
                f"{broker.name} is flagged supports_automated_optout=True but has no "
                f"registered submitter — this is a bug, not an operator error."
            )
        submit(finding)
        storage.update_remediation_status(finding_id, RemediationStatus.REQUESTED)
        return f"Automated opt-out submitted to {broker.name}; marked REQUESTED."

    path = write_manual_instructions(finding, broker, data_dir)
    return (
        f"Manual instructions written to {path}. Once you've sent the request, "
        f"run remediate again with --confirm-sent to mark it REQUESTED."
    )


def _build_target(config: dict) -> Target:
    target_config = config.get("target", {})
    name = target_config.get("name")
    if not name:
        raise SystemExit("config.toml's [target] section needs a 'name' — see the template.")
    return Target(
        name=name,
        emails=target_config.get("emails", []),
        images=target_config.get("images", []),
        org_affiliations=target_config.get("org_affiliations", []),
    )


def _build_scanners(config: dict) -> list[Scanner]:
    searxng_base_url = config.get("searxng", {}).get("base_url", DEFAULT_BASE_URL)
    searxng_client = SearxngClient(base_url=searxng_base_url)
    searxng: SearxngClient | None
    if searxng_client.is_available():
        click.echo(f"Automated search enabled via SearXNG at {searxng_base_url}")
        searxng = searxng_client
    else:
        click.echo(
            f"SearXNG not reachable at {searxng_base_url} — name search, data broker, "
            f"and social media will use manual-check links only this run."
        )
        searxng = None

    scanners: list[Scanner] = [
        NameSearchScanner(searxng),
        ReverseImageScanner(),
        DataBrokerScanner(searxng),
        SocialMediaScanner(searxng),
    ]
    api_key = config.get("hibp", {}).get("api_key")
    if api_key:
        scanners.append(BreachScanner(api_key=api_key))
    else:
        click.echo("HIBP breach scanning skipped — no API key configured in config.toml.")
    return scanners


@click.group()
def cli() -> None:
    """Online Footprint Auditor — local OSINT footprint audit CLI."""


@cli.command()
def scan() -> None:
    """Run every scanner against the configured target and write report/checklist/risk-list."""
    config = load_config()
    target = _build_target(config)
    scanners = _build_scanners(config)
    storage = Storage(get_data_dir() / "results.db")
    output_dir = get_data_dir() / "scans" / target.name.replace(" ", "_")
    summary = _run_scan(target, scanners, storage, output_dir)
    storage.close()
    click.echo(f"Scan complete: {summary.finding_count} findings.")
    click.echo(f"Report, checklist, and risk list written to {summary.output_dir}")


@cli.command()
def status() -> None:
    """Show the current remediation status of every finding for the configured target."""
    config = load_config()
    target = _build_target(config)
    storage = Storage(get_data_dir() / "results.db")
    click.echo(_run_status(target.name, storage))
    storage.close()


@cli.command()
@click.option("--finding-id", type=int, required=True)
@click.option("--confirm-sent", is_flag=True, default=False)
def remediate(finding_id: int, confirm_sent: bool) -> None:
    """Generate (or submit) an opt-out request for a data-broker finding."""
    storage = Storage(get_data_dir() / "results.db")
    click.echo(_run_remediate(finding_id, storage, get_data_dir(), confirm_sent))
    storage.close()
