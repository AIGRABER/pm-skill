<div align="center">

# pm-skill

**Local-first project management for AI-assisted development.**

Keep requirements, TODOs, branch progress, checks, handovers, and audit trails inside the Git repository, so humans and coding agents can resume work without guessing from chat history.

<p><a href="README.md">English</a> | <a href="docs/i18n/README.zh-CN.md">简体中文</a> | <a href="docs/i18n/README.zh-TW.md">繁體中文</a> | <a href="docs/i18n/README.ja.md">日本語</a> | <a href="docs/i18n/README.ko.md">한국어</a> | <a href="docs/i18n/README.es.md">Español</a> | <a href="docs/i18n/README.tr.md">Türkçe</a> | <a href="docs/i18n/README.ru.md">Русский</a></p>

</div>


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

`pm-skill` is most useful when you talk to your coding agent in plain language and let the agent call the CLI, REST, or MCP adapter for you. It is not only a context snapshot tool. It gives AI coding work a repository-native control plane:

```text
recover state -> discuss uncertainty -> extract draft requirements -> approve scope -> split TODOs -> constrain context -> verify acceptance -> audit changes -> hand over or release
```

That control loop keeps agents from guessing what matters, drifting beyond the agreed scope, losing progress between sessions, or marking work done without evidence.

### 1. Install from GitHub

```bash
pipx install git+https://github.com/AIGRABER/pm-skill.git
```

Or install into your active Python environment:

```bash
python -m pip install git+https://github.com/AIGRABER/pm-skill.git
```

`pm-skill` requires Python 3.11 or newer.

### 2. Tell your agent what you want

Use natural language. The agent should translate your request into audited `pm-skill` operations and show you the important result.

Set up the repository:

```text
Use pm-skill to initialize the project at C:\Users\win\Documents\MyProject. Use project id my-project and display name "My Project".
```

For an existing codebase:

```text
Onboard this existing repo into pm-skill, then show me the current project status.
```

At the start of each session:

```text
Use pm-skill to recover the project control state. Tell me the current branch, dirty files, active requirements, active TODOs, warnings, and the next safe action.
```

When the user is not sure what they want yet:

```text
Discuss the login redesign with me first. Ask clarifying questions, identify the actual requirements from the conversation, then save them as a pm-skill draft requirement for review.
```

Define the boundary before coding:

```text
Create a pm-skill draft requirement for "Passwordless login". Capture the goal, owners, dependencies, risks, and initial acceptance criteria.
```

Approve only the part that is ready to build:

```text
Promote the passwordless-login draft into a formal requirement slice for magic-link sign-in. Include acceptance criteria for email delivery, token expiry, replay protection, and regression tests.
```

Turn the approved scope into controlled work:

```text
Create TODOs from the approved magic-link requirement, generate an acceptance matrix for each TODO, and show me the coverage gaps before implementation starts.
```

Limit the agent's working context:

```text
Create a work package for the first TODO. Add the relevant auth files as implementation context and the login tests as verification context.
```

While working:

```text
Record this progress in pm-skill: the login endpoint is implemented and regression tests are next.
Run the default checks afterwards.
```

Before marking work done:

```text
Validate the acceptance matrix for this TODO, run the default checks, and only then mark it done with a branch changelog entry.
```

Before pausing:

```text
Write a pm-skill handover. The next action is to continue with login regression tests.
```

### 3. Use any language you work in

Natural-language instructions do not need to be English. For example:

```text
用 pm-skill 恢复这个项目的控制状态，告诉我当前分支、脏文件、活跃需求、未完成 TODO、风险和下一步安全动作。
```

```text
Usa pm-skill para recuperar el estado de control del proyecto y dime la rama actual, requisitos activos, TODOs abiertos, riesgos y siguiente acción segura.
```

The underlying project files stay in the repository, and write operations are still audited under `.pm-skill/audit/audit-log.jsonl`.

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
| `pm-skill create-requirement --title "..." --json` | Capture a draft requirement before implementation. |
| `pm-skill promote-requirement REQ-DRAFT-... --json` | Promote a draft requirement into approved work. |
| `pm-skill promote-requirement-slice REQ-DRAFT-... --title "..." --acceptance "..." --json` | Approve only the buildable slice of a broader draft. |
| `pm-skill create-work-surface --title "..." --json` | Create branch-aware requirement/TODO/progress scaffolding. |
| `pm-skill update-work-surface --progress-note "..." --json` | Record progress, TODO state, and branch changelog entries. |
| `pm-skill list-work-branches --json` | Inspect unfinished branch work. |
| `pm-skill create-todo-from-source --title "..." --source-path docs/spec.md --json` | Create a TODO and audit that it covers the source material. |
| `pm-skill create-acceptance-matrix --todo-id TODO-... --json` | Generate a coverage-oriented acceptance matrix for a TODO. |
| `pm-skill validate-acceptance --todo-id TODO-... --json` | Validate an acceptance matrix and optionally run checks. |
| `pm-skill create-work-package TODO-... --json` | Build a focused implementation and verification context bundle for a TODO. |
| `pm-skill add-work-package-context TODO-... --action implementation --file src/app.py --reason "..." --json` | Add concrete files to a TODO work package. |
| `pm-skill run-checks --profile default --json` | Run the repository-defined validation profile. |
| `pm-skill sync-index --json` | Refresh file fingerprints and project index metadata. |
| `pm-skill prepare-release --json` | Prepare a release proposal from branch work and checks. |
| `pm-skill handover --summary-level standard --json` | Write a handover document for the next session. |
| `pm-skill query-audit --limit 20 --json` | Inspect recent command audit events. |

## Architecture

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

Adapters should go through the shared command envelope so policy, audit, and Git state checks are not skipped.

## Safety Model

`pm-skill` is local-first and repository-scoped. It does not try to replace GitHub Issues, pull requests, CI, or a hosted project-management product. Instead, it provides a durable local coordination layer that works well with those tools.

Do not put tokens, API keys, `.env` contents, private keys, or credentials into TODOs, requirements, changelogs, handovers, or index files.

## Documentation

- [Quick Start](docs/quick-start.md)
- [Features](docs/features.md)

## Project Status

Current package version: `0.1.0`.

`pm-skill` is early alpha software. The command surface is usable, but data formats and workflow commands may still evolve before a 1.0 release.

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).
