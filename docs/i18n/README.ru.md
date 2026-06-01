<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**Локальное управление проектом для разработки с AI-помощниками.**

`pm-skill` хранит требования, TODO, прогресс веток, проверки, handover-документы и аудит прямо в Git-репозитории. Люди и coding agents могут продолжать работу по фактам из репозитория, а не по истории чата.

## Зачем это нужно

AI-сессии разработки сильны, но состояние проекта часто остается в диалогах. `pm-skill` помогает репозиторию самому отвечать: какая ветка активна, какие TODO существуют, какие требования важны, какие проверки запускались и что делать дальше.

## Возможности

- Local-first: состояние проекта хранится в репозитории.
- Поддержка веток: требования, TODO и changelog могут быть привязаны к ветке.
- Markdown, понятный людям и инструментам.
- CLI, REST и MCP используют общий command envelope.
- Команды записи попадают в `.pm-skill/audit/audit-log.jsonl`.

## Quick Start

```bash
pipx install git+https://github.com/AIGRABER/pm-skill.git
pm-skill init-project --project-id my-project --display-name "My Project" --json
pm-skill show-status --json
pm-skill create-work-surface --title "Add login flow" --json
pm-skill run-checks --profile default --json
```

## Core Ideas

- Repository files are the source of truth.
- `.pm-skill/` stores machine-readable control-plane state.
- Markdown files store requirements, TODOs, changelogs, acceptance notes, and handovers.
- CLI, REST, and MCP adapters should use the same command envelope.
- Write operations are audited so long-running work can be reconstructed.

## Useful Commands

| Command | Purpose |
| --- | --- |
| `pm-skill show-status --json` | Inspect the current project state. |
| `pm-skill recover-project --json` | Reconstruct project context. |
| `pm-skill create-work-surface --title "..." --json` | Start branch-aware work. |
| `pm-skill update-work-surface --progress-note "..." --json` | Record progress. |
| `pm-skill run-checks --profile default --json` | Run configured checks. |
| `pm-skill handover --summary-level standard --json` | Leave a handover for the next session. |

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
