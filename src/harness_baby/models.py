"""Data models shared by Harness Baby scanners, checks, scoring, and reporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Status(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass(frozen=True)
class CheckResult:
    id: str
    category: str
    status: Status
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "status": self.status.value,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class ScanContext:
    root: Path
    display_path: str
    files: tuple[Path, ...]
    detected_stacks: tuple[str, ...]

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def paths_named(self, *names: str) -> list[Path]:
        wanted = set(names)
        return [path for path in self.files if path.name in wanted]

    def paths_with_suffix(self, *suffixes: str) -> list[Path]:
        wanted = set(suffixes)
        return [path for path in self.files if path.suffix in wanted]


@dataclass(frozen=True)
class ScanReport:
    schema_version: int
    tool: dict[str, str]
    project: dict[str, Any]
    summary: dict[str, int]
    checks: dict[str, dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tool": self.tool,
            "project": self.project,
            "summary": self.summary,
            "checks": self.checks,
        }
