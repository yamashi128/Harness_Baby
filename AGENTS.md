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
python -m pip install -e '.[dev]'
harness-doctor scan .
```

## Test commands

```bash
pytest
ruff check .
ruff format --check .
mypy
```

## Constraints

- Python 3.12 or newer.
- Checks must be deterministic, offline, and side-effect-free.
- Never run destructive commands, Terraform apply, or external-service calls.
- Never include detected secret values in evidence or logs.
- Preserve schema compatibility within schema version 1.

## Definition of Done

Editable installation succeeds; tests, lint, formatting, and type checks pass; `harness-doctor scan .` produces `.harness/report.yaml`; user-facing behavior is documented.

