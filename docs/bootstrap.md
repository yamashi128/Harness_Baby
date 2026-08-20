# Start from an empty folder

The generic bootstrap is for someone who has an idea but does not yet know how to
structure repository context for coding agents. It creates a small, agent-neutral
skeleton and leaves unknown facts as explained TODOs.

## 1. Preview

The default mode never creates the target directory or writes files:

```bash
harness-doctor init my-project
```

Review the seven planned paths. Use a display name when the folder name is not the
right project name:

```bash
harness-doctor init my-project --project-name "My Project"
```

## 2. Create the skeleton

Apply the exact preview explicitly:

```bash
harness-doctor init my-project --project-name "My Project" --apply
cd my-project
```

The command accepts a missing directory, an empty directory, or an empty directory
that already contains `.git`. It never runs `git init` for you.

It creates:

```text
.agent-readiness.yaml
.gitignore
AGENTS.md
README.md
docs/architecture.md
docs/decisions/README.md
docs/work-loop.md
```

## 3. Add only known facts

Start with the TODOs in `AGENTS.md`, `docs/architecture.md`, and
`docs/work-loop.md`. Do not invent a test command, dependency, architecture, or CI
system just to fill a slot. Add each command after the corresponding engineering
control really exists.

Choose a license and initialize version control when appropriate:

```bash
git init
```

Git is not required to edit the skeleton, but the readiness report correctly treats
the absence of repository metadata as unfinished work.

## 4. Observe and adjust

```bash
harness-doctor scan .
```

Read `.harness/report.yaml`, choose one evidenced gap, improve the repository, and
scan again. A freshly generated skeleton is not expected to score 100: it has no
real tests, CI, lockfile, license, or application stack yet.

## Conflict behavior

Running the same apply command again is a no-op when every generated file still
matches. Runtime reports under `.harness/` do not change that result.

The command refuses to proceed when it finds unexpected content, a partial
skeleton, or a human-edited generated file. There is intentionally no `--force`
option. Move to a new empty directory or reconcile the files manually instead of
asking the bootstrap to guess ownership.

## Current boundary

This first template is deliberately generic. It does not create application source,
tests, dependencies, licenses, GitHub Actions, or vendor-specific agent settings.
Stack-specific templates and safe adoption into existing repositories require their
own reviewed contracts.
