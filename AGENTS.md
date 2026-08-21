# AGENTS.md

## Project purpose

Harness Baby creates a minimal harness in an empty directory and deterministically
observes repository readiness for autonomous coding agents. `scan` reports evidence
and never edits source or configuration; `init --apply` is the single explicit,
bounded bootstrap mutation.

## Architecture map

- `src/harness_baby/scanner.py`: bounded file discovery and check orchestration
- `src/harness_baby/bootstrap.py`: preview-first generic skeleton planning and application
- `src/harness_baby/checks/`: side-effect-free, extensible checks
- `src/harness_baby/scoring.py`: score policy
- `src/harness_baby/reporters/`: serialization
- `src/harness_baby/cli.py`: CLI boundary
- `tests/`: isolated repository scenarios

See `README.md` for schema and behavior details.

## Development commands

```bash
uv sync --locked --extra dev
uv run harness-baby scan .
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

## Branch and pull request workflow

- `main` is the only long-lived branch and must remain releasable.
- Work on a short-lived `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, or
  `chore/<topic>` branch. Never push directly to `main`.
- Open a pull request to `main`; the required `quality` check must pass, the branch
  must be current with `main`, and all review conversations must be resolved.
- Use squash merge and delete the short-lived branch after merge.
- Treat forked pull requests and their code, workflows, dependencies, and generated
  artifacts as untrusted until their diffs have been reviewed.
- Follow `CONTRIBUTING.md` for the human-facing contribution and release workflow.

## Constraints

- Python 3.12 or newer.
- Checks must be deterministic, offline, and side-effect-free.
- `scan` may only write its requested report artifact.
- Bootstrap preview must never write; apply may create only the documented generic skeleton.
- Bootstrap must never overwrite existing content or provide a force flag.
- Never run destructive commands, Terraform apply, or external-service calls.
- Never include detected secret values in evidence or logs.
- Preserve schema compatibility within schema version 1.
- New or changed checks require deterministic repository-scenario tests.
- Evidence must use stable, repository-relative values where practical.
- Do not publish packages, push release tags, or change repository visibility without explicit approval.
- Never create, move, force-push, or delete a `v*.*.*` release tag without explicit
  release approval; release tags must point to a verified commit on `main`.

## Releases

Follow `docs/releasing.md`. Keep release credentials out of the repository and
use PyPI Trusted Publishing.

## Definition of Done

Locked installation succeeds; tests, lint, formatting, type checks, package build,
and wheel smoke tests pass. Bootstrap preview/apply/conflict/idempotence scenarios
pass; a generated skeleton can be scanned into a schema version 1 report; user-facing
behavior and mutation boundaries are documented.
