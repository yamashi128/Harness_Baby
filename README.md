# Harness Baby

Harness Baby is a deterministic CLI for people who want an AI coding agent to work
safely but do not yet know what repository harness to build. It gives an empty folder
the smallest honest starting structure, then scores readiness as you and your preferred
coding agent fill in the real project details.

You do not need to understand harness engineering before using it. Preview the starter
skeleton, create it explicitly, ask the coding agent you already like to help fill the
TODOs, and run the scan again. Harness Baby provides the first foothold and the feedback
loop; it does not choose your agent or pretend unfinished controls already exist.

## Project status

Harness Baby is experimental alpha software, not a stable release or a guarantee that
a repository is ready for production or unsupervised agent work. Use it at your own
risk. Review the preview before running `init --apply`, keep the target under version
control or backed up, and independently verify generated content, detected evidence,
and scores before relying on them. The software is provided without warranty under the
MIT License.

It is not an AI agent and never calls an LLM. `scan` does not change source or
configuration, install dependencies, run Terraform, or contact external services;
its only repository write is the requested `.harness/report.yaml` artifact. The
separate `init --apply` command writes only its reviewed generic skeleton into an
empty target.

## Install

Python 3.12 or newer is required.

Install the released CLI in an isolated environment with
[`pipx`](https://pipx.pypa.io/):

```bash
pipx install harness-baby --python python3.12
```

Upgrade or remove it with:

```bash
pipx upgrade harness-baby
pipx uninstall harness-baby
```

For development from a source checkout, use the commands in the Development section.

## Usage

### Start from an empty folder

Preview a generic, agent-neutral harness without writing anything:

```bash
harness-baby init my-project --project-name "My Project"
```

Create the exact preview explicitly:

```bash
harness-baby init my-project --project-name "My Project" --apply
```

The bootstrap creates seven context and feedback files. It does not invent source
code, tests, CI, dependencies, a license, or an architecture. See
[`docs/bootstrap.md`](https://github.com/yamashi128/Harness_Baby/blob/main/docs/bootstrap.md)
for the novice walkthrough and conflict
behavior.

### Check readiness

Scan the current directory:

```bash
harness-baby scan .
```

Choose another report destination:

```bash
harness-baby scan /path/to/repository --output /tmp/report.yaml
```

The command prints a compact summary and writes `<repository>/.harness/report.yaml` by default. Finding failed checks does not make the process fail; exit code `2` is reserved for invocation, path, or report-write errors.

## Report schema

Schema version 1 has five stable top-level fields. Evidence fields may grow as checks improve.

```yaml
schema_version: 1
tool:
  name: harness-baby
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

`Scanner` performs bounded, sorted file discovery, detects stacks, and executes an ordered registry of `Check` implementations. A check receives an immutable `ScanContext` and returns a `CheckResult`; it does not mutate the repository. Adding a stack means adding checks under `src/harness_baby/checks/` and registering them in `built_in_checks()`.

The score policy and YAML reporter are independent modules. YAML output preserves registry order and contains no timestamps, making repeated scans stable when repository and relevant tool availability are unchanged.

`bootstrap.py` owns the generic template and separates deterministic planning from
explicit application. It preflights every path before writing, refuses ownership
ambiguity, and verifies the complete result after application. The maintained
contract and stop conditions live in
[`docs/specs/blank-folder-bootstrap.md`](https://github.com/yamashi128/Harness_Baby/blob/main/docs/specs/blank-folder-bootstrap.md).

## Development

The committed `uv.lock` is the reproducible development environment:

```bash
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python -m build
uv run twine check dist/*
```

Without `uv`, create a Python 3.12 virtual environment and run
`python -m pip install -e '.[dev]'` before invoking the tools directly.

Release maintainers should follow
[`docs/releasing.md`](https://github.com/yamashi128/Harness_Baby/blob/main/docs/releasing.md).

## Roadmap

After the generic bootstrap is proven, likely additions are a novice-friendly
interactive flow, stack-specific templates, safe adoption into existing repositories,
a versioned external plugin discovery contract, configurable check weights, optional
report history, more robust workflow semantics, and support for Node.js, Go, Rust,
Java, Docker, Kubernetes, and Ansible.

Dynamic plugins, application-code generation, automatic remediation, external
command execution, historical reports, remote integrations, and exhaustive secret
scanning are intentionally outside the current scope.
