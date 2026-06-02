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
```

インストール後は、coding agent に自然言語で依頼できます。

`pm-skill` の価値はコンテキスト復元だけではありません。AI coding にリポジトリ内の control plane を与えます: recover state -> discuss uncertainty -> extract draft requirements -> approve scope -> split TODOs -> constrain context -> verify acceptance -> audit changes -> handover/release。

```text
pm-skill で C:\Users\win\Documents\MyProject のプロジェクトを初期化してください。project id は my-project、表示名は "My Project" にしてください。
```

```text
pm-skill でプロジェクトの control state を復元し、現在のブランチ、変更済みファイル、アクティブな要件、未完了 TODO、リスク、次の安全なアクションを教えてください。
```

```text
ログイン改修に何を含めるべきかまだ分かりません。まず私と議論し、確認質問をして、会話から目的、制約、リスク、受け入れ条件を抽出し、pm-skill のドラフト要件として保存してください。
```

```text
pm-skill で「ログインフロー追加」の作業面を作り、リポジトリ標準のチェックまで実行してください。
```

```text
pm-skill で「パスワードなしログイン」のドラフト要件を作り、実装前のスコープ境界として目的、担当者、リスク、初期受け入れ条件を整理してください。
```

```text
magic-link sign-in の部分を正式要件に昇格し、その要件から TODO と受け入れマトリクスを作成してください。
```

```text
最初の TODO の work package を作成し、agent の作業コンテキストを制限するために実装ファイルと検証ファイルを追加して、完了前に受け入れマトリクスを検証してください。
```

他の言語で依頼してもかまいません。agent が自然言語を `pm-skill` コマンド、REST、または MCP 呼び出しに変換します。

## 基本コンセプト

- リポジトリ内のファイルが信頼できる事実です。
- `.pm-skill/` は機械可読な control-plane 状態を保存します。
- Markdown は要件、TODO、changelog、受け入れメモ、handover を保存します。
- CLI、REST、MCP は同じ command envelope を使うべきです。
- 書き込み操作は監査され、長い AI coding 作業を再構成できます。

## 便利なコマンド

| コマンド | 用途 |
| --- | --- |
| `pm-skill show-status --json` | 現在のブランチ、変更済みファイル、アクティブ TODO、警告、次の手順を確認します。 |
| `pm-skill recover-project --json` | プロジェクトの control state とコンテキストを復元します。 |
| `pm-skill create-requirement --title "..." --json` | 会話や仕様からドラフト要件を作成します。 |
| `pm-skill promote-requirement REQ-DRAFT-... --json` | ドラフト要件を正式要件へ昇格します。 |
| `pm-skill create-todo-from-source --source-requirement REQ-... --json` | 正式要件から追跡可能な TODO を作成します。 |
| `pm-skill create-acceptance-matrix TODO-... --json` | TODO の受け入れマトリクスを生成します。 |
| `pm-skill create-work-package TODO-... --json` | agent のコンテキストを制限する focused work package を作成します。 |
| `pm-skill validate-acceptance TODO-... --checks-profile default --json` | 受け入れマトリクスと checks で完了度を検証します。 |
| `pm-skill handover --summary-level standard --json` | 次のセッションのために handover を残します。 |

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
