# Quick Start

This guide takes you from a normal Git repository to a `pm-skill` managed project in a few minutes.

The easiest way to use `pm-skill` is not to memorize every command. Talk to your coding agent in natural language. The agent can translate your request into `pm-skill` CLI, REST, or MCP calls, then summarize the repository-backed result.

The distinctive workflow is a control loop for AI coding:

```text
recover state -> discuss uncertainty -> extract draft requirements -> approve scope -> split TODOs -> constrain context -> verify acceptance -> audit changes -> hand over or release
```

This is what makes `pm-skill` different from simple context-management tools. It does not only remind the next agent what happened. It helps turn messy discussion into reviewable requirements, then gives the agent boundaries, source-of-truth requirements, traceable TODOs, focused work packages, acceptance gates, check profiles, branch changelogs, handovers, and an audit trail.

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

## Use Natural Language First

After installation, open your coding agent in the repository root and say what you want. These prompts are meant to be copied as-is and adapted.

### Initialize a New Managed Repository

```text
Use pm-skill to initialize the project at C:\Users\win\Documents\MyProject. Use project id my-project and display name "My Project".
```

The agent will usually call:

```bash
pm-skill --project-path "C:\Users\win\Documents\MyProject" init-project --project-id my-project --display-name "My Project" --json
```

This creates the repository control plane and starter project-management files in the target project directory.

### Onboard an Existing Codebase

```text
Onboard this existing codebase into pm-skill. If Git or pm-skill metadata is missing, initialize what is needed, then show me the project status.
```

The agent will usually call:

```bash
pm-skill --project-path /path/to/repo onboard-project --project-id my-project --json
```

`onboard-project` can initialize Git when needed, create `.pm-skill/`, export schemas, build an initial index, and write onboarding notes.

### Recover the Control State

```text
Use pm-skill to recover the project control state. Tell me the current branch, dirty state, active requirements, active TODOs, warnings, and recommended next safe action.
```

The agent will usually call:

```bash
pm-skill show-status --json
```

Use this output to answer five control questions:

1. Which branch am I on?
2. Is the worktree dirty?
3. Which requirements and TODOs are active?
4. What warnings could make the next edit unsafe?
5. What is the next safe action?

If you need a fuller recovery view:

```text
Recover the full pm-skill project context before making changes.
```

```bash
pm-skill recover-project --json
```

For a compact AI-agent context bundle:

```text
Get the compact pm-skill context bundle for this turn.
```

```bash
pm-skill get-context --mode turn --json
```

### Define Scope With a Draft Requirement

Use this before coding, while the scope is still being shaped. The user does not need to know exactly what they want yet; the agent can ask questions, extract requirements from the discussion, and then save a draft for review.

```text
I am not sure what the login redesign should include. Discuss it with me first: ask clarifying questions, separate goals from implementation guesses, identify risks and acceptance criteria, then save the result as a pm-skill draft requirement for review.
```

The agent will usually discuss first, then call `create-requirement` once the draft is concrete enough:

```bash
pm-skill create-requirement --title "Login redesign" --owner product --acceptance "Users can complete the primary login path without regressions." --body "Draft extracted from product discussion." --json
```

If the scope is already clear, you can be more direct:

```text
Create a pm-skill draft requirement for "Passwordless login". Capture the problem, target users, owners, dependencies, risks, and initial acceptance criteria.
```

The agent will usually call:

```bash
pm-skill create-requirement --title "Passwordless login" --owner product --acceptance "Users can request a magic link from the login page." --acceptance "Magic links expire and cannot be reused." --json
```

Draft requirements live under `docs/requirements/drafts/` and can evolve before the team commits to implementation. They turn a vague instruction into a reviewable boundary.

### Approve Formal Requirements

Use this when part of a draft is ready to become the implementation contract:

```text
Promote the passwordless-login draft into a formal requirement slice for magic-link sign-in. Include acceptance criteria for email delivery, token expiry, replay protection, and regression tests.
```

The agent will usually call one of:

```bash
pm-skill promote-requirement REQ-DRAFT-2026-0001 --json
pm-skill promote-requirement-slice REQ-DRAFT-2026-0001 --title "Magic-link sign-in" --acceptance "Magic links expire after 15 minutes." --acceptance "A used magic link cannot be replayed." --json
```

Formal requirements live under `docs/requirements/final/`. This lets a broad idea stay open while a buildable slice becomes approved work. Agents should implement against approved scope, not against a loose chat instruction.

### Create TODOs From Source

Use this when you want implementation tasks to stay traceable to a requirement or source document:

```text
Create TODOs from the approved magic-link requirement. Keep each TODO linked to the requirement and point out any source coverage gaps.
```

The agent will usually call:

```bash
pm-skill create-todo-from-source --source-requirement REQ-2026-0001 --title "Implement magic-link token flow" --priority P1 --json
```

For a source document instead of a requirement:

```text
Create TODOs from docs/specs/auth.md and audit whether the TODO covers the source material.
```

```bash
pm-skill create-todo-from-source --source-path docs/specs/auth.md --title "Implement auth spec" --priority P1 --json
```

### Add Acceptance Gates

Use this before implementation so the definition of done is explicit and verifiable:

```text
Generate an acceptance matrix for the magic-link TODO. Show me which acceptance items, files, checks, and evidence are still missing.
```

The agent will usually call:

```bash
pm-skill create-acceptance-matrix TODO-2026-0001 --json
```

Acceptance matrices live under `docs/acceptance/`. They help prevent TODOs from drifting away from requirements and give the agent a clear "not done yet" signal.

### Constrain Agent Context With a Work Package

Use this when the agent needs a focused context bundle instead of wandering through the whole repository:

```text
Create a work package for TODO-2026-0001. Add src/auth/magic_links.py as implementation context and tests/test_auth_magic_links.py as verification context.
```

The agent will usually call:

```bash
pm-skill create-work-package TODO-2026-0001 --json
pm-skill add-work-package-context TODO-2026-0001 --action implementation --file src/auth/magic_links.py --reason "Token creation and validation live here." --json
pm-skill add-work-package-context TODO-2026-0001 --action verification --file tests/test_auth_magic_links.py --reason "Regression coverage for magic-link behavior." --json
```

Work packages live under `docs/work-packages/` and collect PRD notes, implementation context, verification context, and package metadata. They make the next coding turn smaller, more inspectable, and easier to review.

### Create a One-Step Work Surface

```text
Create a pm-skill work surface for "Add login flow". Keep the TODO, requirement notes, branch marker, and audit trail aligned with the current branch.
```

The agent will usually call:

```bash
pm-skill create-work-surface --title "Add login flow" --json
```

A work surface gives the task a durable home in the repository. It can create or update branch-aware requirement notes, TODO files, branch progress metadata, and audit events.

This is the fast path when you do not need to separately shape draft requirements, promote formal requirements, and split TODOs.

### Record Progress

```text
Record this pm-skill progress note: Login endpoint implemented; next step is regression coverage.
```

```bash
pm-skill update-work-surface --progress-note "Login endpoint implemented; next step is regression coverage." --json
```

When a TODO is tied to an approved requirement, record a changelog entry before marking it done:

```text
Mark the active pm-skill TODO done and add this changelog entry: Add login flow project-management support.
```

```bash
pm-skill update-work-surface --todo-status done --changelog-entry "Add login flow project-management support." --json
```

### Validate Acceptance and Run Checks

Before marking a TODO done, use acceptance and checks as the completion gate:

```text
Validate the acceptance matrix for TODO-2026-0001 and run the default checks. If anything is missing, summarize the gap instead of marking the TODO done.
```

The agent will usually call:

```bash
pm-skill validate-acceptance TODO-2026-0001 --checks-profile default --json
```

If you only want the configured check profile:

`pm-skill` reads check commands from `docs/standards/development-policy.yaml`:

```text
Run the default pm-skill checks and summarize any failures with file paths.
```

```bash
pm-skill run-checks --profile default --json
```

The default profile in this repository runs documentation encoding checks and the unit test suite.

### Refresh the Index

When `show-status` reports `index_stale`, refresh the project-management index:

```text
pm-skill says the index is stale. Refresh it, then show status again.
```

```bash
pm-skill sync-index --json
pm-skill show-status --json
```

### Prepare a Handover

Before pausing or handing work to another agent:

```text
Write a pm-skill handover for the next session. Summary level standard. Next action: Continue with login regression tests.
```

```bash
pm-skill handover --summary-level standard --next-action "Continue with login regression tests." --json
```

A good handover keeps the next session from rediscovering everything from scratch.

### Prepare a Release

Before a release:

```text
Use pm-skill to list unfinished branch work and prepare a release proposal. Do not apply it yet.
```

```bash
pm-skill list-work-branches --json
pm-skill prepare-release --json
```

Use `--apply` only when you intentionally want the release proposal written into the global changelog and related release files.

## Multilingual Prompts

You can speak to the agent in the language you normally use. `pm-skill` stores repository facts; the natural-language layer is for you and the agent.

```text
用 pm-skill 恢复这个项目的控制状态，告诉我当前分支、脏文件、活跃需求、未完成 TODO、风险和下一步安全动作。
```

```text
用 pm-skill 为“登录流程”创建需求草稿、正式需求、TODO 和验收矩阵，再按默认检查验证完成度。
```

```text
Usa pm-skill para recuperar el estado de control del proyecto y dime la rama actual, requisitos activos, TODOs abiertos, riesgos y siguiente acción segura.
```

```text
pm-skill でこのプロジェクトの control state を復元し、現在のブランチ、アクティブな要件、未完了 TODO、警告、次の安全なアクションを教えてください。
```

```text
pm-skill로 프로젝트 control state를 복구하고 현재 브랜치, 활성 요구사항, 남은 TODO, 경고, 다음 안전한 작업을 알려줘.
```

```text
Usa o pm-skill para transformar "Adicionar fluxo de login" em requisito, TODO, matriz de aceitação e checks padrão antes de marcar como concluído.
```

The agent should keep generated requirements, TODOs, changelogs, and handovers in the language that is most useful for the project team, while preserving command names, file paths, IDs, and JSON fields exactly.
