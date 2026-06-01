from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .command_router import execute_command_envelope, tool_descriptions as router_tool_descriptions


def run_tool(project_path: str | Path, command: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    return execute_command_envelope(
        project_path,
        {
            "request_id": "mcp_local",
            "command": command,
            "args": args or {},
            "actor": "agent",
            "session_id": "mcp",
        },
    )


def recover_project(project_path: str | Path = ".", hydrate_level: str = "standard") -> dict[str, Any]:
    return run_tool(project_path, "recover_project", {"hydrate_level": hydrate_level})


def list_todo(project_path: str | Path = ".", scope: str = "branch") -> dict[str, Any]:
    return run_tool(project_path, "list_todo", {"scope": scope})


def handover(project_path: str | Path = ".", summary_level: str = "standard") -> dict[str, Any]:
    return run_tool(project_path, "handover", {"summary_level": summary_level})


def list_work_branches(project_path: str | Path = ".", include_completed: bool = False) -> dict[str, Any]:
    return run_tool(project_path, "list_work_branches", {"include_completed": include_completed})


def prepare_release(
    project_path: str | Path = ".",
    version: str | None = None,
    branch: str | None = None,
    apply: bool = False,
    allow_unfinished: bool = False,
    checks_profile: str = "default",
) -> dict[str, Any]:
    return run_tool(
        project_path,
        "prepare_release",
        {
            "version": version,
            "branch": branch,
            "apply": apply,
            "allow_unfinished": allow_unfinished,
            "checks_profile": checks_profile,
        },
    )


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "recover_project": {
        "description": "恢复项目状态，包括 Git、manifest、TODO、需求、handover、warning 和下一步建议。",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "default": ".", "description": "目标项目根目录。"},
                "hydrate_level": {
                    "type": "string",
                    "enum": ["minimal", "standard", "full"],
                    "default": "standard",
                    "description": "恢复深度；minimal 适合快速进入，standard 是默认，full 预留给更完整扫描。",
                },
            },
        },
    },
    "list_todo": {
        "description": "列出 TODO，支持当前分支、全部分支或 legacy 根目录 TODO。",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "default": ".", "description": "目标项目根目录。"},
                "scope": {
                    "type": "string",
                    "enum": ["branch", "all", "legacy"],
                    "default": "branch",
                    "description": "TODO 范围：当前分支、全部分支或旧版根目录 TODO。",
                },
            },
        },
    },
    "handover": {
        "description": "生成跨会话交接文档，并更新 manifest.latest_handover。",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "default": ".", "description": "目标项目根目录。"},
                "summary_level": {"type": "string", "default": "standard", "description": "摘要详细程度。"},
            },
        },
    },
    "list_work_branches": {
        "description": "列出正在开发或已完结的分支工作进展。",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "default": ".", "description": "目标项目根目录。"},
                "include_completed": {"type": "boolean", "default": False, "description": "是否包含已标记完结的分支。"},
            },
        },
    },
    "prepare_release": {
        "description": "准备发布：检查未完成分支、聚合分支版本变更，并可提议基线版本。",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "default": ".", "description": "目标项目根目录。"},
                "version": {
                    "type": ["string", "null"],
                    "description": "可选 SemVer 版本，例如 v0.2.0；默认只聚合 release notes。",
                },
                "branch": {
                    "type": ["string", "null"],
                    "description": "只聚合某个分支的 changelog；为空时聚合全部分支 changelog。",
                },
                "apply": {"type": "boolean", "default": False, "description": "是否真正写入全局 CHANGELOG 并运行检查。"},
                "allow_unfinished": {
                    "type": "boolean",
                    "default": False,
                    "description": "存在未完成分支时是否仍继续生成发布提案。",
                },
                "checks_profile": {"type": "string", "default": "default", "description": "apply 模式下使用的检查 profile。"},
            },
        },
    },
}


def tool_descriptions() -> dict[str, Any]:
    return router_tool_descriptions()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--list-tools":
        print(json.dumps(tool_descriptions(), ensure_ascii=False, indent=2))
        return
    payload = json.loads(sys.stdin.read() or "{}")
    project_path = payload.pop("project_path", ".")
    result = execute_command_envelope(project_path, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
