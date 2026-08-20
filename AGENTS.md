# AGENTS.md

## Project purpose

Harness Doctor deterministically observes repository readiness for autonomous coding agents. It reports evidence and never edits the repository except for its requested report artifact.

## Architecture map

- `src/harness_doctor/scanner.py`: bounded file discovery and check orchestration
- `src/harness_doctor/checks/`: side-effect-free, extensible checks
- `src/harness_doctor/scoring.py`: score policy
- `src/harness_doctor/reporters/`: serialization
- `src/harness_doctor/cli.py`: CLI boundary
- `tests/`: isolated repository scenarios

See `README.md` for schema and behavior details.

## Development commands

```bash
uv sync --locked --extra dev
uv run harness-doctor scan .
```

If `uv` is unavailable, use `python -m pip install -e '.[dev]'` and run the same
tools directly.

## Test commands

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python -m build
uv run twine check dist/*
```

## Constraints

- Python 3.12 or newer.
- Checks must be deterministic, offline, and side-effect-free.
- Never run destructive commands, Terraform apply, or external-service calls.
- Never include detected secret values in evidence or logs.
- Preserve schema compatibility within schema version 1.
- New or changed checks require deterministic repository-scenario tests.
- Evidence must use stable, repository-relative values where practical.
- Do not publish packages, push release tags, or change repository visibility without explicit approval.

## Releases

Follow `docs/releasing.md`. Keep release credentials out of the repository and
use PyPI Trusted Publishing.

## Definition of Done

Locked installation succeeds; tests, lint, formatting, type checks, package
build, and wheel smoke tests pass; `harness-doctor scan .` produces a schema
version 1 report; user-facing behavior is documented.
