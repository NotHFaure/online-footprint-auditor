"""Shared interface every source-specific scanner implements."""

from __future__ import annotations

from typing import Protocol

from footprint_auditor.models import Finding, Target


class Scanner(Protocol):
    """A single source category (name search, reverse-image, data broker, ...)."""

    def scan(self, target: Target) -> list[Finding]:
        """Run this scanner against target and return whatever it finds."""
        ...
