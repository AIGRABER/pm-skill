<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**Gestión de proyectos local-first para desarrollo asistido por IA.**

`pm-skill` guarda requisitos, TODOs, progreso de ramas, verificaciones, handovers y registros de auditoría dentro del repositorio Git. Así, personas y coding agents pueden retomar el trabajo desde hechos versionados, no desde el historial del chat.

## Por qué existe

Las sesiones de programación con IA son poderosas, pero el estado del proyecto suele quedar disperso en conversaciones. `pm-skill` hace que el repositorio pueda explicar en qué rama estás, qué TODOs existen, qué requisitos importan, qué checks corrieron y cuál es el siguiente paso.

## Características

- Local-first: el estado vive en el repositorio.
- Consciente de ramas: requisitos, TODOs y changelogs por rama.
- Markdown legible para humanos y herramientas.
- CLI, REST y MCP comparten el mismo command envelope.
- Las escrituras quedan auditadas en `.pm-skill/audit/audit-log.jsonl`.

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
