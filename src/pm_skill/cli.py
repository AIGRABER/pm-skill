from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from . import commands
from .command_router import describe_command
from .paths import ProjectPaths


CHANGELOG_CATEGORY_CHOICES = [
    "Added", "Changed", "Fixed", "Removed", "Deprecated", "Security", "Docs",
    "新增", "变更", "修改", "修复", "移除", "删除", "废弃", "安全", "文档",
]


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        raise SystemExit(2)
    project_path = Path(args.project_path).resolve()
    no_discover_commands = {
        "help",
        "export-schemas",
        "describe-command",
        "init-project",
        "onboard-project",
    }
    if args.command in no_discover_commands:
        paths = ProjectPaths(project_path)
    else:
        paths = ProjectPaths.discover(project_path)
    try:
        result = args.handler(paths, args)
    except Exception as exc:  # noqa: BLE001 - CLI boundary should convert all errors.
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
    emit(result, as_json=getattr(args, "json", False))


def emit(result: dict[str, Any], as_json: bool = False) -> None:
    if as_json or not result.get("ok", False):
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return
    if set(result) == {"ok", "text"}:
        print(result["text"])
        return
    for key, value in result.items():
        if key == "ok":
            continue
        if isinstance(value, (dict, list)):
            print(f"{key}: {json.dumps(value, ensure_ascii=False, default=str)}")
        else:
            print(f"{key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pm-skill")
    parser.add_argument(
        "--project-path",
        default=".",
        help="Target project directory. Defaults to the current working directory.",
    )
    sub = parser.add_subparsers(dest="command")

    add_json_flag(
        sub.add_parser("help", help="Show complete project-dev-management usage guide."),
        lambda paths, args: commands.help_guide(),
    )

    add_json_flag(
        sub.add_parser("export-schemas", help="Write JSON schema files."),
        lambda paths, args: commands.export_schemas(paths),
    )

    describe = sub.add_parser("describe-command", help="Show a command spec and runtime effects.")
    describe.add_argument("command")
    add_json_flag(describe, lambda paths, args: describe_command(args.command))

    init = sub.add_parser("init-project", help="Initialize repository project-management metadata.")
    init.add_argument("--project-id", required=True)
    init.add_argument("--default-branch", default="master")
    init.add_argument("--display-name")
    init.add_argument("--force", action="store_true")
    add_json_flag(
        init,
        lambda paths, args: commands.init_project(
            paths,
            project_id=args.project_id,
            default_branch=args.default_branch,
            force=args.force,
            display_name=args.display_name,
        ),
    )

    onboard = sub.add_parser("onboard-project", help="Onboard an existing project directory into pm-skill management.")
    onboard.add_argument("--project-id")
    onboard.add_argument("--default-branch")
    onboard.add_argument("--display-name")
    onboard.add_argument("--init-git", action="store_true", default=True)
    onboard.add_argument("--no-init-git", action="store_false", dest="init_git")
    onboard.add_argument("--force", action="store_true")
    add_json_flag(
        onboard,
        lambda paths, args: commands.onboard_project(
            paths,
            project_id=args.project_id,
            default_branch=args.default_branch,
            display_name=args.display_name,
            init_git=args.init_git,
            force=args.force,
        ),
    )

    recover = sub.add_parser("recover-project", help="Recover project state.")
    recover.add_argument("--hydrate-level", choices=["minimal", "standard", "full"], default="standard")
    add_json_flag(recover, lambda paths, args: commands.recover_project(paths, args.hydrate_level))

    add_json_flag(
        sub.add_parser("show-status", help="Show a compact project-state summary."),
        lambda paths, args: commands.show_status(paths),
    )

    context = sub.add_parser("get-context", help="Show low-noise turn context for AI work.")
    context.add_argument("--mode", choices=["turn", "full"], default="turn")
    add_json_flag(context, lambda paths, args: commands.get_context(paths, args.mode))

    list_todo = sub.add_parser("list-todo", help="List TODO files.")
    list_todo.add_argument("--status", action="append", dest="statuses")
    list_todo.add_argument("--priority", action="append", dest="priorities")
    list_todo.add_argument("--source-requirement")
    list_todo.add_argument("--scope", choices=["branch", "all", "legacy"], default="branch")
    list_todo.add_argument("--branch", help="Branch name to inspect when --scope branch is used.")
    add_json_flag(
        list_todo,
        lambda paths, args: commands.list_to_do(
            paths,
            statuses=args.statuses,
            priorities=args.priorities,
            source_requirement=args.source_requirement,
            scope=args.scope,
            branch=args.branch,
        ),
    )

    work_branches = sub.add_parser("list-work-branches", help="List active branch work and progress.")
    work_branches.add_argument("--include-completed", action="store_true")
    add_json_flag(
        work_branches,
        lambda paths, args: commands.list_work_branches(
            paths,
            include_completed=args.include_completed,
            human=not args.json,
        ),
    )

    mark_branch = sub.add_parser("mark-branch-work", help="Mark whether a branch's work is completed.")
    mark_branch.add_argument("--branch", help="Branch name. Defaults to the current branch.")
    mark_branch.add_argument("--completed", action="store_true", help="Mark branch work as completed.")
    mark_branch.add_argument("--active", action="store_true", help="Mark branch work as active/not completed.")
    mark_branch.add_argument("--progress-note")
    add_json_flag(
        mark_branch,
        lambda paths, args: commands.mark_branch_work(
            paths,
            branch=args.branch,
            completed=False if args.active else args.completed,
            progress_note=args.progress_note,
        ),
    )

    update_surface = sub.add_parser(
        "update-work-surface",
        help="Update branch work-surface progress, TODO status, changelog, and completion marker.",
    )
    update_surface.add_argument("--branch", help="Branch name. Defaults to the current branch.")
    update_surface.add_argument("--progress-note")
    update_surface.add_argument("--completed", action="store_true", help="Mark branch work as completed.")
    update_surface.add_argument("--active", action="store_true", help="Mark branch work as active/not completed.")
    update_surface.add_argument("--todo-id", action="append", dest="todo_ids", default=[])
    update_surface.add_argument(
        "--todo-status",
        choices=["draft", "ready", "in_progress", "blocked", "done", "cancelled"],
    )
    update_surface.add_argument("--changelog-entry")
    update_surface.add_argument(
        "--changelog-category",
        default="Changed",
        choices=CHANGELOG_CATEGORY_CHOICES,
    )
    update_surface.add_argument("--changelog-scope", choices=["branch", "global"], default="branch")
    add_json_flag(
        update_surface,
        lambda paths, args: commands.update_work_surface(
            paths,
            branch=args.branch,
            progress_note=args.progress_note,
            completed=False if args.active else (True if args.completed else None),
            todo_ids=args.todo_ids or None,
            todo_status=args.todo_status,
            changelog_entry=args.changelog_entry,
            changelog_category=args.changelog_category,
            changelog_scope=args.changelog_scope,
        ),
    )

    release_notes = sub.add_parser(
        "prepare-release-notes",
        help="Merge branch changelog entries into the global CHANGELOG.",
    )
    release_notes.add_argument("--branch", help="Only merge one branch changelog. Defaults to all branch changelogs.")
    release_notes.add_argument("--apply", action="store_true", help="Write entries into root CHANGELOG.md.")
    add_json_flag(
        release_notes,
        lambda paths, args: commands.prepare_release_notes(
            paths,
            branch=args.branch,
            apply=args.apply,
        ),
    )

    prepare_release = sub.add_parser(
        "prepare-release",
        help="Run release preparation checks and release-note aggregation.",
    )
    prepare_release.add_argument("--version", help="Optional SemVer baseline version to propose.")
    prepare_release.add_argument("--branch", help="Only aggregate one branch changelog.")
    prepare_release.add_argument("--apply", action="store_true", help="Apply release-note merge after checks.")
    prepare_release.add_argument("--allow-unfinished", action="store_true")
    prepare_release.add_argument("--checks-profile", default="default")
    add_json_flag(
        prepare_release,
        lambda paths, args: commands.prepare_release(
            paths,
            version=args.version,
            branch=args.branch,
            apply=args.apply,
            allow_unfinished=args.allow_unfinished,
            checks_profile=args.checks_profile,
        ),
    )

    migrate_legacy = sub.add_parser("migrate-legacy-todo", help="Move legacy todo/*.md files into a branch TODO folder.")
    migrate_legacy.add_argument("--branch", required=True)
    migrate_legacy.add_argument("--todo-id")
    add_json_flag(
        migrate_legacy,
        lambda paths, args: commands.migrate_legacy_todo(
            paths,
            branch=args.branch,
            todo_id=args.todo_id,
        ),
    )

    create_todo = sub.add_parser("create-todo", help="Create a TODO document.")
    create_todo.add_argument("--title", required=True)
    create_todo.add_argument("--priority", default="P2", choices=["P0", "P1", "P2", "P3"])
    create_todo.add_argument(
        "--status",
        default="ready",
        choices=["draft", "ready", "in_progress", "blocked", "done", "cancelled"],
    )
    create_todo.add_argument("--source-requirement")
    create_todo.add_argument("--assignee", default="agent")
    create_todo.add_argument("--body")
    add_json_flag(
        create_todo,
        lambda paths, args: commands.create_todo(
            paths,
            title=args.title,
            priority=args.priority,
            status=args.status,
            source_requirement=args.source_requirement,
            assignee=args.assignee,
            body=args.body,
        ),
    )

    create_todo_source = sub.add_parser(
        "create-todo-from-source",
        help="Create a TODO from a document or requirement and audit source coverage.",
    )
    create_todo_source.add_argument("--title")
    source_group = create_todo_source.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--source-requirement")
    source_group.add_argument("--source-path")
    create_todo_source.add_argument("--priority", default="P1", choices=["P0", "P1", "P2", "P3"])
    create_todo_source.add_argument("--status", default="ready")
    create_todo_source.add_argument("--assignee", default="agent")
    add_json_flag(
        create_todo_source,
        lambda paths, args: commands.create_todo_from_source(
            paths,
            title=args.title,
            source_requirement=args.source_requirement,
            source_path=args.source_path,
            priority=args.priority,
            status=args.status,
            assignee=args.assignee,
        ),
    )

    work_surface = sub.add_parser(
        "create-work-surface",
        help="Create a branch-aware requirement, TODO, and started task in one command.",
    )
    work_surface.add_argument("--title", required=True)
    work_surface.add_argument("--branch-name")
    work_surface.add_argument("--requirement-title")
    work_surface.add_argument("--todo-title")
    work_surface.add_argument("--priority", default="P1", choices=["P0", "P1", "P2", "P3"])
    work_surface.add_argument("--owner", action="append", default=[])
    work_surface.add_argument("--acceptance", action="append", default=[])
    work_surface.add_argument("--body")
    add_json_flag(
        work_surface,
        lambda paths, args: commands.create_work_surface(
            paths,
            title=args.title,
            branch_name=args.branch_name,
            requirement_title=args.requirement_title,
            todo_title=args.todo_title,
            priority=args.priority,
            owners=args.owner,
            acceptance=args.acceptance,
            body=args.body,
        ),
    )

    create_req = sub.add_parser("create-requirement", help="Create a draft requirement document.")
    create_req.add_argument("--title", required=True)
    create_req.add_argument("--owner", action="append", default=[])
    create_req.add_argument("--acceptance", action="append", default=[])
    create_req.add_argument("--body")
    add_json_flag(
        create_req,
        lambda paths, args: commands.create_requirement(
            paths,
            title=args.title,
            owners=args.owner,
            acceptance=args.acceptance,
            body=args.body,
        ),
    )

    update_req = sub.add_parser("update-requirement", help="Update a draft requirement document.")
    update_req.add_argument("requirement_id")
    update_req.add_argument("--title")
    update_req.add_argument("--owner", action="append")
    update_req.add_argument("--acceptance", action="append")
    update_req.add_argument("--depends-on", action="append", dest="depends_on")
    update_req.add_argument(
        "--status",
        choices=["draft", "approved", "superseded", "rejected"],
    )
    update_req.add_argument("--append-body")
    update_req.add_argument("--allow-final", action="store_true")
    add_json_flag(
        update_req,
        lambda paths, args: commands.update_requirement(
            paths,
            args.requirement_id,
            title=args.title,
            owner=args.owner,
            acceptance=args.acceptance,
            depends_on=args.depends_on,
            status=args.status,
            append_body=args.append_body,
            allow_final=args.allow_final,
        ),
    )

    list_req = sub.add_parser("list-requirements", help="List branch requirement collections.")
    list_req.add_argument("--status", choices=["draft", "approved", "superseded", "rejected"])
    add_json_flag(
        list_req,
        lambda paths, args: commands.list_requirements(paths, status=args.status),
    )

    show_req = sub.add_parser("show-requirement", help="Show a requirement by id.")
    show_req.add_argument("requirement_id")
    add_json_flag(
        show_req,
        lambda paths, args: commands.show_requirement(paths, args.requirement_id),
    )

    delete_req = sub.add_parser("delete-requirement", help="Delete a requirement and related TODOs.")
    delete_req.add_argument("requirement_id")
    delete_req.add_argument("--keep-todos", action="store_true")
    add_json_flag(
        delete_req,
        lambda paths, args: commands.delete_requirement(
            paths,
            args.requirement_id,
            remove_todos=not args.keep_todos,
        ),
    )

    start = sub.add_parser("start-task", help="Start a TODO.")
    start.add_argument("todo_id")
    start.add_argument("--branch-mode", choices=["new_branch", "current_branch"], default="new_branch")
    start.add_argument("--branch-name", help="Explicit branch name to create; Chinese names are supported.")
    add_json_flag(
        start,
        lambda paths, args: commands.start_task(
            paths,
            args.todo_id,
            args.branch_mode,
            branch_name=args.branch_name,
        ),
    )

    update = sub.add_parser("update-task", help="Update TODO metadata.")
    update.add_argument("todo_id")
    update.add_argument("--status")
    update.add_argument("--blocked-by", action="append", default=[])
    update.add_argument("--progress-line")
    update.add_argument("--changelog-entry")
    update.add_argument("--changelog-scope", choices=["branch", "global"], default="branch")
    update.add_argument(
        "--changelog-category",
        default="Changed",
        choices=CHANGELOG_CATEGORY_CHOICES,
    )
    add_json_flag(
        update,
        lambda paths, args: commands.update_task(
            paths,
            args.todo_id,
            status=args.status,
            blocked_by=args.blocked_by or None,
            progress_line=args.progress_line,
            changelog_entry=args.changelog_entry,
            changelog_category=args.changelog_category,
            changelog_scope=args.changelog_scope,
        ),
    )

    changelog = sub.add_parser("add-changelog-entry", help="Add an Unreleased changelog entry.")
    changelog.add_argument("--message", required=True)
    changelog.add_argument(
        "--category",
        default="Changed",
        choices=CHANGELOG_CATEGORY_CHOICES,
    )
    changelog.add_argument("--requirement-id")
    changelog.add_argument("--todo-id")
    changelog.add_argument("--scope", choices=["branch", "global"], default="branch")
    changelog.add_argument("--branch", help="Branch name for branch-scoped changelog.")
    add_json_flag(
        changelog,
        lambda paths, args: commands.add_changelog_entry(
            paths,
            message=args.message,
            category=args.category,
            requirement_id=args.requirement_id,
            todo_id=args.todo_id,
            scope=args.scope,
            branch=args.branch,
        ),
    )

    promote = sub.add_parser("promote-requirement", help="Promote a draft requirement.")
    promote.add_argument("requirement_id")
    promote.add_argument("--version")
    promote.add_argument("--baseline-ref")
    add_json_flag(
        promote,
        lambda paths, args: commands.promote_requirement(
            paths,
            args.requirement_id,
            version=args.version,
            baseline_ref=args.baseline_ref,
        ),
    )

    promote_slice = sub.add_parser(
        "promote-requirement-slice",
        help="Promote part of a draft requirement into a formal requirement.",
    )
    promote_slice.add_argument("source_requirement_id")
    promote_slice.add_argument("--title", required=True)
    promote_slice.add_argument("--acceptance", action="append", required=True)
    promote_slice.add_argument("--source-slice")
    promote_slice.add_argument("--version")
    promote_slice.add_argument("--body")
    add_json_flag(
        promote_slice,
        lambda paths, args: commands.promote_requirement_slice(
            paths,
            source_requirement_id=args.source_requirement_id,
            title=args.title,
            acceptance=args.acceptance,
            source_slice=args.source_slice,
            version=args.version,
            body=args.body,
        ),
    )

    matrix = sub.add_parser("create-acceptance-matrix", help="Create and audit an acceptance matrix for a TODO.")
    matrix.add_argument("todo_id")
    add_json_flag(
        matrix,
        lambda paths, args: commands.create_acceptance_matrix(paths, args.todo_id),
    )

    validate = sub.add_parser("validate-acceptance", help="Validate a TODO against its acceptance matrix and optional checks.")
    validate.add_argument("todo_id")
    validate.add_argument("--matrix-path")
    validate.add_argument("--checks-profile")
    add_json_flag(
        validate,
        lambda paths, args: commands.validate_acceptance(
            paths,
            args.todo_id,
            matrix_path=args.matrix_path,
            run_checks_profile=args.checks_profile,
        ),
    )

    package = sub.add_parser("create-work-package", help="Create a TODO work package directory.")
    package.add_argument("todo_id")
    add_json_flag(package, lambda paths, args: commands.create_work_package(paths, args.todo_id))

    package_context = sub.add_parser(
        "add-work-package-context",
        help="Add implementation or verification context to a TODO work package.",
    )
    package_context.add_argument("todo_id")
    package_context.add_argument("--action", required=True, choices=["implementation", "verification"])
    package_context.add_argument("--file", required=True)
    package_context.add_argument("--reason", required=True)
    add_json_flag(
        package_context,
        lambda paths, args: commands.add_work_package_context(
            paths,
            args.todo_id,
            action=args.action,
            file=args.file,
            reason=args.reason,
        ),
    )

    list_packages = sub.add_parser("list-work-packages", help="List TODO work packages.")
    list_packages.add_argument("--todo-id")
    add_json_flag(list_packages, lambda paths, args: commands.list_work_packages(paths, args.todo_id))

    refresh_templates = sub.add_parser(
        "refresh-template-hashes",
        help="Refresh hashes for pm-skill managed template files.",
    )
    refresh_templates.add_argument("--path", action="append", dest="paths")
    add_json_flag(
        refresh_templates,
        lambda paths, args: commands.refresh_template_hashes(paths, args.paths),
    )

    add_json_flag(
        sub.add_parser("check-template-hashes", help="Check pm-skill managed template hashes."),
        lambda paths, args: commands.check_template_hashes(paths),
    )

    baseline = sub.add_parser("create-baseline", help="Create or propose a baseline.")
    baseline.add_argument("name")
    baseline.add_argument("--from-ref", default="HEAD")
    baseline.add_argument("--apply", action="store_true")
    add_json_flag(
        baseline,
        lambda paths, args: commands.create_baseline(
            paths,
            name=args.name,
            from_ref=args.from_ref,
            apply=args.apply,
        ),
    )

    checks = sub.add_parser("run-checks", help="Run configured checks.")
    checks.add_argument("--profile", default="default")
    add_json_flag(checks, lambda paths, args: commands.run_checks(paths, args.profile))

    docs_check = sub.add_parser("check-docs-encoding", help="Check Markdown docs for encoding/mojibake issues.")
    docs_check.add_argument("--scope", default="docs", choices=["docs", "all"])
    add_json_flag(docs_check, lambda paths, args: commands.check_docs_encoding(paths, args.scope))

    sync = sub.add_parser("sync-index", help="Synchronize file fingerprints and summaries.")
    sync.add_argument("--scope", choices=["all", "changed"], default="all")
    add_json_flag(sync, lambda paths, args: commands.sync_index(paths, args.scope))

    ho = sub.add_parser("handover", help="Generate a handover document.")
    ho.add_argument("--summary-level", default="standard")
    ho.add_argument("--session-id", default="local")
    ho.add_argument("--next-action", action="append", default=[])
    add_json_flag(
        ho,
        lambda paths, args: commands.handover(
            paths,
            summary_level=args.summary_level,
            session_id=args.session_id,
            next_action=args.next_action or None,
        ),
    )

    audit = sub.add_parser("query-audit", help="Query audit JSONL events.")
    audit.add_argument("--command")
    audit.add_argument("--ok", choices=["true", "false"])
    audit.add_argument("--limit", type=int, default=20)
    add_json_flag(
        audit,
        lambda paths, args: commands.query_audit(
            paths,
            command=args.command,
            ok=None if args.ok is None else args.ok == "true",
            limit=args.limit,
        ),
    )

    return parser


def add_json_flag(parser: argparse.ArgumentParser, handler: Callable[[ProjectPaths, Any], dict[str, Any]]) -> None:
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.set_defaults(handler=handler)


if __name__ == "__main__":
    main()
