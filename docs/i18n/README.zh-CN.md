<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**面向 AI 辅助开发的本地优先项目管理工具。**

`pm-skill` 把需求、TODO、分支进展、检查、交接和审计记录放回 Git 仓库里。这样人和 coding agent 都可以从仓库事实恢复上下文，而不是依赖聊天历史。

## 为什么需要它

AI 编码很强，但项目状态很容易散落在对话里。`pm-skill` 的目标是让仓库自己说明当前的工作：现在在哪个分支、有哪些 TODO、需求是什么、检查是否跑过、下一步该做什么。

## 亮点

- 本地优先：项目状态在仓库里。
- 分支感知：需求、TODO 和 changelog 可以跟随分支。
- 人机共读：Markdown 给人看，front matter 给工具读。
- 统一命令入口：CLI、REST、MCP 复用 command envelope。
- 可审计：写命令进入 `.pm-skill/audit/audit-log.jsonl`。

## Quick Start

```bash
pipx install git+https://github.com/AIGRABER/pm-skill.git
```

安装后直接用自然语言告诉 coding agent 你想做什么：

`pm-skill` 的核心不只是恢复上下文，而是给 AI coding 加一个仓库内控制面：恢复状态 -> 讨论不确定需求 -> 提取需求草稿 -> 批准范围 -> 拆 TODO -> 约束上下文 -> 验证验收 -> 审计变更 -> 交接/发布。

```text
用 pm-skill 初始化项目 C:\Users\win\Documents\MyProject，project id 用 my-project，显示名用“My Project”。
```

```text
用 pm-skill 恢复项目控制状态，告诉我当前分支、脏文件、活跃需求、未完成 TODO、风险和下一步安全动作。
```

```text
我还不确定登录改版到底要做什么。先和我讨论，追问澄清问题，把目标、约束、风险和验收标准从对话里提取出来，然后保存成 pm-skill 需求草稿给我确认。
```

```text
用 pm-skill 为“登录流程”创建工作面，然后按仓库默认检查完成实现。
```

```text
用 pm-skill 为“免密码登录”创建需求草稿，把目标、负责人、风险和初始验收标准整理成编码前的范围边界。
```

```text
把这个需求草稿中“魔法链接登录”的部分提升为正式需求，再从正式需求创建 TODO 和验收矩阵。
```

```text
为第一个 TODO 创建工作包，加入相关实现文件和验证文件，用它约束 agent 的工作上下文，然后按验收矩阵验证完成度。
```

你也可以用其他语言提需求；agent 负责把自然语言转换成 `pm-skill` 命令、REST 或 MCP 调用。

## 核心理念

- 仓库文件是事实来源。
- `.pm-skill/` 保存机器可读的控制面状态。
- Markdown 保存需求、TODO、changelog、验收记录和交接文档。
- CLI、REST、MCP 应复用同一个 command envelope。
- 写操作会被审计，长周期 AI coding 工作可以被追溯和复盘。

## 常用命令

| 命令 | 用途 |
| --- | --- |
| `pm-skill show-status --json` | 查看当前分支、脏文件、活跃 TODO、警告和下一步。 |
| `pm-skill recover-project --json` | 恢复项目控制状态和上下文。 |
| `pm-skill create-requirement --title "..." --json` | 从讨论或明确说明中创建需求草稿。 |
| `pm-skill promote-requirement REQ-DRAFT-... --json` | 将需求草稿提升为正式需求。 |
| `pm-skill create-todo-from-source --source-requirement REQ-... --json` | 从正式需求创建可追溯 TODO。 |
| `pm-skill create-acceptance-matrix TODO-... --json` | 为 TODO 生成验收矩阵。 |
| `pm-skill create-work-package TODO-... --json` | 为 TODO 创建聚焦工作包，约束 agent 上下文。 |
| `pm-skill validate-acceptance TODO-... --checks-profile default --json` | 用验收矩阵和检查命令验证完成度。 |
| `pm-skill handover --summary-level standard --json` | 给下一次会话留下交接。 |

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
