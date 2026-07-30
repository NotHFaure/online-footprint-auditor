# Online Footprint Auditor

A local, general-purpose OSINT-style CLI tool that audits what's publicly discoverable about a target (name, images, identifiers, associated organizations), scores the risk of each finding, and tracks remediation progress over time.

This repository contains tool code only — no scan results, target data, or credentials ever live here (see **Data boundary** below).

## Status

Core scanning, scoring, output generation, remediation, and the CLI are implemented, with automated unit tests for the non-trivial logic (scoring, remediation state machine, storage).

## Install

```
uv sync
```

## Usage

Fill in `config.toml` (created automatically on first run, in the private data directory below — see the printed path), then:

```
uv run footprint-auditor scan
```

Runs every scanner against the target configured in `config.toml`, scores each finding, persists it, and writes `report.md`, `checklist.md`, `risk_list.md`, and `profile.md` (a deterministic, non-AI summary — category counts, breach exposure, and a top-5 risk list) into the private data directory (not the repo, and not your terminal — these files can contain your target's PII). Re-running `scan` deduplicates against what's already on record — it won't create duplicate findings or reset remediation progress for something still present.

```
uv run footprint-auditor status
```

Read-only view of every finding's current remediation status.

```
uv run footprint-auditor remediate --finding-id <id>
uv run footprint-auditor remediate --finding-id <id> --confirm-sent
```

Only applies to `data_broker` findings. The first form writes manual opt-out instructions (or submits automatically, for the handful of brokers that support it — most don't yet); the second marks it `REQUESTED` once you've actually sent the request yourself.

## Automated search (optional)

By default, name search, data-broker checks, and social-media search generate manual, ready-to-click links for you to review — no automated network calls happen. If you'd rather get real automated results, run a self-hosted [SearXNG](https://docs.searxng.org/) instance and the tool will use it automatically, falling back to manual links for anything it doesn't find (or if SearXNG isn't running at all). No official free API exists for this kind of search; a self-hosted instance is the only free, Terms-of-Service-clean way to automate it — see `EP-2026-07-30-006` in this project's execution history for why.

To stand one up locally with Docker:

```
docker run -d --name searxng -p 8080:8080 -v /path/to/config:/etc/searxng \
  -e "BASE_URL=http://localhost:8080/" searxng/searxng:latest
```

Then add `search: formats: [html, json]` to the generated `settings.yml` in that config directory and restart the container — JSON output is disabled by default and this tool needs it.

By default the tool looks for SearXNG at `http://localhost:8080`. If you run it elsewhere (e.g. a homelab server), set `[searxng] base_url` in `config.toml` — no code change needed.

## Private data

All API keys, target identifiers, scan results, and the remediation tracker live in a local data directory resolved via `platformdirs.user_data_dir("online-footprint-auditor")` (e.g. `%LOCALAPPDATA%\online-footprint-auditor` on Windows). It does not exist until the tool is run for the first time, and it is never committed or pushed — this repo has no knowledge of its contents.

## HIBP (Have I Been Pwned) breach checking

The HIBP API is paid-only. This tool treats it as a **one-time cost**: subscribe for a single month, run your scans during that window, then cancel. No ongoing subscription is required or assumed.

## Responsible use

This tool is general-purpose — it is not restricted to scanning your own identity, and it does not verify or enforce consent for whoever it's pointed at. You are responsible for ensuring each use is lawful and consented to, including anti-stalking/harassment law, unauthorized-access statutes, and the Terms of Service of any platform being queried. The tool itself does not check any of this for you.
