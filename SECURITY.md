# Security Policy

`pm-skill` is a local-first project-management tool. It reads Git state and writes repository-managed project metadata. Please treat reports involving data exposure, unsafe file writes, command execution, or credential leakage as security-sensitive.

## Supported Versions

The project is pre-1.0. Security fixes are handled on the default branch until a formal version support policy is published.

## Reporting a Vulnerability

If you find a vulnerability, please do not open a public issue with exploit details.

Use GitHub private vulnerability reporting if it is enabled for the repository. If it is not enabled yet, contact the repository owner through GitHub and share only a high-level summary until a private channel is available.

Please include:

- affected version or commit
- operating system
- reproduction steps
- expected impact
- whether secrets, local files, or command execution are involved

## Sensitive Data Rules

Do not put secrets in:

- `.pm-skill/project-manifest.json`
- `.pm-skill/index/`
- `.pm-skill/audit/audit-log.jsonl`
- `todo/`
- `docs/requirements/`
- `docs/changelog/`
- `docs/handover/`
- `docs/work-packages/`

The default project policy excludes common secret file patterns such as `.env`, `*.pem`, and `*.key`, but contributors should still review diffs before committing.