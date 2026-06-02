<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**面向 AI 輔助開發的本地優先專案管理工具。**

`pm-skill` 將需求、TODO、分支進度、檢查、交接和審計記錄放回 Git 倉庫。人和 coding agent 都可以根據倉庫中的事實恢復上下文，而不是依賴聊天歷史。

## 為什麼需要它

AI 編碼很強，但專案狀態很容易散落在對話中。`pm-skill` 讓倉庫自己說明目前工作：在哪個分支、有哪些 TODO、需求是什麼、檢查是否執行過、下一步該做什麼。

## 亮點

- 本地優先：專案狀態保存在倉庫中。
- 分支感知：需求、TODO 和 changelog 可以跟隨分支。
- 人機共讀：Markdown 給人閱讀，front matter 給工具解析。
- 統一命令入口：CLI、REST、MCP 共用 command envelope。
- 可審計：寫入命令會記錄到 `.pm-skill/audit/audit-log.jsonl`。

## Quick Start

```bash
pipx install git+https://github.com/AIGRABER/pm-skill.git
```

安裝後直接用自然語言告訴 coding agent 你想做什麼：

`pm-skill` 的核心不只是恢復上下文，而是給 AI coding 加一個倉庫內控制面：恢復狀態 -> 討論不確定需求 -> 提取需求草稿 -> 批准範圍 -> 拆 TODO -> 約束上下文 -> 驗證驗收 -> 審計變更 -> 交接/發布。

```text
用 pm-skill 初始化專案 C:\Users\win\Documents\MyProject，project id 用 my-project，顯示名稱用「My Project」。
```

```text
用 pm-skill 恢復專案控制狀態，告訴我目前分支、髒檔案、活躍需求、未完成 TODO、風險和下一步安全動作。
```

```text
我還不確定登入改版到底要做什麼。先和我討論，追問澄清問題，把目標、約束、風險和驗收標準從對話裡提取出來，然後保存成 pm-skill 需求草稿給我確認。
```

```text
用 pm-skill 為「登入流程」建立工作面，然後依照倉庫預設檢查完成實作。
```

```text
用 pm-skill 為「免密碼登入」建立需求草稿，把目標、負責人、風險和初始驗收標準整理成編碼前的範圍邊界。
```

```text
把這個需求草稿中「魔法連結登入」的部分提升為正式需求，再從正式需求建立 TODO 和驗收矩陣。
```

```text
為第一個 TODO 建立工作包，加入相關實作檔案和驗證檔案，用它約束 agent 的工作上下文，然後依照驗收矩陣驗證完成度。
```

你也可以用其他語言提出需求；agent 會把自然語言轉成 `pm-skill` 命令、REST 或 MCP 呼叫。

## 核心理念

- 倉庫檔案是事實來源。
- `.pm-skill/` 保存機器可讀的控制面狀態。
- Markdown 保存需求、TODO、changelog、驗收記錄和交接文件。
- CLI、REST、MCP 應共用同一個 command envelope。
- 寫入操作會被審計，長週期 AI coding 工作可以被追溯和復盤。

## 常用命令

| 命令 | 用途 |
| --- | --- |
| `pm-skill show-status --json` | 查看目前分支、髒檔案、活躍 TODO、警告和下一步。 |
| `pm-skill recover-project --json` | 恢復專案控制狀態和上下文。 |
| `pm-skill create-requirement --title "..." --json` | 從討論或明確說明中建立需求草稿。 |
| `pm-skill promote-requirement REQ-DRAFT-... --json` | 將需求草稿提升為正式需求。 |
| `pm-skill create-todo-from-source --source-requirement REQ-... --json` | 從正式需求建立可追溯 TODO。 |
| `pm-skill create-acceptance-matrix TODO-... --json` | 為 TODO 生成驗收矩陣。 |
| `pm-skill create-work-package TODO-... --json` | 為 TODO 建立聚焦工作包，約束 agent 上下文。 |
| `pm-skill validate-acceptance TODO-... --checks-profile default --json` | 用驗收矩陣和檢查命令驗證完成度。 |
| `pm-skill handover --summary-level standard --json` | 給下一次會話留下交接。 |

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
