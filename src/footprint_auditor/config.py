"""Resolves and loads configuration from the private, out-of-repo data directory.

See CLAUDE.md's "Data boundary" section: this directory lives entirely outside
the git working tree, resolved via platformdirs. Nothing in this module ever
writes API keys, target identifiers, or scan output into this repository.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from platformdirs import user_data_dir

_APP_NAME = "online-footprint-auditor"

_CONFIG_TEMPLATE = """\
# Online Footprint Auditor configuration.
# Fill in the values below, then re-run.

[hibp]
# api_key = "your-hibp-api-key"

[searxng]
# Optional. Enables real automated name/social-media/data-broker search via a
# self-hosted SearXNG instance (see README). Leaving this unset defaults to
# http://localhost:8080 — change it here if you move SearXNG to another host
# (e.g. a homelab server) later; no code change is needed.
# base_url = "http://localhost:8080"

[target]
# name = "Jane Doe"
# emails = ["jane@example.com"]
# images = ["/path/to/photo.jpg"]
# org_affiliations = ["Acme Corp"]
"""


def get_data_dir() -> Path:
    """Resolve the private data directory, creating it if it doesn't exist yet.

    appauthor=False avoids platformdirs doubling the path segment on Windows
    (without it, the app name would appear twice in the resolved path).
    """
    data_dir = Path(user_data_dir(_APP_NAME, appauthor=False))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def load_config(data_dir: Path | None = None) -> dict:
    """Load config.toml from the private data directory.

    data_dir overrides the resolved directory — used by tests/smoke checks so
    they never touch the real, per-machine private data directory.

    If config.toml doesn't exist yet, a commented template is written and the
    process exits with instructions — never proceed silently with an empty
    config, per the fail-loudly convention.
    """
    resolved_dir = data_dir if data_dir is not None else get_data_dir()
    resolved_dir.mkdir(parents=True, exist_ok=True)
    config_path = resolved_dir / "config.toml"

    if not config_path.exists():
        config_path.write_text(_CONFIG_TEMPLATE, encoding="utf-8")
        raise SystemExit(
            f"No configuration found. A template has been created at:\n"
            f"  {config_path}\n"
            f"Fill in the required values, then re-run."
        )

    with config_path.open("rb") as f:
        return tomllib.load(f)
