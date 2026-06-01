# Quick Start

This guide takes you from a normal Git repository to a `pm-skill` managed project in a few minutes.

## Requirements

- Python 3.11 or newer
- Git
- A local repository you want to manage

Optional but recommended:

- `pipx` for isolated CLI installation
- `pytest` or your own test runner configured through `docs/standards/development-policy.yaml`

## Install

Install from GitHub with `pipx`:

```bash
pipx install git+https://github.com/AIGRABER/pm-skill.git
```

Or install into the current Python environment:

```bash
python -m pip install git+https://github.com/AIGRABER/pm-skill.git
```

Check that the CLI is available:

```bash
pm-skill help
```

## Initialize a New Managed Repository

Run this from the root of your Git repository:

```bash
pm-skill init-project --project-id my-project --display-name "My Project" --json
```

This creates the repository control plane and starter project-management files.

## Onboard an Existing Codebase

If you are pointing `pm-skill` at an existing directory:

```bash
pm-skill --project-path /path/to/repo onboard-project --project-id my-project --json
```

`onboard-project` can initialize Git when needed, create `.pm-skill/`, export schemas, build an initial index, and write onboarding notes.

## Start a Work Session

At the beginning of a session, run:

```bash
pm-skill show-status --json
```

Use this output to answer three questions:

1. Which branch am I on?
2. Is the worktree dirty?
3. What TODO or warning needs attention next?

If you need a fuller recovery view:

```bash
pm-skill recover-project --json
```

For a compact AI-agent context bundle:

```bash
pm-skill get-context --mode turn --json
```

## Create a Work Surface

For a new task, prefer one command:

```bash
pm-skill create-work-surface --title "Add login flow" --json
```

A work surface gives the task a durable home in the repository. It can create or update branch-aware requirement notes, TODO files, branch progress metadata, and audit events.

## Record Progress

Use progress notes while you work:

```bash
pm-skill update-work-surface --progress-note "Login endpoint implemented; next step is regression coverage." --json
```

When a TODO is tied to an approved requirement, record a changelog entry before marking it done:

```bash
pm-skill update-work-surface --todo-status done --changelog-entry "Add login flow project-management support." --json
```

## Run Checks

`pm-skill` reads check commands from `docs/standards/development-policy.yaml`:

```bash
pm-skill run-checks --profile default --json
```

The default profile in this repository runs documentation encoding checks and the unit test suite.

## Refresh the Index

When `show-status` reports `index_stale`, refresh the project-management index:

```bash
pm-skill sync-index --json
pm-skill show-status --json
```

## Prepare a Handover

Before pausing or handing work to another agent:

```bash
pm-skill handover --summary-level standard --next-action "Continue with login regression tests." --json
```

A good handover keeps the next session from rediscovering everything from scratch.

## Prepare a Release

Before a release:

```bash
pm-skill list-work-branches --json
pm-skill prepare-release --json
```

Use `--apply` only when you intentionally want the release proposal written into the global changelog and related release files.
