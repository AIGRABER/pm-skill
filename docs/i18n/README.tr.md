<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**Yapay zeka destekli geliştirme için yerel öncelikli proje yönetimi.**

`pm-skill`, gereksinimleri, TODO kayıtlarını, dal ilerlemesini, kontrolleri, devir notlarını ve denetim izlerini Git deposunda tutar. Böylece insanlar ve coding agentlar, sohbet geçmişine değil depodaki gerçeklere bakarak devam edebilir.

## Neden var

AI kodlama oturumları güçlüdür, fakat proje durumu konuşmaların içinde dağılabilir. `pm-skill`, hangi dalda çalışıldığını, hangi TODOların bulunduğunu, hangi kontrollerin koştuğunu ve sıradaki adımı deponun açıklayabilmesini sağlar.

## Özellikler

- Yerel öncelikli: durum depoda saklanır.
- Dal farkındalığı: gereksinimler, TODOlar ve changeloglar dal bazında yönetilir.
- İnsan ve araçlar için okunabilir Markdown.
- CLI, REST ve MCP aynı command envelope kullanır.
- Yazma komutları `.pm-skill/audit/audit-log.jsonl` içine kaydedilir.

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
