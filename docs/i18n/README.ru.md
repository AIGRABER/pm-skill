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
```

После установки можно говорить с coding agent обычным языком:

Главная ценность `pm-skill` не только в восстановлении контекста. Он дает AI coding контрольную плоскость внутри репозитория: recover state -> discuss uncertainty -> extract draft requirements -> approve scope -> split TODOs -> constrain context -> verify acceptance -> audit changes -> handover/release.

```text
Инициализируй проект C:\Users\win\Documents\MyProject через pm-skill. project id: my-project, display name: "My Project".
```

```text
Используй pm-skill, чтобы восстановить контрольное состояние проекта: текущая ветка, измененные файлы, активные требования, открытые TODO, риски и следующий безопасный шаг.
```

```text
Я пока не уверен, что должно входить в редизайн логина. Сначала обсуди это со мной, задай уточняющие вопросы, извлеки из разговора цели, ограничения, риски и критерии приемки, затем сохрани как черновик требования pm-skill для проверки.
```

```text
Создай через pm-skill рабочую поверхность для "Add login flow" и запусти стандартные проверки репозитория.
```

```text
Создай через pm-skill черновик требования для "Passwordless login" как границу объема до кодинга: цель, владельцы, риски и начальные критерии приемки.
```

```text
Повышай часть про magic-link sign-in до формального требования, затем создай из него TODO и acceptance matrix.
```

```text
Создай work package для первого TODO, добавь файлы реализации и проверки, чтобы ограничить рабочий контекст agent, затем проверь acceptance matrix перед завершением.
```

Можно писать запрос на любом удобном языке; agent переводит намерение в команды `pm-skill`, REST или MCP-вызовы.

## Ключевые Идеи

- Файлы репозитория являются источником истины.
- `.pm-skill/` хранит машинно-читаемое состояние контрольной плоскости.
- Markdown хранит требования, TODO, changelog, заметки приемки и handover.
- CLI, REST и MCP должны использовать один command envelope.
- Операции записи аудируются, чтобы длинную AI coding работу можно было восстановить.

## Полезные Команды

| Команда | Назначение |
| --- | --- |
| `pm-skill show-status --json` | Посмотреть текущую ветку, измененные файлы, активные TODO, предупреждения и следующий шаг. |
| `pm-skill recover-project --json` | Восстановить control state и контекст проекта. |
| `pm-skill create-requirement --title "..." --json` | Создать черновик требования из обсуждения или спецификации. |
| `pm-skill promote-requirement REQ-DRAFT-... --json` | Повысить черновик требования до формального требования. |
| `pm-skill create-todo-from-source --source-requirement REQ-... --json` | Создать отслеживаемый TODO из формального требования. |
| `pm-skill create-acceptance-matrix TODO-... --json` | Создать acceptance matrix для TODO. |
| `pm-skill create-work-package TODO-... --json` | Создать focused work package, ограничивающий контекст agent. |
| `pm-skill validate-acceptance TODO-... --checks-profile default --json` | Проверить готовность через acceptance matrix и checks. |
| `pm-skill handover --summary-level standard --json` | Оставить handover для следующей сессии. |

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
