<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**面向 AI 輔助開發的本地優先專案管理工具。**

`pm-skill` 將需求、TODO、分支進度、檢查、交接和審計記錄放回 Git 倉庫。人和 coding agent 都可以根據倉庫中的事實恢復上下文，而不是依賴聊天歷史。

## 為什麼需要它

AI 編碼會話很強，但專案狀態很容易散落在對話中。`pm-skill` 讓倉庫自己說明目前工作：在哪個分支、有哪些 TODO、需求是什麼、檢查是否執行過、下一步該做什麼。

## 亮點

- 本地優先：專案狀態保存在倉庫中。
- 分支感知：需求、TODO 和 changelog 可以跟隨分支。
- 人機共讀：Markdown 給人閱讀，front matter 給工具解析。
- 統一命令入口：CLI、REST、MCP 共用 command envelope。
- 可審計：寫入命令會記錄到 `.pm-skill/audit/audit-log.jsonl`。

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
