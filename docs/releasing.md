# Releasing Harness Baby

This document covers the human-reviewed path from a clean checkout to TestPyPI,
PyPI, and eventual public repository visibility. Package publication, tag pushes,
and visibility changes always require explicit approval.

## 1. Prepare the release

Start from a clean feature branch and update `src/harness_baby/__init__.py` to
the intended semantic version. The package metadata reads that value as its
single version source.

Run the complete local gate:

```bash
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run harness-baby scan . --output /tmp/harness-baby-release-report.yaml
uv run python -m build
uv run twine check dist/*
```

Inspect the source archive and wheel under `dist/`. Confirm that the source archive
contains the package, metadata, README, license, tests, and maintained Markdown
documentation, while the wheel contains only runtime package and metadata material.
Install the wheel into a clean Python 3.12 environment. Outside the source checkout,
preview and apply a blank-folder bootstrap, scan the generated repository, and
confirm that a second apply is unchanged.

## 2. Configure Trusted Publishing

Create GitHub environments named `testpypi` and `pypi`; require a reviewer for
the production environment when available. Configure pending Trusted Publishers
with these exact identities:

| Index | Owner | Repository | Workflow | Environment |
| --- | --- | --- | --- | --- |
| TestPyPI | `yamashi128` | `Harness_Baby` | `release.yml` | `testpypi` |
| PyPI | `yamashi128` | `Harness_Baby` | `release.yml` | `pypi` |

No PyPI API token belongs in GitHub secrets. The release workflow requests a
short-lived OIDC credential with job-scoped `id-token: write` permission.

## 3. Verify on TestPyPI

Run the **Release** workflow manually. Manual runs publish to TestPyPI only.
Each package version can be uploaded once, so increment the version before a
retry that needs a new distribution.

Install the candidate in a clean environment, using PyPI for dependencies:

```bash
python3.12 -m venv /tmp/harness-baby-testpypi
/tmp/harness-baby-testpypi/bin/python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  harness-baby
/tmp/harness-baby-testpypi/bin/harness-baby --version
```

Run a representative repository scan and inspect the generated schema version 1
report before approving production publication.

## 4. Publish to PyPI

After TestPyPI verification and explicit approval, create an annotated version
tag matching the package version, such as `v0.1.0`, and push only that tag. A
matching `v*.*.*` tag triggers the production `pypi` environment. The workflow
refuses to publish when the tag and package versions differ.

After publication, verify installation through `pipx`, the CLI version, and a
scan outside the checkout.

## 5. Public repository gate

Closing the release-readiness issue means the software is ready for a public
review; it does not change visibility automatically. Before approving a public
repository, inspect Git history, release archives, workflows, documentation,
license metadata, and secret exposure. Change visibility only after a separate,
explicit approval.
