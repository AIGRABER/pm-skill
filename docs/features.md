# Features

`pm-skill` is a local-first project-management sidecar for AI-assisted software work. It does not replace Git, GitHub, CI, or issue trackers. It fills the gap between a live coding session and durable project state.

## Local-First Control Plane

The `.pm-skill/` directory stores machine-readable state:

- project identity and repository UID
- latest indexed commit
- file fingerprints
- semantic index manifests
- command audit events
- branch work markers
- exported JSON schemas

Because the control plane lives in the repository, it can be committed, reviewed, diffed, and recovered like normal project state.

## Human-Readable Work Surface

Project-management state is also written as Markdown:

- draft requirements
- approved requirements
- TODO files
- branch changelogs
- acceptance matrices
- work packages
- handover notes

This keeps the system useful even without a UI. Humans can read the files; agents can parse the front matter and structured sections.

## Branch-Aware Project Work

New work is scoped to the current Git branch by default. That means a feature branch can carry its own:

- requirement collection
- TODO directory
- branch changelog
- progress marker
- work packages
- acceptance evidence

When release time comes, branch work can be summarized and prepared for global release notes.

## Command Envelope Runtime

`pm-skill` has a shared command runtime for CLI, REST, and MCP adapters:

1. validate command envelope
2. look up the command spec
3. build run context from Git, manifest, policy, and dirty state
4. run preflight checks
5. execute the command handler
6. write audit events
7. return structured JSON

This keeps adapters from bypassing policy, audit, or Git state checks.

## Context Recovery

`show-status` and `recover-project` are designed for the start of a session:

- current branch and HEAD
- dirty files
- protected branch status
- active TODOs
- requirement counts
- latest handover
- stale index warnings
- next actions

This is especially helpful when an AI coding agent resumes work after a context reset.

## Work Surfaces

`create-work-surface` is a high-level workflow command. It creates a durable place for a task and records the action in the audit log.

Use it when someone says:

- create a work surface
- start a new branch task
- prepare a feature workspace
- create the TODO and requirement for this task

## Acceptance and Verification

The acceptance workflow helps connect source material to implementation evidence:

- create TODOs from source documents
- audit source coverage
- generate acceptance matrices
- validate acceptance readiness
- optionally run check profiles during validation

This keeps generated TODOs from drifting away from their requirements.

## Work Packages

Work packages collect focused context for a TODO:

- implementation context
- verification context
- PRD notes
- package metadata

They are not a replacement for TODOs or requirements. They are a focused context carrier for implementation and review.

## Checks and Policy

`docs/standards/development-policy.yaml` defines local policy:

- protected branches
- branch naming patterns
- commit trailer expectations
- check profiles
- index exclusions
- handover expectations

`run-checks` executes the configured command list for a profile.

## Audit Trail

Write commands append audit events to:

```text
.pm-skill/audit/audit-log.jsonl
```

Events include command name, request ID, actor, session ID, before/after refs, target branch, success state, and details. This gives long-running local work a traceable history.

## Release Preparation

Release commands help answer:

- Which branches still have unfinished work?
- Which branch changelogs should be aggregated?
- Are checks passing?
- Is this release proposal ready to apply?

`prepare-release --json` gives a proposal first. Add `--apply` only when you want to write release changes.

## Non-Goals

`pm-skill` deliberately does not try to be:

- a hosted ALM platform
- a complete GitHub Issues replacement
- a CI/CD orchestrator
- a secrets manager
- a multi-tenant permissions system
- an external vector database

It is a small local coordination layer for repository-native project state.
