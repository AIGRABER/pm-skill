from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from . import commands
from .paths import ProjectPaths
from .pydantic_models import validate_command_envelope
from .runtime import CommandEffects, CommandSpec, RunContext, execute_with_runtime


Handler = Callable[[RunContext, dict[str, Any]], dict[str, Any]]


def _call(fn: Callable[..., dict[str, Any]], *names: str) -> Handler:
    def handler(context: RunContext, args: dict[str, Any]) -> dict[str, Any]:
        kwargs = {name: args[name] for name in names if name in args}
        return fn(context.paths, **kwargs)

    return handler


def _spec(
    name: str,
    handler: Handler,
    *,
    aliases: tuple[str, ...] = (),
    arg_names: tuple[str, ...] = (),
    description: str = "",
    effects: CommandEffects | None = None,
    requires_manifest: bool = True,
    requires_clean_worktree: bool = False,
    allow_protected_branch: bool = True,
    audit: bool = True,
    discover_repo: bool = True,
) -> CommandSpec:
    return CommandSpec(
        name=name,
        handler=handler,
        aliases=aliases,
        arg_names=arg_names,
        description=description,
        effects=effects or CommandEffects(),
        requires_manifest=requires_manifest,
        requires_clean_worktree=requires_clean_worktree,
        allow_protected_branch=allow_protected_branch,
        audit=audit,
        discover_repo=discover_repo,
    )


COMMAND_SPECS: list[CommandSpec] = [
    _spec(
        "show_status",
        _call(commands.show_status),
        aliases=("show-status",),
        description="显示项目状态摘要。",
        requires_manifest=False,
    ),
    _spec(
        "get_context",
        _call(commands.get_context, "mode"),
        aliases=("get-context",),
        arg_names=("mode",),
        description="输出当前回合所需的低噪声项目上下文。",
        effects=CommandEffects(read_repo=True),
        requires_manifest=False,
    ),
    _spec(
        "recover_project",
        _call(commands.recover_project, "hydrate_level"),
        aliases=("recover-project",),
        arg_names=("hydrate_level",),
        description="恢复项目状态，包括 Git、manifest、TODO、需求、handover、warning 和下一步建议。",
        requires_manifest=False,
    ),
    _spec(
        "help",
        lambda _context, _args: commands.help_guide(),
        description="显示完整的项目使用说明。",
        requires_manifest=False,
        discover_repo=False,
    ),
    _spec(
        "export_schemas",
        _call(commands.export_schemas),
        aliases=("export-schemas",),
        description="导出 JSON Schema 文件。",
        requires_manifest=False,
        discover_repo=False,
    ),
    _spec(
        "describe_command",
        lambda _context, args: describe_command(args["command"]),
        aliases=("describe-command",),
        arg_names=("command",),
        description="展示单个命令的能力与约束。",
        requires_manifest=False,
        discover_repo=False,
    ),
    _spec(
        "list_todo",
        _call(commands.list_to_do, "statuses", "priorities", "source_requirement", "scope", "branch"),
        aliases=("list-todo",),
        arg_names=("statuses", "priorities", "source_requirement", "scope", "branch"),
        description="列出 TODO 文件。",
    ),
    _spec(
        "create_todo",
        _call(commands.create_todo, "title", "priority", "status", "source_requirement", "assignee", "body"),
        aliases=("create-todo",),
        arg_names=("title", "priority", "status", "source_requirement", "assignee", "body"),
        description="创建 TODO 文档。",
        effects=CommandEffects(write_repo=True, git_write=False),
    ),
    _spec(
        "create_todo_from_source",
        _call(
            commands.create_todo_from_source,
            "title",
            "source_requirement",
            "source_path",
            "priority",
            "status",
            "assignee",
        ),
        aliases=("create-todo-from-source",),
        arg_names=("title", "source_requirement", "source_path", "priority", "status", "assignee"),
        description="从文档、正式需求或草案需求生成 TODO，并审计 TODO 是否覆盖来源功能与逻辑。",
        effects=CommandEffects(write_repo=True, git_write=False),
    ),
    _spec(
        "create_work_surface",
        _call(
            commands.create_work_surface,
            "title",
            "branch_name",
            "requirement_title",
            "todo_title",
            "priority",
            "owners",
            "acceptance",
            "body",
        ),
        aliases=("create-work-surface",),
        arg_names=("title", "branch_name", "requirement_title", "todo_title", "priority", "owners", "acceptance", "body"),
        description="一键创建分支感知的需求、TODO 和已启动任务。",
        effects=CommandEffects(write_repo=True, git_write=True),
    ),
    _spec(
        "list_work_branches",
        _call(commands.list_work_branches, "include_completed", "human"),
        aliases=("list-work-branches",),
        arg_names=("include_completed", "human"),
        description="列出正在开发或已完成的分支工作。",
    ),
    _spec(
        "mark_branch_work",
        _call(commands.mark_branch_work, "branch", "completed", "progress_note"),
        aliases=("mark-branch-work",),
        arg_names=("branch", "completed", "progress_note"),
        description="标记分支工作是否已完成。",
    ),
    _spec(
        "update_work_surface",
        _call(
            commands.update_work_surface,
            "branch",
            "progress_note",
            "completed",
            "todo_ids",
            "todo_status",
            "changelog_entry",
            "changelog_category",
            "changelog_scope",
        ),
        aliases=("update-work-surface",),
        arg_names=("branch", "progress_note", "completed", "todo_ids", "todo_status", "changelog_entry", "changelog_category", "changelog_scope"),
        description="同步分支进展、TODO 状态与版本变更。",
        effects=CommandEffects(write_repo=True, git_write=True),
    ),
    _spec(
        "create_acceptance_matrix",
        _call(commands.create_acceptance_matrix, "todo_id"),
        aliases=("create-acceptance-matrix",),
        arg_names=("todo_id",),
        description="从 TODO 生成验收矩阵，并审计矩阵是否覆盖 TODO。",
        effects=CommandEffects(write_repo=True, git_write=False),
    ),
    _spec(
        "validate_acceptance",
        _call(commands.validate_acceptance, "todo_id", "matrix_path", "run_checks_profile"),
        aliases=("validate-acceptance",),
        arg_names=("todo_id", "matrix_path", "run_checks_profile"),
        description="对照验收矩阵和可选检查命令执行验收。",
        effects=CommandEffects(read_repo=True, run_shell=True),
    ),
    _spec(
        "create_work_package",
        _call(commands.create_work_package, "todo_id"),
        aliases=("create-work-package",),
        arg_names=("todo_id",),
        description="为指定 TODO 创建独立工作包目录。",
        effects=CommandEffects(write_repo=True),
    ),
    _spec(
        "add_work_package_context",
        _call(commands.add_work_package_context, "todo_id", "action", "file", "reason"),
        aliases=("add-work-package-context",),
        arg_names=("todo_id", "action", "file", "reason"),
        description="向 TODO 工作包追加实现或验证上下文条目。",
        effects=CommandEffects(write_repo=True),
    ),
    _spec(
        "list_work_packages",
        _call(commands.list_work_packages, "todo_id"),
        aliases=("list-work-packages",),
        arg_names=("todo_id",),
        description="列出 TODO 工作包摘要。",
    ),
    _spec(
        "refresh_template_hashes",
        _call(commands.refresh_template_hashes, "managed_paths"),
        aliases=("refresh-template-hashes",),
        arg_names=("managed_paths",),
        description="刷新 pm-skill 托管模板 hash manifest。",
        effects=CommandEffects(write_repo=True),
    ),
    _spec(
        "check_template_hashes",
        _call(commands.check_template_hashes),
        aliases=("check-template-hashes",),
        description="检查 pm-skill 托管模板 hash 状态。",
    ),
    _spec(
        "prepare_release_notes",
        _call(commands.prepare_release_notes, "branch", "apply"),
        aliases=("prepare-release-notes",),
        arg_names=("branch", "apply"),
        description="汇总分支版本变更到全局发布说明。",
        effects=CommandEffects(write_repo=True),
    ),
    _spec(
        "prepare_release",
        _call(commands.prepare_release, "version", "branch", "apply", "allow_unfinished", "checks_profile"),
        aliases=("prepare-release",),
        arg_names=("version", "branch", "apply", "allow_unfinished", "checks_profile"),
        description="准备发布并执行检查。",
        effects=CommandEffects(write_repo=True, run_shell=True),
        requires_clean_worktree=False,
    ),
    _spec(
        "migrate_legacy_todo",
        _call(commands.migrate_legacy_todo, "branch", "todo_id"),
        aliases=("migrate-legacy-todo",),
        arg_names=("branch", "todo_id"),
        description="迁移旧版根目录 TODO 到分支目录。",
        effects=CommandEffects(write_repo=True, git_write=False),
    ),
    _spec(
        "list_requirements",
        _call(commands.list_requirements, "status"),
        aliases=("list-requirements",),
        arg_names=("status",),
        description="列出当前分支的需求集合。",
    ),
    _spec(
        "show_requirement",
        _call(commands.show_requirement, "requirement_id"),
        aliases=("show-requirement",),
        arg_names=("requirement_id",),
        description="显示单个需求详情。",
    ),
    _spec(
        "delete_requirement",
        _call(commands.delete_requirement, "requirement_id", "remove_todos"),
        aliases=("delete-requirement",),
        arg_names=("requirement_id", "remove_todos"),
        description="删除需求并可选清理相关 TODO。",
        effects=CommandEffects(write_repo=True),
    ),
    _spec(
        "run_checks",
        _call(commands.run_checks, "profile"),
        aliases=("run-checks",),
        arg_names=("profile",),
        description="运行策略指定的检查命令。",
        effects=CommandEffects(run_shell=True),
    ),
    _spec(
        "check_docs_encoding",
        _call(commands.check_docs_encoding, "scope"),
        aliases=("check-docs-encoding",),
        arg_names=("scope",),
        description="检查 Markdown 文档是否存在编码或 mojibake 问题。",
        effects=CommandEffects(read_repo=True),
        requires_manifest=False,
    ),
    _spec(
        "sync_index",
        _call(commands.sync_index, "scope"),
        aliases=("sync-index",),
        arg_names=("scope",),
        description="同步文件指纹与摘要索引。",
        effects=CommandEffects(write_repo=True),
    ),
    _spec(
        "handover",
        _call(commands.handover, "summary_level", "session_id", "next_action"),
        arg_names=("summary_level", "session_id", "next_action"),
        description="生成交接文档并更新 manifest.latest_handover。",
        effects=CommandEffects(write_repo=True),
    ),
    _spec(
        "query_audit",
        _call(commands.query_audit, "command", "ok", "limit"),
        aliases=("query-audit",),
        arg_names=("command", "ok", "limit"),
        description="查询审计事件。",
        requires_manifest=False,
    ),
    _spec(
        "init_project",
        _call(commands.init_project, "project_id", "default_branch", "force", "display_name", "create_package_dirs"),
        aliases=("init-project",),
        arg_names=("project_id", "default_branch", "force", "display_name", "create_package_dirs"),
        description="初始化项目管理控制面。",
        effects=CommandEffects(write_repo=True, git_write=False),
        requires_manifest=False,
        discover_repo=False,
    ),
    _spec(
        "onboard_project",
        _call(commands.onboard_project, "project_id", "default_branch", "display_name", "init_git", "force"),
        aliases=("onboard-project",),
        arg_names=("project_id", "default_branch", "display_name", "init_git", "force"),
        description="将已有目录接入项目管理控制面。",
        effects=CommandEffects(write_repo=True, git_write=True),
        requires_manifest=False,
        discover_repo=False,
    ),
]


def _spec_map() -> dict[str, CommandSpec]:
    mapping: dict[str, CommandSpec] = {}
    for spec in COMMAND_SPECS:
        for name in spec.names():
            mapping[name] = spec
    return mapping


COMMAND_SPEC_MAP = _spec_map()


def command_specs() -> list[dict[str, Any]]:
    return [spec.public_dict() for spec in COMMAND_SPECS]


def describe_command(name: str) -> dict[str, Any]:
    spec = COMMAND_SPEC_MAP.get(name)
    if not spec:
        raise RuntimeError(f"Unsupported command: {name}")
    return {"ok": True, "command": spec.public_dict()}


def tool_descriptions() -> dict[str, Any]:
    tools = {
        spec.name: {
            "description": spec.description,
            "input_schema": spec.tool_schema()["input_schema"],
            "effects": spec.effects.to_dict(),
            "aliases": list(spec.aliases),
        }
        for spec in COMMAND_SPECS
        if spec.name not in {"help", "export_schemas", "init_project", "onboard_project"}
    }
    return {"ok": True, "tools": tools}


def execute_command_envelope(project_path: str | Path, envelope: dict[str, Any]) -> dict[str, Any]:
    validated = validate_command_envelope(envelope)
    command = validated["command"]
    spec = COMMAND_SPEC_MAP.get(command)
    if not spec:
        raise RuntimeError(f"Unsupported command: {command}")
    return execute_with_runtime(project_path, validated, spec)


def supported_commands() -> list[str]:
    return sorted(COMMAND_SPEC_MAP)
