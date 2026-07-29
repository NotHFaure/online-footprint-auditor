# Online Footprint Auditor

A local, general-purpose OSINT-style CLI tool that audits what's publicly discoverable about a target (name, images, identifiers, associated organizations), scores the risk of each finding, and tracks remediation progress over time.

This repository contains tool code only — no scan results, target data, or credentials ever live here (see **Data boundary** below).

## Status

Scaffold only. Scanner logic, CLI commands, and storage are not implemented yet.

## Install

```
uv sync
```

## Private data

All API keys, target identifiers, scan results, and the remediation tracker live in a local data directory resolved via `platformdirs.user_data_dir("online-footprint-auditor")` (e.g. `%LOCALAPPDATA%\online-footprint-auditor` on Windows). It does not exist until the tool is run for the first time, and it is never committed or pushed — this repo has no knowledge of its contents.

## HIBP (Have I Been Pwned) breach checking

The HIBP API is paid-only. This tool treats it as a **one-time cost**: subscribe for a single month, run your scans during that window, then cancel. No ongoing subscription is required or assumed.

## Responsible use

This tool is general-purpose — it is not restricted to scanning your own identity, and it does not verify or enforce consent for whoever it's pointed at. You are responsible for ensuring each use is lawful and consented to, including anti-stalking/harassment law, unauthorized-access statutes, and the Terms of Service of any platform being queried. The tool itself does not check any of this for you.
