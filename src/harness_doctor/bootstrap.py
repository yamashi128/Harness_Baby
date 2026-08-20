"""Deterministic, preview-first repository harness bootstrap."""

from __future__ import annotations

import os
from contextlib import suppress
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import yaml

BOOTSTRAP_SCHEMA_VERSION = 1
TEMPLATE_ID = "generic-agent-ready"
TEMPLATE_VERSION = 1
MAX_REPORTED_CONFLICTS = 20
IGNORED_RUNTIME_ROOTS = {".git", ".harness"}
GENERATED_PATHS = (
    ".agent-readiness.yaml",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "docs/architecture.md",
    "docs/decisions/README.md",
    "docs/work-loop.md",
)


class BootstrapStatus(StrEnum):
    CREATE = "create"
    UNCHANGED = "unchanged"
    CONFLICT = "conflict"


@dataclass(frozen=True)
class BootstrapFile:
    relative_path: str
    content: str


@dataclass(frozen=True)
class BootstrapPlan:
    target: Path
    project_name: str
    files: tuple[BootstrapFile, ...]
    status: BootstrapStatus
    conflicts: tuple[str, ...] = ()


class BootstrapConflictError(ValueError):
    def __init__(self, conflicts: tuple[str, ...]) -> None:
        self.conflicts = conflicts
        super().__init__("Bootstrap target has conflicts: " + "; ".join(conflicts))


def _project_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise ValueError("Project name must not be empty")
    if len(name) > 100:
        raise ValueError("Project name must be 100 characters or fewer")
    if any(character in "\r\n" or ord(character) < 32 for character in name):
        raise ValueError("Project name must be a single printable line")
    return name


def _manifest(project_name: str) -> str:
    data = {
        "schema_version": BOOTSTRAP_SCHEMA_VERSION,
        "template": {"id": TEMPLATE_ID, "version": TEMPLATE_VERSION},
        "project": {"name": project_name},
        "generated_files": list(GENERATED_PATHS),
        "next_command": "harness-doctor scan .",
    }
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def _template_files(project_name: str) -> tuple[BootstrapFile, ...]:
    files = {
        ".agent-readiness.yaml": _manifest(project_name),
        ".gitignore": ".DS_Store\n.harness/report.yaml\n",
        "AGENTS.md": f"""# AGENTS.md

## Project purpose

TODO: Describe what {project_name} does and who it serves.

## Source of truth

- `README.md`: human entry point and setup
- `docs/architecture.md`: system boundaries and component map
- `docs/decisions/`: durable architecture decisions
- `docs/work-loop.md`: current goal, verification menu, and stop conditions

## Working loop

1. Read this file and the linked context before changing files.
2. State a small, verifiable goal.
3. Make the smallest change that advances that goal.
4. Run the documented verification commands.
5. Record durable decisions and leave a clear handoff.
6. Stop when the acceptance criteria pass or human input is required.

## Commands

- Readiness scan: `harness-doctor scan .`
- Tests: TODO: Add the real test command.
- Lint: TODO: Add the real lint command.
- Format check: TODO: Add the real formatting command.

## Constraints

- Do not invent commands, architecture, dependencies, or requirements.
- Do not expose credentials or secret values in code, logs, or reports.
- Do not overwrite existing work without explaining the intended change.
- Keep generated and machine-local artifacts out of version control.

## Definition of Done

- The stated acceptance criteria are satisfied.
- Documented verification commands pass.
- Relevant documentation and decisions are current.
- `harness-doctor scan .` has been reviewed; unresolved findings are explicit.
""",
        "README.md": f"""# {project_name}

This repository starts with a minimal, agent-neutral harness. It provides durable
places for project context, architecture, decisions, work state, and verification
without pretending that application code or engineering controls already exist.

## Start here

1. Replace the project-purpose TODO in `AGENTS.md`.
2. Record the first real system boundaries in `docs/architecture.md`.
3. Add real test, lint, and formatting commands to `AGENTS.md` and
   `docs/work-loop.md` when they exist.
4. Choose a license and initialize version control if needed.
5. Run the readiness scan:

```bash
harness-doctor scan .
```

Review `.harness/report.yaml`, improve one evidenced gap at a time, and scan again.

## Documentation map

- `AGENTS.md`: concise operating contract for coding agents
- `docs/architecture.md`: architecture facts and unknowns
- `docs/decisions/`: decision records
- `docs/work-loop.md`: persistent goal and verification loop

## Status

TODO: Describe the first useful milestone. This skeleton alone does not mean the
repository is ready for autonomous work.
""",
        "docs/architecture.md": f"""# Architecture

## Current state

No architecture was inferred because {project_name} was initialized from an empty
directory. Replace the TODO items only when repository evidence exists.

## System context

- Users: TODO
- External systems: TODO
- Inputs and outputs: TODO

## Components

TODO: List components and their responsibilities after they exist.

## Boundaries

TODO: State dependency, security, and data-ownership boundaries.

## Verification

TODO: Link each component to its real test or validation command.
""",
        "docs/decisions/README.md": """# Decision records

Record decisions that future humans and coding agents must not have to rediscover.

Create files named `NNNN-short-title.md` with:

```markdown
# Decision title

## Status
Proposed | Accepted | Superseded

## Context
What evidence and constraints require a decision?

## Decision
What was chosen?

## Consequences
What becomes easier, harder, or intentionally unsupported?
```
""",
        "docs/work-loop.md": """# Work loop

This file is persistent state for a human-reviewed coding-agent loop. Keep it short
and evidence-based.

## Goal

TODO: State one concrete outcome and its acceptance criteria.

## Action

TODO: Identify the smallest next change.

## Observation

Run only commands that are known to belong to this repository:

- Tests: TODO
- Lint: TODO
- Format check: TODO
- Readiness: `harness-doctor scan .`

Record failures as evidence; do not hide or relabel them as success.

## Adjustment

TODO: Use the latest verification result to choose the next action.

## Stop conditions

- Acceptance criteria pass.
- Required verification commands pass.
- Remaining readiness findings are accepted and documented.
- Stop early when the same failure repeats or human judgment is required.

## Handoff

TODO: Record what changed, what was verified, and the next unresolved item.
""",
    }
    return tuple(BootstrapFile(path, files[path]) for path in GENERATED_PATHS)


def _expected_entries(files: tuple[BootstrapFile, ...]) -> set[str]:
    entries: set[str] = set()
    for item in files:
        relative = Path(item.relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe generated path: {item.relative_path}")
        entries.add(relative.as_posix())
        parent = relative.parent
        while parent != Path("."):
            entries.add(parent.as_posix())
            parent = parent.parent
    return entries


def _existing_entries(target: Path) -> set[str]:
    entries: set[str] = set()
    for current, directory_names, file_names in os.walk(target, followlinks=False):
        current_path = Path(current)
        if current_path == target:
            directory_names[:] = [
                name for name in directory_names if name not in IGNORED_RUNTIME_ROOTS
            ]
            file_names = [name for name in file_names if name not in IGNORED_RUNTIME_ROOTS]
        for name in sorted((*directory_names, *file_names)):
            entries.add((current_path / name).relative_to(target).as_posix())
    return entries


def plan_bootstrap(path: str | Path, project_name: str | None = None) -> BootstrapPlan:
    requested = Path(path).expanduser()
    if requested.is_symlink():
        raise ValueError("Bootstrap target must not be a symbolic link")
    target = requested.resolve()
    if target.exists() and not target.is_dir():
        raise NotADirectoryError(f"Bootstrap target is not a directory: {path}")
    if not target.exists() and not target.parent.is_dir():
        raise ValueError(f"Bootstrap target parent does not exist: {target.parent}")

    name = _project_name(project_name if project_name is not None else target.name)
    files = _template_files(name)
    expected = _expected_entries(files)
    if not target.exists():
        return BootstrapPlan(target, name, files, BootstrapStatus.CREATE)

    existing = _existing_entries(target)
    if not existing:
        return BootstrapPlan(target, name, files, BootstrapStatus.CREATE)

    conflicts: list[str] = []
    for relative in sorted(existing - expected):
        conflicts.append(f"unexpected path: {relative}")
    for relative in sorted(expected - existing):
        conflicts.append(f"missing generated path: {relative}")
    for item in files:
        destination = target / item.relative_path
        if item.relative_path not in existing:
            continue
        if destination.is_symlink() or not destination.is_file():
            conflicts.append(f"generated path is not a regular file: {item.relative_path}")
            continue
        try:
            current = destination.read_text(encoding="utf-8")
        except OSError:
            conflicts.append(f"generated file is unreadable: {item.relative_path}")
            continue
        if current != item.content:
            conflicts.append(f"modified generated file: {item.relative_path}")

    if conflicts:
        if len(conflicts) > MAX_REPORTED_CONFLICTS:
            hidden_count = len(conflicts) - MAX_REPORTED_CONFLICTS
            conflicts = conflicts[:MAX_REPORTED_CONFLICTS]
            conflicts.append(f"additional conflicts not shown: {hidden_count}")
        return BootstrapPlan(
            target,
            name,
            files,
            BootstrapStatus.CONFLICT,
            tuple(conflicts),
        )
    return BootstrapPlan(target, name, files, BootstrapStatus.UNCHANGED)


def apply_bootstrap(path: str | Path, project_name: str | None = None) -> BootstrapPlan:
    plan = plan_bootstrap(path, project_name)
    if plan.status is BootstrapStatus.CONFLICT:
        raise BootstrapConflictError(plan.conflicts)
    if plan.status is BootstrapStatus.UNCHANGED:
        return plan

    created_files: list[Path] = []
    created_directories: list[Path] = []
    try:
        if not plan.target.exists():
            plan.target.mkdir()
            created_directories.append(plan.target)
        for item in plan.files:
            destination = plan.target / item.relative_path
            missing_parents: list[Path] = []
            parent = destination.parent
            while parent != plan.target and not parent.exists():
                missing_parents.append(parent)
                parent = parent.parent
            for directory in reversed(missing_parents):
                directory.mkdir()
                created_directories.append(directory)
            with destination.open("x", encoding="utf-8", newline="\n") as stream:
                created_files.append(destination)
                stream.write(item.content)
        result = plan_bootstrap(plan.target, plan.project_name)
        if result.status is not BootstrapStatus.UNCHANGED:
            raise ValueError("Bootstrap verification failed after writing files")
        return result
    except (OSError, ValueError):
        for created_file in reversed(created_files):
            with suppress(OSError):
                created_file.unlink()
        for created_directory in reversed(created_directories):
            with suppress(OSError):
                created_directory.rmdir()
        raise
