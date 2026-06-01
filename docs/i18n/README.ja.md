<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**AI 支援開発のためのローカルファーストなプロジェクト管理ツール。**

`pm-skill` は、要件、TODO、ブランチの進捗、チェック、引き継ぎ、監査ログを Git リポジトリ内に保存します。人間も coding agent も、チャット履歴ではなくリポジトリの事実から作業を再開できます。

## なぜ必要か

AI コーディングセッションは強力ですが、プロジェクト状態は会話の中に散らばりがちです。`pm-skill` は、現在のブランチ、TODO、要件、実行済みチェック、次の作業をリポジトリ自身が説明できるようにします。

## 主な特徴

- ローカルファースト: 状態はリポジトリに保存されます。
- ブランチ対応: 要件、TODO、changelog をブランチ単位で扱えます。
- 人間にもツールにも読める Markdown。
- CLI、REST、MCP が同じ command envelope を共有します。
- 書き込み操作は `.pm-skill/audit/audit-log.jsonl` に記録されます。

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
