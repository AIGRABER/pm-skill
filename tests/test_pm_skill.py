from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pm_skill.commands import (  # noqa: E402
    add_changelog_entry,
    check_docs_encoding,
    add_work_package_context,
    create_acceptance_matrix,
    create_requirement,
    create_todo,
    create_todo_from_source,
    create_work_package,
    create_work_surface,
    delete_requirement,
    get_context,
    handover,
    help_guide,
    init_project,
    list_work_branches,
    list_to_do,
    list_requirements,
    list_work_packages,
    migrate_legacy_todo,
    onboard_project,
    mark_branch_work,
    prepare_release,
    prepare_release_notes,
    promote_requirement,
    promote_requirement_slice,
    query_audit,
    recover_project,
    refresh_template_hashes,
    check_template_hashes,
    show_requirement,
    start_task,
    sync_index,
    update_task,
    update_work_surface,
    update_requirement,
    validate_acceptance,
)
from pm_skill.command_router import describe_command, execute_command_envelope, supported_commands  # noqa: E402
from pm_skill.frontmatter_io import read_frontmatter, write_frontmatter  # noqa: E402
from pm_skill.git_client import GitClient  # noqa: E402
from pm_skill.models import RequirementMeta, TodoMeta  # noqa: E402
from pm_skill.paths import ProjectPaths  # noqa: E402


class PmSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True, text=True)
        self.paths = ProjectPaths.discover(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "pm_skill", "--project-path", str(self.root), *args],
            cwd=self.root,
            text=True,
            capture_output=True,
            env=env,
            check=True,
        )

    def mark_acceptance_matrix_passed(self, matrix_path: str) -> None:
        path = self.root / matrix_path
        text = path.read_text(encoding="utf-8")
        text = text.replace("待补充", "tests/test_pm_skill.py")
        text = text.replace("pending", "passed")
        path.write_text(text, encoding="utf-8", newline="\n")

    def test_init_project_creates_control_plane(self) -> None:
        result = init_project(self.paths, "demo", "master")
        self.assertTrue(result["ok"])
        self.assertTrue(self.paths.manifest.exists())
        self.assertTrue((self.paths.schemas / "todo.schema.json").exists())
        self.assertTrue((self.root / "README.md").exists())
        self.assertTrue((self.root / "AGENTS.md").exists())
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Project Dev Management", agents)
        self.assertIn("development-policy.yaml", agents)
        self.assertIn("通用协作规则", agents)
        self.assertIn("最小必要改动", agents)
        self.assertIn("不要自动提交", agents)
        audit = self.paths.audit_log.read_text(encoding="utf-8")
        self.assertIn("init_project", audit)

    def test_cli_parser_init_show_status_and_human_work_branches(self) -> None:
        init_result = self.run_cli("init-project", "--project-id", "demo", "--json")
        self.assertTrue(json.loads(init_result.stdout)["ok"])
        status_result = self.run_cli("show-status", "--json")
        status = json.loads(status_result.stdout)
        self.assertTrue(status["ok"])
        self.assertEqual(status["summary"]["manifest"]["project_id"], "demo")
        changelog_result = self.run_cli("add-changelog-entry", "--message", "Docs update", "--category", "文档", "--json")
        self.assertEqual(json.loads(changelog_result.stdout)["category"], "Docs")
        work_result = self.run_cli("list-work-branches")
        self.assertIn("未完成分支工作", work_result.stdout)

    def test_docs_encoding_check_is_available_in_cli_and_policy(self) -> None:
        init_project(self.paths, "demo", "master")
        policy_text = self.paths.policy.read_text(encoding="utf-8")
        self.assertIn("pm-skill check-docs-encoding --json", policy_text)
        direct = check_docs_encoding(self.paths)
        self.assertTrue(direct["ok"])
        self.assertGreater(direct["scanned_files"], 0)
        cli_result = self.run_cli("check-docs-encoding", "--json")
        cli = json.loads(cli_result.stdout)
        self.assertTrue(cli["ok"])

    def test_describe_command_exposes_runtime_effects(self) -> None:
        init_project(self.paths, "demo", "master")
        result = describe_command("create-work-surface")
        self.assertTrue(result["ok"])
        command = result["command"]
        self.assertEqual(command["name"], "create_work_surface")
        self.assertTrue(command["effects"]["write_repo"])
        self.assertTrue(command["effects"]["git_write"])
        self.assertFalse(command["requires_clean_worktree"])

    def test_command_envelope_dispatcher_supports_show_status(self) -> None:
        init_project(self.paths, "demo", "master")
        result = execute_command_envelope(
            self.root,
            {
                "request_id": "req_test",
                "command": "show_status",
                "args": {},
                "actor": "agent",
            },
        )
        self.assertTrue(result["ok"])
        self.assertIn("show_status", supported_commands())
        self.assertIn("create_todo_from_source", supported_commands())
        self.assertIn("create-acceptance-matrix", supported_commands())
        self.assertIn("validate_acceptance", supported_commands())

    def test_mcp_adapter_exposes_core_tool_function(self) -> None:
        from pm_skill.mcp_server import recover_project as mcp_recover_project
        from pm_skill.mcp_server import tool_descriptions

        init_project(self.paths, "demo", "master")
        result = mcp_recover_project(self.root, hydrate_level="minimal")
        self.assertTrue(result["ok"])
        self.assertEqual(result["hydrate_level"], "minimal")
        descriptions = tool_descriptions()
        self.assertTrue(descriptions["ok"])
        self.assertIn("recover_project", descriptions["tools"])
        self.assertIn("input_schema", descriptions["tools"]["recover_project"])

    def test_rest_adapter_create_app_and_command_route(self) -> None:
        from pm_skill.api import create_app

        init_project(self.paths, "demo", "master")
        app = create_app(self.root)
        route_paths = [getattr(route, "path", route) for route in app.routes]
        self.assertIn("/v1/command", route_paths)
        if hasattr(app, "handle"):
            result = app.handle(
                "POST",
                "/v1/command",
                {
                    "request_id": "req_rest",
                    "command": "show_status",
                    "args": {},
                    "actor": "agent",
                },
            )
        else:
            result = execute_command_envelope(
                self.root,
                {
                    "request_id": "req_rest",
                    "command": "show_status",
                    "args": {},
                    "actor": "agent",
                },
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["summary"]["manifest"]["project_id"], "demo")

    def test_onboard_existing_plain_directory(self) -> None:
        app_dir = self.root / "app"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("print('hello')\n", encoding="utf-8")
        result = onboard_project(ProjectPaths(self.root), project_id="legacy-app")
        self.assertTrue(result["ok"])
        self.assertTrue((self.root / ".git").exists())
        self.assertTrue(self.paths.manifest.exists())
        self.assertTrue((self.root / "docs" / "PROJECT_ONBOARDING.md").exists())
        self.assertFalse((self.root / "src" / "pm_skill").exists())
        fingerprints = json.loads((self.paths.index / "file-fingerprints.json").read_text(encoding="utf-8"))
        self.assertIn("app/main.py", fingerprints)

    def test_frontmatter_round_trip_preserves_body(self) -> None:
        target = self.root / "todo" / "TODO-1.md"
        meta = TodoMeta(id="TODO-1", title="Example", status="ready").to_dict()
        write_frontmatter(target, meta, "# Body\n\n- [ ] Work\n")
        loaded, body = read_frontmatter(target)
        self.assertEqual(loaded["id"], "TODO-1")
        self.assertIn("- [ ] Work", body)

    def test_frontmatter_writes_multiline_metadata_as_literal_block(self) -> None:
        target = self.root / "docs" / "requirements" / "drafts" / "REQ-DRAFT-1.md"
        meta = RequirementMeta(
            id="REQ-DRAFT-1",
            title="Draft",
            change_history=[
                {
                    "ts": "2026-05-17T00:00:00+00:00",
                    "event": "body_note",
                    "body": "第一段\n\n第二段\n- 列表项",
                }
            ],
        ).to_dict()
        write_frontmatter(target, meta, "# Draft\n")
        text = target.read_text(encoding="utf-8")
        self.assertIn("body: |", text)
        self.assertIn("  第一段", text)
        self.assertNotIn("\\n", text.split("---", 2)[1])
        loaded, _body = read_frontmatter(target)
        self.assertEqual(loaded["change_history"][0]["body"], "第一段\n\n第二段\n- 列表项")

    def test_recover_project_reports_uninitialized(self) -> None:
        result = recover_project(self.paths)
        self.assertIn("project_not_initialized", result["warnings"])

    def test_list_and_update_todo(self) -> None:
        init_project(self.paths, "demo", "master")
        todo_path = self.paths.todo / "TODO-2026-05-09-001.md"
        write_frontmatter(
            todo_path,
            TodoMeta(
                id="TODO-2026-05-09-001",
                title="Build CLI",
                status="ready",
                priority="P1",
            ).to_dict(),
            "- [ ] Implement\n",
        )
        listed = list_to_do(self.paths, statuses=["ready"], priorities=["P1"])
        self.assertEqual(len(listed["todos"]), 1)
        update_task(self.paths, "TODO-2026-05-09-001", status="blocked", blocked_by=["Need input"])
        meta, _ = read_frontmatter(todo_path)
        self.assertEqual(meta["status"], "blocked")
        self.assertEqual(meta["blocked_by"], ["Need input"])

    def test_create_todo_and_query_audit(self) -> None:
        init_project(self.paths, "demo", "master")
        result = create_todo(self.paths, title="Add audit query", priority="P1")
        self.assertTrue(result["ok"])
        self.assertTrue((self.root / result["path"]).exists())
        listed = list_to_do(self.paths, statuses=["ready"], priorities=["P1"])
        self.assertEqual(listed["todos"][0]["id"], result["todo_id"])
        audit = query_audit(self.paths, command="create_todo", limit=5)
        self.assertEqual(len(audit["events"]), 1)
        self.assertEqual(audit["events"][0]["command"], "create_todo")

    def test_create_and_promote_requirement(self) -> None:
        init_project(self.paths, "demo", "master")
        created = create_requirement(
            self.paths,
            title="Recover state",
            owners=["pm@example.com"],
            acceptance=["Recover command returns JSON"],
        )
        self.assertTrue((self.root / created["path"]).exists())
        promoted = promote_requirement(self.paths, created["requirement_id"], version="0.1.0")
        self.assertTrue(promoted["ok"])
        self.assertTrue((self.root / created["path"]).exists())
        final_path = self.root / promoted["path"]
        self.assertTrue(final_path.exists())
        listed = list_requirements(self.paths, status="approved")
        self.assertEqual(listed["requirements"][0]["status"], "approved")
        self.assertEqual(listed["requirements"][0]["version"], "0.1.0")

    def test_update_draft_requirement(self) -> None:
        init_project(self.paths, "demo", "master")
        created = create_requirement(self.paths, title="Recover state")
        updated = update_requirement(
            self.paths,
            created["requirement_id"],
            title="Recover state reliably",
            owner=["agent"],
            acceptance=["Status command returns JSON"],
            append_body="## Notes\n\nClarified during planning.",
        )
        self.assertTrue(updated["ok"])
        shown = show_requirement(self.paths, created["requirement_id"])
        meta = shown["requirement"]
        self.assertEqual(meta["title"], "Recover state reliably")
        self.assertEqual(meta["owners"], ["agent"])
        self.assertEqual(meta["acceptance"], ["Status command returns JSON"])
        self.assertEqual(meta["change_history"][0]["event"], "updated")

    def test_update_final_requirement_requires_allow_final(self) -> None:
        init_project(self.paths, "demo", "master")
        created = create_requirement(self.paths, title="Recover state")
        promoted = promote_requirement(self.paths, created["requirement_id"], version="0.1.0")
        with self.assertRaises(RuntimeError):
            update_requirement(self.paths, promoted["requirement_id"], title="Nope")

    def test_promote_requirement_slice_keeps_source_draft(self) -> None:
        init_project(self.paths, "demo", "master")
        created = create_requirement(
            self.paths,
            title="User profile features",
            acceptance=["Avatar upload", "Display name editing"],
        )
        promoted = promote_requirement_slice(
            self.paths,
            created["requirement_id"],
            title="Avatar upload only",
            acceptance=["Support png and jpg", "Limit file size to 5MB"],
            source_slice="Avatar upload",
        )
        self.assertTrue(promoted["ok"])
        drafts = list_requirements(self.paths, status="draft")["requirements"]
        finals = list_requirements(self.paths, status="approved")["requirements"]
        self.assertEqual(len(drafts), 1)
        self.assertEqual(len(finals), 1)
        self.assertEqual(finals[0]["source_draft"], created["requirement_id"])
        self.assertEqual(finals[0]["source_slice"], "Avatar upload")
        self.assertEqual(drafts[0]["change_history"][0]["event"], "slice_promoted")

    def test_collection_ids_do_not_collide_with_legacy_files(self) -> None:
        init_project(self.paths, "demo", "master")
        legacy_path = self.paths.requirements_drafts / "REQ-DRAFT-2026-0001-legacy.md"
        write_frontmatter(
            legacy_path,
            RequirementMeta(id="REQ-DRAFT-2026-0001", title="Legacy draft").to_dict(),
            "# Legacy draft\n",
        )
        created = create_requirement(self.paths, title="Collection draft")
        self.assertEqual(created["requirement_id"], "REQ-DRAFT-2026-0002")

    def test_requirement_scan_warns_and_skips_unmanaged_or_invalid_docs(self) -> None:
        init_project(self.paths, "demo", "master")
        created = create_requirement(self.paths, title="Managed draft")
        unmanaged = self.paths.requirements_drafts / "architecture-note.md"
        unmanaged.write_text("# Architecture note\n\nThis is not a managed requirement.\n", encoding="utf-8")
        malformed = self.paths.requirements_final / "broken.md"
        malformed.write_text("---\nrequirements:\n  - `not valid yaml`\n---\n\n# Broken\n", encoding="utf-8")

        status = recover_project(self.paths)
        self.assertTrue(status["ok"])
        self.assertIn(created["requirement_id"], [
            item["id"] for item in list_requirements(self.paths)["requirements"]
        ])
        warnings = list_requirements(self.paths)["warnings"]
        self.assertTrue(any("unmanaged_requirement_document" in item for item in warnings))
        self.assertTrue(any("invalid_requirement_frontmatter" in item for item in warnings))

    def test_delete_final_requirement_removes_related_todos(self) -> None:
        init_project(self.paths, "demo", "master")
        created = create_requirement(self.paths, title="Recover state")
        promoted = promote_requirement(self.paths, created["requirement_id"], version="0.1.0")
        todo = create_todo(
            self.paths,
            title="Implement final requirement",
            source_requirement=promoted["requirement_id"],
        )
        self.assertTrue((self.root / todo["path"]).exists())
        deleted = delete_requirement(self.paths, promoted["requirement_id"])
        self.assertEqual(deleted["removed_todos"], [todo["todo_id"]])
        self.assertFalse((self.root / todo["path"]).exists())
        self.assertEqual(list_requirements(self.paths, status="approved")["requirements"], [])

    def test_add_changelog_entry(self) -> None:
        init_project(self.paths, "demo", "master")
        result = add_changelog_entry(
            self.paths,
            message="完成项目状态恢复命令",
            category="新增",
            requirement_id="REQ-2026-0001",
            todo_id="TODO-2026-05-09-001",
        )
        self.assertTrue(result["ok"])
        changelog = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("### 新增", changelog)
        self.assertIn("完成项目状态恢复命令", changelog)
        self.assertIn("需求: REQ-2026-0001", changelog)
        self.assertIn("任务: TODO-2026-05-09-001", changelog)

    def test_add_changelog_entry_accepts_docs_category(self) -> None:
        init_project(self.paths, "demo", "master")
        result = add_changelog_entry(self.paths, message="更新文档说明", category="文档")
        self.assertEqual(result["category"], "Docs")
        self.assertEqual(result["heading"], "文档")
        changelog = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("### 文档", changelog)
        self.assertIn("更新文档说明", changelog)

    def test_create_todo_from_source_audits_coverage_and_builds_acceptance_flow(self) -> None:
        init_project(self.paths, "demo", "master")
        requirement = create_requirement(
            self.paths,
            title="Import flow",
            acceptance=["支持 CSV 导入", "导入失败要给出错误提示"],
        )
        todo = create_todo_from_source(self.paths, source_requirement=requirement["requirement_id"])
        self.assertTrue(todo["source_coverage_audit"]["ok"])
        todo_text = (self.root / todo["path"]).read_text(encoding="utf-8")
        self.assertIn("支持 CSV 导入", todo_text)
        self.assertIn("导入失败要给出错误提示", todo_text)
        matrix = create_acceptance_matrix(self.paths, todo["todo_id"])
        self.assertTrue(matrix["coverage_audit"]["ok"])
        matrix_text = (self.root / matrix["path"]).read_text(encoding="utf-8")
        self.assertIn("支持 CSV 导入", matrix_text)
        self.assertIn("导入失败要给出错误提示", matrix_text)
        with self.assertRaises(RuntimeError):
            validate_acceptance(self.paths, todo["todo_id"])
        self.mark_acceptance_matrix_passed(matrix["path"])
        validated = validate_acceptance(self.paths, todo["todo_id"])
        self.assertTrue(validated["ok"])
        self.assertTrue(validated["readiness"]["ok"])

    def test_chinese_branch_name_is_used_for_requirement_collection_file(self) -> None:
        subprocess.run(["git", "switch", "-c", "功能-登录"], cwd=self.root, check=True, capture_output=True, text=True)
        init_project(self.paths, "demo", "功能-登录")
        created = create_requirement(self.paths, title="登录功能")
        self.assertEqual(created["path"], "docs/requirements/drafts/功能-登录.md")
        requirement_text = (self.root / "docs" / "requirements" / "drafts" / "功能-登录.md").read_text(encoding="utf-8")
        self.assertIn("# 草案需求集合", requirement_text)
        self.assertIn("### 验收标准", requirement_text)

    def test_todo_defaults_to_current_branch_directory(self) -> None:
        subprocess.run(["git", "switch", "-c", "branch-todo"], cwd=self.root, check=True, capture_output=True, text=True)
        init_project(self.paths, "demo", "master")
        created = create_todo(self.paths, title="Branch task", priority="P1")
        self.assertTrue(created["path"].startswith("todo/branch-todo/"))
        todo_text = (self.root / created["path"]).read_text(encoding="utf-8")
        self.assertIn("明确实现步骤", todo_text)
        self.assertIn("记录版本变更", todo_text)
        listed = list_to_do(self.paths, statuses=["ready"], priorities=["P1"])
        self.assertEqual(len(listed["todos"]), 1)
        self.assertEqual(listed["branch"], "branch-todo")
        self.assertTrue((self.root / created["path"]).exists())

    def test_branch_changelog_is_separate_from_global_changelog(self) -> None:
        subprocess.run(["git", "switch", "-c", "feature-changelog"], cwd=self.root, check=True, capture_output=True, text=True)
        init_project(self.paths, "demo", "master")
        result = add_changelog_entry(self.paths, message="Branch feature done", category="Added")
        self.assertEqual(result["path"], "docs/changelog/feature-changelog.md")
        branch_changelog = (self.root / result["path"]).read_text(encoding="utf-8")
        root_changelog = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("Branch feature done", branch_changelog)
        self.assertNotIn("Branch feature done", root_changelog)

    def test_create_work_surface_creates_branch_requirement_todo_and_started_task(self) -> None:
        init_project(self.paths, "demo", "master")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Tester", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        (self.root / "temp.log").write_text("scratch\n", encoding="utf-8")
        result = create_work_surface(self.paths, title="Login module", acceptance=["Can sign in"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["branch"], "codex/Login-module")
        self.assertTrue(result["branch_created"])
        self.assertEqual(GitClient(self.root).branch(), "codex/Login-module")
        self.assertTrue((self.root / "docs" / "requirements" / "drafts" / "codex-Login-module.md").exists())
        self.assertTrue((self.root / result["todo"]["path"]).exists())
        self.assertIn("todo/codex-Login-module/", result["todo"]["path"])
        self.assertEqual(result["task"]["status"], "in_progress")
        self.assertEqual(result["changelog_path"], "docs/changelog/codex-Login-module.md")
        branches = list_work_branches(self.paths)
        self.assertEqual(len(branches["branches"]), 1)
        self.assertEqual(branches["branches"][0]["branch"], "codex/Login-module")
        self.assertFalse(branches["branches"][0]["completed"])
        self.assertEqual(branches["branches"][0]["todo_counts"]["in_progress"], 1)
        marked = mark_branch_work(self.paths, completed=True, progress_note="登录模块开发完成。")
        self.assertTrue(marked["marker"]["completed"])
        self.assertEqual(marked["marker_path"], ".pm-skill/branches/codex-Login-module.json")
        self.assertEqual(list_work_branches(self.paths)["branches"], [])
        completed = list_work_branches(self.paths, include_completed=True)["branches"]
        self.assertEqual(completed[0]["progress_note"], "登录模块开发完成。")
        human = list_work_branches(self.paths, include_completed=True, human=True)
        self.assertIn("分支工作进展", human["text"])
        self.assertIn("codex/Login-module", human["text"])

    def test_create_work_surface_still_rejects_tracked_changes(self) -> None:
        init_project(self.paths, "demo", "master")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Tester", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        (self.root / "README.md").write_text("changed\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            create_work_surface(self.paths, title="Blocked module")

    def test_update_work_surface_updates_branch_note_todo_and_changelog(self) -> None:
        init_project(self.paths, "demo", "master")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Tester", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        surface = create_work_surface(self.paths, title="Billing module")
        result = update_work_surface(
            self.paths,
            progress_note="Billing API done, tests pending.",
            todo_ids=[surface["todo"]["todo_id"]],
            todo_status="blocked",
            changelog_entry="推进账单模块 API 实现",
            changelog_category="变更",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["marker"]["progress_note"], "Billing API done, tests pending.")
        self.assertEqual(result["updated_todos"][0]["status"], "blocked")
        self.assertEqual(result["changelog"]["path"], "docs/changelog/codex-Billing-module.md")
        self.assertTrue(result["regression_guard"]["created"])
        guard_path = self.root / result["regression_guard"]["path"]
        self.assertTrue(guard_path.exists())
        guard_text = guard_path.read_text(encoding="utf-8")
        self.assertIn("执行测试过程中发现的问题", guard_text)
        self.assertIn("用户提出的问题", guard_text)
        changelog = (self.root / result["changelog"]["path"]).read_text(encoding="utf-8")
        self.assertIn("推进账单模块 API 实现", changelog)

    def test_prepare_release_notes_merges_branch_changelog_to_global(self) -> None:
        subprocess.run(["git", "switch", "-c", "feature-release"], cwd=self.root, check=True, capture_output=True, text=True)
        init_project(self.paths, "demo", "master")
        add_changelog_entry(self.paths, message="完成分支功能", category="新增")
        proposal = prepare_release_notes(self.paths, branch="feature-release")
        self.assertEqual(proposal["mode"], "proposal")
        self.assertEqual(len(proposal["planned_entries"]), 1)
        applied = prepare_release_notes(self.paths, branch="feature-release", apply=True)
        self.assertEqual(applied["mode"], "applied")
        root_changelog = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("【feature-release】完成分支功能", root_changelog)

    def test_prepare_release_blocks_unfinished_branch_work_then_proposes(self) -> None:
        init_project(self.paths, "demo", "master")
        create_todo(self.paths, title="Finish module", priority="P1")
        blocked = prepare_release(self.paths, version="v0.2.0")
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["error"], "unfinished_branch_work")
        self.assertEqual(blocked["unfinished_branches"][0]["todo_counts"]["ready"], 1)
        proposal = prepare_release(self.paths, version="v0.2.0", allow_unfinished=True)
        self.assertTrue(proposal["ok"])
        self.assertEqual(proposal["mode"], "proposal")
        self.assertEqual(proposal["baseline"]["mode"], "proposal")
        self.assertEqual(proposal["baseline"]["version"], "v0.2.0")

    def test_migrate_legacy_todo_moves_root_todo_to_branch_folder(self) -> None:
        init_project(self.paths, "demo", "master")
        legacy_path = self.paths.todo / "TODO-2026-05-10-001.md"
        write_frontmatter(
            legacy_path,
            TodoMeta(id="TODO-2026-05-10-001", title="Legacy", status="ready").to_dict(),
            "# Legacy\n",
        )
        result = migrate_legacy_todo(self.paths, branch="feature-migrate")
        self.assertEqual(result["migrated"][0]["path"], "todo/feature-migrate/TODO-2026-05-10-001.md")
        self.assertFalse(legacy_path.exists())
        meta, _ = read_frontmatter(self.root / result["migrated"][0]["path"])
        self.assertEqual(meta["branch"], "feature-migrate")

    def test_start_task_accepts_explicit_chinese_branch_name(self) -> None:
        init_project(self.paths, "demo", "master")
        todo = create_todo(self.paths, title="实现中文分支", priority="P1")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Tester", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        result = start_task(self.paths, todo["todo_id"], branch_name="功能/中文分支")
        self.assertEqual(result["branch"], "功能/中文分支")
        self.assertEqual(GitClient(self.root).branch(), "功能/中文分支")

    def test_help_guide_mentions_core_commands_and_rules(self) -> None:
        result = help_guide()
        self.assertTrue(result["ok"])
        text = result["text"]
        self.assertIn("init-project", text)
        self.assertIn("create-requirement", text)
        self.assertIn("list-requirements", text)
        self.assertIn("promote-requirement-slice", text)
        self.assertIn("delete-requirement", text)
        self.assertIn("create-todo-from-source", text)
        self.assertIn("create-acceptance-matrix", text)
        self.assertIn("validate-acceptance", text)
        self.assertIn("update-task", text)
        self.assertIn("add-changelog-entry", text)
        self.assertIn("create-work-surface", text)
        self.assertIn("list-work-branches", text)
        self.assertIn("mark-branch-work", text)
        self.assertIn("prepare-release-notes", text)
        self.assertIn("migrate-legacy-todo", text)
        self.assertIn("正式需求开发完成时必须写版本变更记录", text)

    def test_done_task_for_approved_requirement_requires_changelog(self) -> None:
        init_project(self.paths, "demo", "master")
        created = create_requirement(self.paths, title="Recover state")
        promoted = promote_requirement(self.paths, created["requirement_id"], version="0.1.0")
        todo = create_todo(
            self.paths,
            title="Finish approved requirement",
            source_requirement=promoted["requirement_id"],
        )
        with self.assertRaises(RuntimeError):
            update_task(
                self.paths,
                todo["todo_id"],
                status="done",
                changelog_entry="Completed approved recovery requirement",
            )
        matrix = create_acceptance_matrix(self.paths, todo["todo_id"])
        self.assertTrue(matrix["coverage_audit"]["ok"])
        self.mark_acceptance_matrix_passed(matrix["path"])
        done = update_task(
            self.paths,
            todo["todo_id"],
            status="done",
            changelog_entry="Completed approved recovery requirement",
            changelog_category="Added",
        )
        self.assertTrue(done["ok"])
        changelog = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("Completed approved recovery requirement", changelog)
        self.assertIn(promoted["requirement_id"], changelog)

    def test_model_validation_rejects_bad_statuses(self) -> None:
        with self.assertRaises(ValueError):
            TodoMeta(id="TODO-1", title="Bad", status="wat")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            RequirementMeta(id="REQ-1", title="Bad", status="wat")  # type: ignore[arg-type]

    def test_handover_updates_manifest(self) -> None:
        init_project(self.paths, "demo", "master")
        result = handover(self.paths, next_action=["Continue tests"])
        self.assertTrue((self.root / result["handover_path"]).exists())
        manifest = json.loads(self.paths.manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest["latest_handover"], result["handover_path"])

    def test_sync_index_excludes_env(self) -> None:
        init_project(self.paths, "demo", "master")
        (self.root / ".env").write_text("SECRET=1\n", encoding="utf-8")
        (self.root / ".git" / "leaky").write_text("internal\n", encoding="utf-8")
        (self.root / "visible.txt").write_text("hello\n", encoding="utf-8")
        result = sync_index(self.paths)
        self.assertTrue(result["ok"])
        fingerprints = json.loads((self.paths.index / "file-fingerprints.json").read_text(encoding="utf-8"))
        self.assertIn("visible.txt", fingerprints)
        self.assertNotIn(".env", fingerprints)
        self.assertFalse(any(path.startswith(".git/") for path in fingerprints))

    def test_sync_index_uses_manifest_index_scope_paths_and_extensions(self) -> None:
        init_project(self.paths, "demo", "master")
        (self.root / "code").mkdir()
        (self.root / "docs" / "changelog").mkdir(parents=True, exist_ok=True)
        (self.root / "code" / "app.py").write_text("print('hi')\n", encoding="utf-8")
        (self.root / "code" / "notes.md").write_text("# Notes\n", encoding="utf-8")
        (self.root / "code" / "scratch.txt").write_text("skip\n", encoding="utf-8")
        (self.root / "docs" / "changelog" / "m1.md").write_text("# Log\n", encoding="utf-8")
        (self.root / "outside.py").write_text("skip = True\n", encoding="utf-8")
        (self.root / "code" / ".env").write_text("SECRET=1\n", encoding="utf-8")
        manifest = json.loads(self.paths.manifest.read_text(encoding="utf-8"))
        manifest["index_scope"] = {"paths": ["code", "docs/changelog"], "extensions": [".py", ".md"]}
        self.paths.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        result = sync_index(self.paths)
        self.assertTrue(result["ok"])
        self.assertEqual(result["index_scope"]["paths"], ["code", "docs/changelog"])
        fingerprints = json.loads((self.paths.index / "file-fingerprints.json").read_text(encoding="utf-8"))
        self.assertIn("code/app.py", fingerprints)
        self.assertIn("code/notes.md", fingerprints)
        self.assertIn("docs/changelog/m1.md", fingerprints)
        self.assertNotIn("code/scratch.txt", fingerprints)
        self.assertNotIn("outside.py", fingerprints)
        self.assertNotIn("code/.env", fingerprints)

    def test_sync_index_uses_manifest_exclude_scope(self) -> None:
        init_project(self.paths, "demo", "master")
        (self.root / "code" / "generated").mkdir(parents=True)
        (self.root / "code" / "app.py").write_text("print('hi')\n", encoding="utf-8")
        (self.root / "code" / "generated" / "keep.py").write_text("print('keep')\n", encoding="utf-8")
        (self.root / "code" / "generated" / "skip.md").write_text("# generated\n", encoding="utf-8")
        (self.root / "code" / "debug.log").write_text("skip\n", encoding="utf-8")
        (self.root / "notes.md").write_text("# keep\n", encoding="utf-8")
        manifest = json.loads(self.paths.manifest.read_text(encoding="utf-8"))
        manifest["index_scope"] = {"paths": "*", "extensions": "*"}
        manifest["exclude_scope"] = {"paths": ["code/generated"], "extensions": [".md"]}
        self.paths.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        result = sync_index(self.paths)
        self.assertTrue(result["ok"])
        self.assertEqual(result["exclude_scope"]["paths"], ["code/generated"])
        fingerprints = json.loads((self.paths.index / "file-fingerprints.json").read_text(encoding="utf-8"))
        self.assertIn("code/app.py", fingerprints)
        self.assertIn("code/debug.log", fingerprints)
        self.assertNotIn("code/generated/keep.py", fingerprints)
        self.assertNotIn("code/generated/skip.md", fingerprints)
        self.assertNotIn("notes.md", fingerprints)

    def test_exclude_scope_filters_pm_skill_dirty_worktree(self) -> None:
        init_project(self.paths, "demo", "master")
        manifest = json.loads(self.paths.manifest.read_text(encoding="utf-8"))
        manifest["exclude_scope"] = {"paths": ["corpus"], "extensions": [".log"]}
        self.paths.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Tester", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        (self.root / "corpus").mkdir()
        (self.root / "corpus" / "sample.txt").write_text("generated\n", encoding="utf-8")
        (self.root / "run.log").write_text("generated\n", encoding="utf-8")

        result = recover_project(self.paths)
        self.assertFalse(result["physical_state"]["dirty"])
        self.assertEqual(result["physical_state"]["dirty_files"], [])

        (self.root / "src.py").write_text("print('tracked by pm-skill')\n", encoding="utf-8")
        result = recover_project(self.paths)
        self.assertTrue(result["physical_state"]["dirty"])
        self.assertEqual(result["physical_state"]["dirty_files"], ["?? src.py"])

    def test_sync_index_rejects_manifest_index_scope_outside_root(self) -> None:
        init_project(self.paths, "demo", "master")
        manifest = json.loads(self.paths.manifest.read_text(encoding="utf-8"))
        manifest["index_scope"] = {"paths": ["../outside"], "extensions": "*"}
        self.paths.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        with self.assertRaises(RuntimeError):
            sync_index(self.paths)

    def test_sync_index_rejects_manifest_exclude_scope_outside_root(self) -> None:
        init_project(self.paths, "demo", "master")
        manifest = json.loads(self.paths.manifest.read_text(encoding="utf-8"))
        manifest["exclude_scope"] = {"paths": ["../outside"], "extensions": "*"}
        self.paths.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        with self.assertRaises(RuntimeError):
            sync_index(self.paths)

    def test_sync_index_does_not_chase_its_own_refresh_commit(self) -> None:
        init_project(self.paths, "demo", "master")
        (self.root / "visible.txt").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Tester", "-c", "user.email=test@example.com", "commit", "-m", "base"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        base_head = GitClient(self.root).head()
        first = sync_index(self.paths)
        self.assertEqual(first["last_indexed_commit"], base_head)
        fingerprints = json.loads((self.paths.index / "file-fingerprints.json").read_text(encoding="utf-8"))
        self.assertNotIn(".pm-skill/project-manifest.json", fingerprints)

        subprocess.run(
            [
                "git",
                "add",
                ".pm-skill/index",
                ".pm-skill/project-manifest.json",
                ".pm-skill/audit/audit-log.jsonl",
            ],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Tester",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "sync index",
            ],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

        refresh_head = GitClient(self.root).head()
        self.assertNotEqual(refresh_head, base_head)
        recovered = recover_project(self.paths)
        self.assertNotIn("index_stale", recovered["warnings"])
        second = sync_index(self.paths)
        self.assertEqual(second["last_indexed_commit"], base_head)
        fingerprints = json.loads((self.paths.index / "file-fingerprints.json").read_text(encoding="utf-8"))
        self.assertEqual({item["last_seen_commit"] for item in fingerprints.values()}, {base_head})

    def test_get_context_exposes_turn_state_and_router_command(self) -> None:
        init_project(self.paths, "demo", "master")
        req = create_requirement(
            self.paths,
            "Context command",
            acceptance=["CLI supports turn context", "Context includes TODOs"],
        )
        todo = create_todo_from_source(
            self.paths,
            source_requirement=req["requirement_id"],
            title="Build context command",
        )
        create_acceptance_matrix(self.paths, todo["todo_id"])

        result = get_context(self.paths, mode="turn")
        self.assertTrue(result["ok"])
        self.assertIn(todo["todo_id"], result["text"])
        self.assertIn("acceptance_matrices", result["context"])
        self.assertIn("get_context", supported_commands())

        routed = execute_command_envelope(
            self.root,
            {
                "request_id": "req_context",
                "command": "get_context",
                "args": {"mode": "turn"},
                "actor": "agent",
            },
        )
        self.assertTrue(routed["ok"])
        self.assertEqual(routed["context"]["mode"], "turn")

    def test_work_package_creates_prd_and_context_jsonl(self) -> None:
        init_project(self.paths, "demo", "master")
        req = create_requirement(
            self.paths,
            "Work package",
            acceptance=["Create package", "Add verification context"],
        )
        todo = create_todo_from_source(
            self.paths,
            source_requirement=req["requirement_id"],
            title="Build work package",
        )
        package = create_work_package(self.paths, todo["todo_id"])
        package_path = self.root / package["path"]
        self.assertTrue((package_path / "prd.md").exists())
        self.assertTrue((package_path / "implementation-context.jsonl").exists())
        self.assertTrue((package_path / "verification-context.jsonl").exists())
        self.assertTrue((package_path / "research").is_dir())

        context_file = "docs/standards/development-policy.yaml"
        result = add_work_package_context(
            self.paths,
            todo["todo_id"],
            action="verification",
            file=context_file,
            reason="Policy checks define the verification contract.",
        )
        self.assertTrue(result["ok"])
        listed = list_work_packages(self.paths, todo_id=todo["todo_id"])
        self.assertEqual(listed["work_packages"][0]["verification_context"]["entry_count"], 1)

    def test_template_hashes_detect_modified_and_protect_user_data(self) -> None:
        init_project(self.paths, "demo", "master")
        refreshed = refresh_template_hashes(
            self.paths,
            managed_paths=["AGENTS.md", "todo/secret-task.md"],
        )
        self.assertEqual(len(refreshed["records"]), 1)
        self.assertEqual(refreshed["skipped"][0]["reason"], "protected_user_data")
        checked = check_template_hashes(self.paths)
        self.assertEqual(checked["counts"], {"unchanged": 1})
        self.assertIn("docs/requirements/", checked["protected_user_data_paths"])

        agents = self.root / "AGENTS.md"
        agents.write_text(agents.read_text(encoding="utf-8") + "\nUser note\n", encoding="utf-8")
        checked = check_template_hashes(self.paths)
        self.assertEqual(checked["counts"], {"modified": 1})

    def test_git_client_handles_unborn_head(self) -> None:
        git = GitClient(self.root)
        self.assertIsNone(git.head())
        self.assertIn(git.branch(), {"master", "main", "HEAD"})


if __name__ == "__main__":
    unittest.main()
