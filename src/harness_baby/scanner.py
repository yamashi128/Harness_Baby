"""Repository observation and check orchestration."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from harness_baby import __version__
from harness_baby.checks import built_in_checks
from harness_baby.checks.base import Check
from harness_baby.models import ScanContext, ScanReport
from harness_baby.scoring import summarize

IGNORED_DIRECTORIES = {
    ".git",
    ".harness",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".terraform",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


def collect_files(root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        directory_names[:] = sorted(
            name for name in directory_names if name not in IGNORED_DIRECTORIES
        )
        current_path = Path(current)
        for name in sorted(file_names):
            path = current_path / name
            if not path.is_symlink():
                files.append(path)
    return tuple(files)


def detect_stacks(root: Path, files: tuple[Path, ...]) -> tuple[str, ...]:
    stacks: list[str] = []
    if (
        (root / "pyproject.toml").is_file()
        or (root / "requirements.txt").is_file()
        or any(path.suffix == ".py" for path in files)
    ):
        stacks.append("python")
    if any(path.suffix == ".tf" for path in files):
        stacks.append("terraform")
    workflow_root = root / ".github" / "workflows"
    if any(
        path.parent == workflow_root and path.suffix.lower() in {".yml", ".yaml"} for path in files
    ):
        stacks.append("github_actions")
    return tuple(stacks)


class Scanner:
    def __init__(self, checks: Sequence[Check] | None = None) -> None:
        self.checks = tuple(checks) if checks is not None else built_in_checks()

    def scan(self, path: str | Path) -> ScanReport:
        root = Path(path).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {path}")
        files = collect_files(root)
        try:
            display_path = Path(os.path.relpath(root, Path.cwd())).as_posix()
        except ValueError:
            display_path = root.as_posix()
        context = ScanContext(root, display_path, files, detect_stacks(root, files))
        results = [check.run(context) for check in self.checks]
        if len({result.id for result in results}) != len(results):
            raise ValueError("Check IDs must be unique")
        return ScanReport(
            schema_version=1,
            tool={"name": "harness-baby", "version": __version__},
            project={"path": display_path, "detected_stacks": list(context.detected_stacks)},
            summary=summarize(results),
            checks={result.id: result.as_dict() for result in results},
        )
