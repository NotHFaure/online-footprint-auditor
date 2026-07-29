# Online Footprint Auditor

## Purpose

A general-purpose, local Python CLI tool that runs an on-demand OSINT-style audit against a given target (name, images, known identifiers, associated organizations), surfaces what's publicly discoverable, scores risk, and tracks remediation status over time.

## Tech stack

- **Language / runtime:** Python 3.12+
- **Framework:** none (CLI tool)
- **Package manager:** `uv`
- **Key dependencies:** `click` (CLI), `httpx` (HTTP), `platformdirs` (private data directory resolution), `sqlite3` (stdlib, persistence)
- **Dev dependencies:** `pytest`, `ruff`, `mypy`

## Commands

- Install: `uv sync`
- Run (dev): `uv run footprint-auditor` (not yet implemented — scaffold only)
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Typecheck: `uv run mypy src/`

## Architecture

- `src/footprint_auditor/` — package root (currently empty scaffold; scanners, models, storage, CLI wiring land in future phases)
- `tests/` — test suite (currently empty scaffold)

Modular scanner-per-source design is planned: one scanner module per source category (name search, reverse-image, data broker, social media, breach/HIBP) behind a shared interface.

## Testing

Tests for non-trivial logic only (scoring, remediation state transitions, parsers) — skip tests for thin API-wrapper glue. Framework: `pytest`. Run a single test: `uv run pytest tests/test_file.py::test_name`.

## Git workflow

Feature branches; show a diff/summary before committing; don't commit unless asked.

## Data boundary — read this before writing any code here

This repository contains **tool code only**. Scan results, target identifiers, and API keys/config live **outside this repository entirely**, in a local data directory resolved via `platformdirs.user_data_dir("online-footprint-auditor")`. Never write PII, API keys, or scan output into this repo. This separation is structural (a distinct directory outside the git working tree), not just a `.gitignore` convention.

## Responsible use

This tool is general-purpose: it can be pointed at any target (self, a consented check, business-contact due diligence, research). It does not build in a consent-verification gate. The operator is responsible for ensuring each use is lawful and consented to — including anti-stalking/harassment law, unauthorized-access statutes, and platform Terms of Service around automated querying. The tool itself does not enforce or verify lawful use.

## Project-specific rules

This repository is public by explicit, recorded exception to the default private-by-default policy of the governance workspace that planned this project (see that workspace's approval queue, items covering repository visibility, the data boundary above, and standard packet-gated development flow, all dated 2026-07-29). Ordinary development commits/pushes follow the normal packet-gated flow — there is no blanket auto-push exception.
