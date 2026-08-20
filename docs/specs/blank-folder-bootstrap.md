# Blank-folder bootstrap specification

## Product outcome

A person who does not yet know harness engineering can start in an empty directory,
preview a small agent-neutral repository harness, create it explicitly, and then use
the existing deterministic scanner to see what real engineering controls are still
missing.

The bootstrap does not claim that a repository is ready for autonomous work. It
creates the durable context and feedback slots that make readiness possible; the
scanner remains the source of evidence.

## User loop

```text
empty directory
  -> preview deterministic skeleton
  -> explicitly apply it
  -> fill truthful project context and verification commands
  -> scan readiness
  -> add real tests, CI, locks, and other controls
  -> scan again until the chosen readiness target is met
```

This applies harness engineering by establishing context, permissions, persistent
state, verification slots, and guardrails. It applies loop engineering by making the
goal, action, observation, adjustment, and stop conditions durable and inspectable.

## CLI contract

```bash
harness-baby init [PATH] [--project-name NAME] [--apply]
```

- `PATH` defaults to the current directory.
- `--project-name` defaults to the target directory name.
- Without `--apply`, the command only prints the plan.
- `--apply` is the only mode that creates the skeleton.
- A missing target directory may be created.
- An existing target must be empty, with `.git` as the only allowed pre-existing
  entry.
- Reapplying an identical, complete skeleton succeeds without rewriting files.
- Known runtime state under `.harness/` is ignored during an identical reapply.
- Partial, modified, or unexpected content is a conflict. There is no force flag.
- Errors use exit code 2 and do not disclose file contents.

The public product name is Harness Baby, the PyPI distribution and CLI command are
`harness-baby`, and the Python package is `harness_baby`.

## Generated skeleton

The generic template creates exactly these tracked files:

```text
.agent-readiness.yaml
.gitignore
AGENTS.md
README.md
docs/architecture.md
docs/decisions/README.md
docs/work-loop.md
```

The files provide:

- a short agent entry point and repository contract;
- a human entry point and onboarding checklist;
- an explicit statement that no architecture was inferred;
- a lightweight decision-record location;
- a persistent goal/action/observation/adjustment loop;
- a deterministic template manifest;
- an ignore rule for generated readiness reports.

Unknown facts are represented as clear `TODO` items. The template never invents a
stack, dependency manager, command, test, CI system, license, or architecture.

## Safety invariants

1. `scan` remains read-only except for its requested report artifact.
2. Preview mode performs no writes, including directory creation.
3. Apply performs no network requests and executes no external commands.
4. No existing path is overwritten, removed, or edited. Root `.git` and `.harness`
   runtime state may coexist with the skeleton but is never traversed or changed.
5. All conflicts are discovered before the first intended write.
6. A failed write attempts to remove only paths created by that invocation.
7. Generated content has no timestamp, random identifier, absolute path, or machine
   specific value.
8. The target path and every generated relative path remain inside the target.
9. Reapplying identical content does not change file modification times.

## Stop conditions

Bootstrap implementation is complete when:

- preview, apply, missing-directory, empty-directory, and `.git`-only scenarios pass;
- unexpected, partial, and modified-directory scenarios fail without overwrites;
- a second identical apply is a no-op;
- the generated repository can be scanned and produces schema version 1;
- tests, lint, formatting, type checks, package build, and distribution checks pass;
- user-facing behavior and the changed mutation boundary are documented.

## Non-goals for the first bootstrap

- adding application source code;
- selecting or installing a language runtime;
- running `git init`;
- generating a license without a user choice;
- inventing test, lint, build, deployment, or CI commands;
- modifying an existing repository;
- interactive prompts or agent-specific configuration;
- stack-specific templates;
- automatically fixing scanner findings;
- claiming that the generated skeleton is production-ready.

## Planned extensions

After the generic loop is proven, later versions may add an interactive novice flow,
stack-specific templates, safe adoption into existing repositories, and CI templates.
Each extension must preserve preview-first behavior and evidence honesty.
