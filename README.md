# Harness Doctor

Harness Doctor is a deterministic CLI that observes whether a repository gives an AI coding agent enough safe, repeatable feedback to work autonomously. It detects repository metadata, Python, Terraform, and GitHub Actions signals, then emits evidence-backed readiness checks and a machine-readable YAML report.

It is not an AI agent. It does not call an LLM, change source or configuration, install dependencies, run Terraform, contact external services, or generate fixes. The only repository write made by the default command is the requested `.harness/report.yaml` artifact.

## Install

Python 3.12 or newer is required.

```bash
python -m pip install -e .
```

For development tools:

```bash
python -m pip install -e '.[dev]'
```

## Usage

Scan the current directory:

```bash
harness-doctor scan .
```

Choose another report destination:

```bash
harness-doctor scan /path/to/repository --output /tmp/report.yaml
```

The command prints a compact summary and writes `<repository>/.harness/report.yaml` by default. Finding failed checks does not make the process fail; exit code `2` is reserved for invocation, path, or report-write errors.

## Report schema

Schema version 1 has five stable top-level fields. Evidence fields may grow as checks improve.

```yaml
schema_version: 1
tool:
  name: harness-doctor
  version: 0.1.0
project:
  path: .
  detected_stacks:
    - python
summary:
  score: 75
  passed: 5
  warned: 2
  failed: 1
  skipped: 2
checks:
  testing:
    category: testing
    status: pass
    evidence:
      frameworks:
        - pytest
      test_files:
        - tests/test_app.py
      pyproject_parse_error: null
```

Every check has an ID, category, status (`pass`, `warn`, `fail`, or `skip`), and evidence. Secret findings contain only a file, line number, and finding kind—never the suspected value.

The score is calculated in `scoring.py`: pass is `1.0`, warn is `0.5`, fail is `0`, and skip is excluded. Each check has weight `1.0` in the MVP, while the scoring API already accepts explicit per-check weights.

## Supported stacks and checks

- Repository: Git marker and license evidence
- Documentation: root README
- Agent context: root `AGENTS.md`
- Python: `pyproject.toml`, `requirements.txt`, pytest, unittest, ruff, flake8, black, mypy, and coverage-related configuration evidence
- Terraform: `.tf` files, module directories, Terraform executable availability, tflint, tfsec/checkov configuration, and read-only fmt/validate readiness
- GitHub Actions: workflows, test/lint/Terraform validate command signals, YAML parse failures, and a deliberately small hardcoded-secret heuristic
- Reproducibility: common Python lockfiles, pinned requirements, and Terraform lockfiles

Terraform commands are never executed. `terraform_binary_available` describes the current environment, while `commands_executed` remains empty. This avoids state changes, implicit initialization, and network access.

## Architecture

`Scanner` performs bounded, sorted file discovery, detects stacks, and executes an ordered registry of `Check` implementations. A check receives an immutable `ScanContext` and returns a `CheckResult`; it does not mutate the repository. Adding a stack means adding checks under `src/harness_doctor/checks/` and registering them in `built_in_checks()`.

The score policy and YAML reporter are independent modules. YAML output preserves registry order and contains no timestamps, making repeated scans stable when repository and relevant tool availability are unchanged.

## Development

```bash
pytest
ruff check .
ruff format --check .
mypy
```

## Roadmap

After the MVP, likely additions are a versioned external plugin discovery contract, configurable check weights, optional report history, more robust workflow semantics, and support for Node.js, Go, Rust, Java, Docker, Kubernetes, and Ansible.

Dynamic plugins, command execution, auto-fixes, historical reports, remote integrations, and exhaustive secret scanning are intentionally outside the MVP.

