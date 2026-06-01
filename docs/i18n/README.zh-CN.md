<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**面向 AI 辅助开发的本地优先项目管理工具。**

`pm-skill` 把需求、TODO、分支进展、检查、交接和审计记录放回 Git 仓库里。这样人和 coding agent 都可以从仓库事实恢复上下文，而不是依赖聊天历史。

## 为什么需要它

AI 编码会话很强，但项目状态很容易散落在对话里。`pm-skill` 的目标是让仓库自己说明当前工作：现在在哪个分支、有哪些 TODO、需求是什么、检查是否跑过、下一步该做什么。

## 亮点

- 本地优先：项目状态在仓库里。
- 分支感知：需求、TODO 和 changelog 可以跟随分支。
- 人机共读：Markdown 给人看，front matter 给工具读。
- 统一命令入口：CLI、REST、MCP 复用 command envelope。
- 可审计：写命令进入 `.pm-skill/audit/audit-log.jsonl`。

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
