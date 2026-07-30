"""Automated opt-out submitters, keyed by broker name.

Empty by design: no vendored broker (data/broker_list.py) currently has
supports_automated_optout=True — determining which sites genuinely expose a
scriptable opt-out flow is real per-site research nobody has done yet.
Fabricating a submission for a real company here would be a real action with
real consequences, not a placeholder. Populate this registry only once a
broker entry is flipped to True after that research happens.
"""

from __future__ import annotations

from collections.abc import Callable

from footprint_auditor.models import Finding

AUTOMATED_SUBMITTERS: dict[str, Callable[[Finding], None]] = {}
