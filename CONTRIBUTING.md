# Contributing to Harness Baby

Harness Baby is experimental alpha software. Contributions are welcome, but every
change must preserve its deterministic, offline, evidence-first, and side-effect-free
scan behavior.

## Branch strategy

Harness Baby uses a trunk-based workflow:

- `main` is the only long-lived branch and must remain releasable.
- Create a short-lived branch named `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, or
  `chore/<topic>`.
- External contributors should work from a fork and open a pull request to `main`.
- Do not push directly to `main`.
- Keep each pull request focused on one reviewable outcome.

## Pull requests

Before merge, a pull request must:

- pass the required `quality` check;
- be up to date with `main`;
- have all review conversations resolved;
- document user-facing behavior when it changes; and
- include deterministic repository-scenario tests for new or changed checks.

Pull requests are squash-merged. The short-lived branch is deleted after merge.
While the repository has one maintainer, an approving review is not required; the
pull request, required CI, and resolved-conversation gates still apply.

## Verification

Run the locked verification suite before requesting review:

```bash
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python -m build
uv run twine check dist/*
```

Do not add credentials, secret values, machine-local artifacts, or generated reports
to a commit.

## Releases

Only a maintainer may create a release tag. Release tags use `vMAJOR.MINOR.PATCH`,
must point to a verified commit on `main`, and must never be moved, force-pushed, or
deleted. Pushing a release tag publishes to PyPI through Trusted Publishing, so follow
[`docs/releasing.md`](docs/releasing.md) and obtain explicit release approval first.

Coding agents must also follow [`AGENTS.md`](AGENTS.md).
