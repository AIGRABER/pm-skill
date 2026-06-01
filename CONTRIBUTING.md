# Contributing

Thanks for taking an interest in `pm-skill`. The project is still early, so the best contributions are small, well-scoped, and easy to review.

## Development Setup

```bash
git clone https://github.com/AIGRABER/pm-skill.git
cd pm-skill
python -m pip install -e ".[dev]"
pm-skill show-status --json
```

`pm-skill` requires Python 3.11 or newer.

## Before You Change Code

1. Run `pm-skill show-status --json` from the repository root.
2. Check the current branch and active TODOs.
3. Prefer a focused branch for each change.
4. Keep generated artifacts, secrets, and local runtime files out of commits.

## Validation

Run the default project checks before opening a pull request:

```bash
pm-skill run-checks --profile default --json
```

For linting:

```bash
pm-skill run-checks --profile lint --json
```

If you change user-facing commands, data formats, or security boundaries, update the docs and tests in the same pull request.

## Commit Style

This repository prefers conventional commit messages, for example:

```text
feat(pm-skill): add release checklist documentation
fix(pm-skill): preserve branch changelog metadata
chore(docs): refresh GitHub landing page
```

When a change is tied to managed requirements or TODOs, include the relevant IDs in the commit body when practical.

## Pull Request Checklist

- [ ] The change is focused and described clearly.
- [ ] Tests or docs were updated when behavior changed.
- [ ] `pm-skill run-checks --profile default --json` passes.
- [ ] No secrets, tokens, `.env` contents, private keys, or local credentials are included.
- [ ] New adapters use the shared command envelope instead of bypassing `pm_skill.command_router`.

## License

By contributing, you agree that your contributions are licensed under the Apache License 2.0.