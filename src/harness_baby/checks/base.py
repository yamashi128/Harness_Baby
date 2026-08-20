"""Extension point for deterministic checks."""

from __future__ import annotations

from abc import ABC, abstractmethod

from harness_baby.models import CheckResult, ScanContext


class Check(ABC):
    """A side-effect-free repository check."""

    id: str
    category: str

    @abstractmethod
    def run(self, context: ScanContext) -> CheckResult:
        """Observe the repository and return structured evidence."""
