# pm-skill

Local-first project management for AI-assisted development.

`pm-skill` keeps project state where engineers and coding agents can both trust it: inside the Git repository. It gives Codex and other agents a small command layer for recovering context, managing TODOs and requirements, recording branch progress, running checks, preparing handovers, and writing an auditable project trail.

It is designed for the messy middle of real work: long-running branches, interrupted sessions, half-finished TODOs, local validation, release notes, and the moment when a new agent needs to understand what happened before touching code.

## Why this exists

AI coding sessions are powerful, but project state often leaks into chat history. That makes handoff fragile. `pm-skill` moves the important facts back into the repository:

- what the current branch is doing
- which TODOs are ready, in progress, blocked, or done
- which requirements a task belongs to
- what changed in a branch
- which checks were run
- what the next agent should do
- which command wrote which project-management artifact

The result is a repo that can explain itself.

## Highlights

- **Local-first control plane**: stores machine-readable state under `.pm-skill/`.
- **Human-readable work surface**: keeps requirements, TODOs, changelogs, acceptance matrices, and handovers in Markdown.
- **Branch-aware workflow**: scopes requirements, TODOs, and changelog entries to the current Git branch.
- **Command envelope runtime**: gives CLI, REST, and MCP adapters one shared command path with policy checks and audit events.
- **Context recovery**: starts every session with `show-status` or `recover-project` instead of guessing from chat history.
- **Work surfaces**: creates a branch-aware requirement, TODO, and progress marker in one command.
- **Validation hooks**: runs repository-defined check profiles from `docs/standards/development-policy.yaml`.
- **Release preparation**: aggregates branch changelogs and warns about unfinished branch work.
- **Safety defaults**: avoids storing secrets in project-management artifacts and records write commands in `.pm-skill/audit/audit-log.jsonl`.

## Quick Start

### 1. Install from the GitHub repository

```bash
pipx install git+https://github.com/AIGRABER/pm-skill.git
```

Or install into your active Python environment:

```bash
python -m pip install git+https://github.com/AIGRABER/pm-skill.git
```

`pm-skill` requires Python 3.11 or newer.

### 2. Initialize a repository

From the root of a Git repository:

```bash
pm-skill init-project --project-id my-project --display-name "My Project" --json
```

For an existing codebase that you want to onboard:

```bash
pm-skill --project-path /path/to/repo onboard-project --project-id my-project --json
```

### 3. Start every session by reading the state

```bash
pm-skill show-status --json
```

If you need more context:

```bash
pm-skill recover-project --json
```

### 4. Create a new work surface

```bash
pm-skill create-work-surface --title "Add login flow" --json
```

This prepares a branch-aware work surface: requirement notes, TODO, branch marker, and audit trail.

### 5. Record progress and run checks

```bash
pm-skill update-work-surface --progress-note "Login endpoint is implemented; tests are next." --json
pm-skill run-checks --profile default --json
```

### 6. Leave a handover before pausing

```bash
pm-skill handover --summary-level standard --next-action "Continue with login regression tests." --json
```

## What pm-skill writes

```text
.pm-skill/
  project-manifest.json          machine-readable project identity and index state
  audit/audit-log.jsonl          command audit event stream
  index/                         file fingerprints and summary manifests
  branches/                      branch work markers

docs/
  requirements/drafts/           draft requirement collections by branch
  requirements/final/            approved requirement collections by branch
  changelog/                     branch changelogs
  handover/                      cross-session handover notes
  acceptance/                    acceptance matrices
  work-packages/                 focused implementation and verification context
  standards/development-policy.yaml

todo/
  <branch>/                      branch-scoped TODO files
```

The repository remains the source of truth. You can read the Markdown files directly, but write operations should go through `pm-skill` so policy checks and audit records stay consistent.

## Common Commands

| Command | Use it when you want to |
| --- | --- |
| `pm-skill show-status --json` | See branch, dirty state, active TODOs, warnings, and next actions. |
| `pm-skill recover-project --json` | Reconstruct project context at the start of a session. |
| `pm-skill get-context --mode turn --json` | Get a compact, low-noise context bundle for an agent turn. |
| `pm-skill create-work-surface --title "..." --json` | Create branch-aware requirement/TODO/progress scaffolding. |
| `pm-skill update-work-surface --progress-note "..." --json` | Record progress, TODO state, and branch changelog entries. |
| `pm-skill list-work-branches --json` | Inspect unfinished branch work. |
| `pm-skill create-todo-from-source --title "..." --source-path docs/spec.md --json` | Create a TODO and audit that it covers the source material. |
| `pm-skill create-acceptance-matrix --todo-id TODO-... --json` | Generate a coverage-oriented acceptance matrix for a TODO. |
| `pm-skill validate-acceptance --todo-id TODO-... --json` | Validate an acceptance matrix and optionally run checks. |
| `pm-skill run-checks --profile default --json` | Run the repository-defined validation profile. |
| `pm-skill sync-index --json` | Refresh file fingerprints and project index metadata. |
| `pm-skill prepare-release --json` | Prepare a release proposal from branch work and checks. |
| `pm-skill handover --summary-level standard --json` | Write a handover document for the next session. |
| `pm-skill query-audit --limit 20 --json` | Inspect recent command audit events. |

## Architecture

`pm-skill` is intentionally small:

```text
CLI / REST / MCP
       |
       v
command envelope validation
       |
       v
command_router.CommandSpec
       |
       v
runtime preflight + audit
       |
       v
commands.py handlers
       |
       v
repository files
```

The important rule is that adapters should not call command internals directly. They should go through the shared command envelope so policy, audit, and Git state checks are not skipped.

## Safety Model

`pm-skill` is local-first and repository-scoped. It does not try to replace GitHub Issues, pull requests, CI, or a hosted project-management product. Instead, it provides a durable local coordination layer that works well with those tools.

By default, project policy lives in:

```text
docs/standards/development-policy.yaml
```

That policy can define protected branches, branch naming, check profiles, index exclusions, changelog rules, and handover expectations.

Do not put tokens, API keys, `.env` contents, private keys, or credentials into TODOs, requirements, changelogs, handovers, or index files.

## Documentation

- [Quick Start](docs/quick-start.md)
- [Features](docs/features.md)

## Project Status

Current package version: `0.1.0`.

`pm-skill` is early alpha software. The command surface is usable, but data formats and workflow commands may still evolve before a 1.0 release.

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).
