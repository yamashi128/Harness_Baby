"""Independent weighted score calculation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from harness_baby.models import CheckResult, Status

STATUS_VALUES: Mapping[Status, float] = {
    Status.PASS: 1.0,
    Status.WARN: 0.5,
    Status.FAIL: 0.0,
}


def calculate_score(
    results: Sequence[CheckResult], weights: Mapping[str, float] | None = None
) -> int:
    """Calculate a 0-100 score; skipped checks do not affect the denominator."""
    configured_weights = weights or {}
    earned = 0.0
    possible = 0.0
    for result in results:
        if result.status is Status.SKIP:
            continue
        weight = configured_weights.get(result.id, 1.0)
        if weight < 0:
            raise ValueError(f"Weight for {result.id!r} cannot be negative")
        possible += weight
        earned += STATUS_VALUES[result.status] * weight
    return round((earned / possible) * 100) if possible else 0


def summarize(results: Sequence[CheckResult]) -> dict[str, int]:
    return {
        "score": calculate_score(results),
        "passed": sum(result.status is Status.PASS for result in results),
        "warned": sum(result.status is Status.WARN for result in results),
        "failed": sum(result.status is Status.FAIL for result in results),
        "skipped": sum(result.status is Status.SKIP for result in results),
    }
