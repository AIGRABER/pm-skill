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
```

설치한 뒤에는 coding agent에게 자연어로 요청하면 됩니다.

`pm-skill`의 핵심 가치는 단순한 컨텍스트 복구가 아니라 AI coding에 저장소 기반 control plane을 주는 것입니다: recover state -> discuss uncertainty -> extract draft requirements -> approve scope -> split TODOs -> constrain context -> verify acceptance -> audit changes -> handover/release.

```text
pm-skill로 C:\Users\win\Documents\MyProject 프로젝트를 초기화해줘. project id는 my-project, 표시 이름은 "My Project"로 해줘.
```

```text
pm-skill로 프로젝트 control state를 복구하고 현재 브랜치, 변경된 파일, 활성 요구사항, 남은 TODO, 위험, 다음 안전한 작업을 알려줘.
```

```text
로그인 개편에 무엇이 포함되어야 할지 아직 모르겠어. 먼저 나와 논의하고, 확인 질문을 하고, 대화에서 목표, 제약, 위험, 수락 기준을 추출한 뒤 pm-skill 초안 요구사항으로 저장해줘.
```

```text
pm-skill로 "로그인 흐름 추가" 작업 표면을 만들고 저장소의 기본 검사를 실행해줘.
```

```text
pm-skill로 "비밀번호 없는 로그인" 초안 요구사항을 만들고 코딩 전 범위 경계로 목표, 담당자, 위험, 초기 수락 기준을 정리해줘.
```

```text
magic-link sign-in 부분을 공식 요구사항으로 승격하고, 그 요구사항에서 TODO와 수락 매트릭스를 만들어줘.
```

```text
첫 번째 TODO의 work package를 만들고 agent의 작업 컨텍스트를 제한하도록 구현 파일과 검증 파일을 추가한 다음, 완료 처리 전에 수락 매트릭스를 검증해줘.
```

다른 언어로 요청해도 됩니다. agent가 자연어를 `pm-skill` 명령, REST 또는 MCP 호출로 변환합니다.

## 핵심 아이디어

- 저장소 파일이 사실의 기준입니다.
- `.pm-skill/`은 기계가 읽을 수 있는 control-plane 상태를 저장합니다.
- Markdown은 요구사항, TODO, changelog, 수락 메모, handover를 저장합니다.
- CLI, REST, MCP 어댑터는 같은 command envelope를 사용해야 합니다.
- 쓰기 작업은 감사 로그에 남아 긴 AI coding 작업을 재구성할 수 있습니다.

## 유용한 명령

| 명령 | 용도 |
| --- | --- |
| `pm-skill show-status --json` | 현재 브랜치, 변경 파일, 활성 TODO, 경고, 다음 단계를 확인합니다. |
| `pm-skill recover-project --json` | 프로젝트 control state와 컨텍스트를 복구합니다. |
| `pm-skill create-requirement --title "..." --json` | 대화나 명세에서 초안 요구사항을 만듭니다. |
| `pm-skill promote-requirement REQ-DRAFT-... --json` | 초안 요구사항을 공식 요구사항으로 승격합니다. |
| `pm-skill create-todo-from-source --source-requirement REQ-... --json` | 공식 요구사항에서 추적 가능한 TODO를 만듭니다. |
| `pm-skill create-acceptance-matrix TODO-... --json` | TODO의 수락 매트릭스를 생성합니다. |
| `pm-skill create-work-package TODO-... --json` | agent 컨텍스트를 제한하는 focused work package를 만듭니다. |
| `pm-skill validate-acceptance TODO-... --checks-profile default --json` | 수락 매트릭스와 checks로 완료도를 검증합니다. |
| `pm-skill handover --summary-level standard --json` | 다음 세션을 위한 handover를 남깁니다. |

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
