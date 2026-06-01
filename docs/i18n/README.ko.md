<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**AI 보조 개발을 위한 로컬 우선 프로젝트 관리 도구.**

`pm-skill`은 요구사항, TODO, 브랜치 진행 상황, 검사, 인수인계, 감사 기록을 Git 저장소 안에 둡니다. 사람과 coding agent 모두 채팅 기록이 아니라 저장소의 사실을 기반으로 작업을 이어갈 수 있습니다.

## 왜 필요한가

AI 코딩 세션은 강력하지만 프로젝트 상태는 대화 속에 흩어지기 쉽습니다. `pm-skill`은 현재 브랜치, TODO, 요구사항, 실행된 검사, 다음 작업을 저장소가 직접 설명할 수 있게 합니다.

## 주요 기능

- 로컬 우선: 프로젝트 상태를 저장소에 보관합니다.
- 브랜치 인식: 요구사항, TODO, changelog를 브랜치별로 관리합니다.
- 사람과 도구가 함께 읽을 수 있는 Markdown.
- CLI, REST, MCP가 같은 command envelope를 사용합니다.
- 쓰기 명령은 `.pm-skill/audit/audit-log.jsonl`에 기록됩니다.

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
