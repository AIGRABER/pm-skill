from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .frontmatter_io import read_frontmatter, write_frontmatter
from .git_client import GitClient
from .json_io import append_jsonl, read_json, write_json_atomic
from .models import (
    AuditEvent,
    HandoverMeta,
    Manifest,
    RequirementMeta,
    TemplateHashRecord,
    TodoMeta,
    WorkPackageMeta,
    utc_now,
)
from .paths import ProjectPaths
from .policy import DEFAULT_POLICY, excluded_from_index, is_protected_branch, read_policy, write_default_policy
from .runtime import WorkflowRun
from .schemas import schemas
from .scope import (
    exclude_scope_enabled,
    matches_exclude_scope,
    matches_scope,
    normalize_exclude_scope,
    normalize_scope_extensions,
    normalize_scope_paths,
)


SEMVER = re.compile(r"^v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
CHANGELOG_CATEGORY_HEADINGS = {
    "Added": "\u65b0\u589e",
    "Changed": "\u53d8\u66f4",
    "Fixed": "\u4fee\u590d",
    "Removed": "\u79fb\u9664",
    "Deprecated": "\u5e9f\u5f03",
    "Security": "\u5b89\u5168",
    "Docs": "\u6587\u6863",
}
CHANGELOG_CATEGORY_ALIASES = {
    **{key: key for key in CHANGELOG_CATEGORY_HEADINGS},
    "\u65b0\u589e": "Added",
    "\u53d8\u66f4": "Changed",
    "\u4fee\u6539": "Changed",
    "\u4fee\u590d": "Fixed",
    "\u79fb\u9664": "Removed",
    "\u5220\u9664": "Removed",
    "\u5e9f\u5f03": "Deprecated",
    "\u5b89\u5168": "Security",
    "\u6587\u6863": "Docs",
}




DEFAULT_AGENTS_TEXT = '# AGENTS.md\n\n## \u9879\u76ee\u5de5\u4f5c\u89c4\u5219\n\n- \u9ed8\u8ba4\u4f7f\u7528 Project Dev Management \u7ba1\u7406\u9879\u76ee\u72b6\u6001\u3002\n- \u6bcf\u6b21\u5f00\u59cb\u5de5\u4f5c\u5148\u8fd0\u884c `pm-skill show-status --json`\uff1b\u9700\u8981\u6062\u590d\u4e0a\u4e0b\u6587\u65f6\u8fd0\u884c `pm-skill recover-project --json`\u3002\n- \u7528\u6237\u8bf4\u201c\u521b\u5efa\u5de5\u4f5c\u9762\u201d\u201c\u521b\u5efa\u5de5\u4f5c\u76ee\u5f55\u201d\u6216\u201c\u521b\u5efa\u5206\u652f\u76ee\u5f55\u201d\u65f6\uff0c\u8c03\u7528 `pm-skill create-work-surface --title "..." --json`\u3002\n- \u8349\u6848\u9700\u6c42\u3001\u6b63\u5f0f\u9700\u6c42\u3001TODO\u3001\u7248\u672c\u53d8\u66f4\u8bb0\u5f55\u9ed8\u8ba4\u4ee5\u4e2d\u6587\u4e3a\u4e3b\u3002\n- \u65b0\u5de5\u4f5c\u9ed8\u8ba4\u6309 Git \u5206\u652f\u9694\u79bb\uff1a\u9700\u6c42\u96c6\u5408\u3001TODO \u548c\u5206\u652f\u7248\u672c\u53d8\u66f4\u8bb0\u5f55\u8ddf\u968f\u5f53\u524d\u5206\u652f\u3002\n- \u67e5\u770b\u672a\u5b8c\u6210\u5206\u652f\u5de5\u4f5c\u65f6\u8fd0\u884c `pm-skill list-work-branches --json`\uff1b\u5206\u652f\u5de5\u4f5c\u5b8c\u7ed3\u65f6\u8fd0\u884c `pm-skill mark-branch-work --completed --progress-note "..." --json`\u3002\n- \u53d1\u5e03\u524d\u9700\u8981\u6c47\u603b\u5206\u652f\u53d8\u66f4\u65f6\uff0c\u4f18\u5148\u8fd0\u884c `pm-skill prepare-release --json`\uff1b\u786e\u8ba4\u540e\u518d\u4f7f\u7528 `--apply`\u3002\n- \u53d1\u73b0\u65e7\u7684 `todo/*.md` \u65f6\uff0c\u4f7f\u7528 `pm-skill migrate-legacy-todo --branch "<\u76ee\u6807\u5206\u652f>" --json` \u8fc1\u79fb\u5230\u5206\u652f TODO \u76ee\u5f55\u3002\n- \u5b8c\u6210\u6b63\u5f0f\u9700\u6c42\u5173\u8054\u7684 TODO \u65f6\uff0c\u5fc5\u987b\u5199\u7248\u672c\u53d8\u66f4\u8bb0\u5f55\u3002\n- REST/MCP \u5165\u53e3\u5fc5\u987b\u590d\u7528 command envelope\uff0c\u4e0d\u8981\u7ed5\u8fc7 `pm_skill.command_router`\u3001policy\u3001audit \u548c Git \u72b6\u6001\u68c0\u67e5\u3002\n- \u6570\u636e\u6a21\u578b\u4f18\u5148\u7ecf\u8fc7 Pydantic wrapper \u6216\u73b0\u6709 dataclass `from_dict` \u6821\u9a8c\uff0c\u4e0d\u8981\u76f4\u63a5\u4fe1\u4efb\u5916\u90e8 JSON\u3002\n- \u4fee\u6539\u4ee3\u7801\u540e\u8fd0\u884c `pm-skill run-checks --profile default --json`\u3002\n- \u4e0d\u8981\u628a token\u3001\u5bc6\u94a5\u3001`.env` \u5185\u5bb9\u5199\u5165\u9700\u6c42\u3001TODO\u3001handover\u3001changelog \u6216\u7d22\u5f15\u3002\n\n## \u901a\u7528\u534f\u4f5c\u89c4\u5219\n\n- \u4f18\u5148\u7406\u89e3\u73b0\u6709\u4ee3\u7801\u7ed3\u6784\u3001\u547d\u540d\u548c\u98ce\u683c\uff0c\u518d\u505a\u6539\u52a8\u3002\n- \u9ed8\u8ba4\u505a\u6700\u5c0f\u5fc5\u8981\u6539\u52a8\uff0c\u907f\u514d\u65e0\u5173\u91cd\u6784\u548c\u5927\u8303\u56f4\u683c\u5f0f\u5316\u3002\n- \u4e0d\u8981\u56de\u6eda\u7528\u6237\u6216\u5176\u4ed6 agent \u5df2\u7ecf\u505a\u51fa\u7684\u6539\u52a8\uff1b\u9047\u5230\u51b2\u7a81\u5148\u8bf4\u660e\u518d\u5904\u7406\u3002\n- \u5199\u4ee3\u7801\u524d\u786e\u8ba4\u9700\u6c42\u3001TODO \u548c\u5f53\u524d Git \u5206\u652f\u662f\u5426\u5339\u914d\u3002\n- \u65b0\u589e\u529f\u80fd\u8981\u8865\u5145\u5fc5\u8981\u6d4b\u8bd5\uff1b\u4fee bug \u8981\u4f18\u5148\u8865\u56de\u5f52\u6d4b\u8bd5\u3002\n- \u6d89\u53ca\u7528\u6237\u53ef\u89c1\u884c\u4e3a\u3001\u547d\u4ee4\u53c2\u6570\u3001\u6570\u636e\u683c\u5f0f\u6216\u5b89\u5168\u8fb9\u754c\u65f6\uff0c\u540c\u6b65\u66f4\u65b0\u6587\u6863\u3002\n- \u547d\u4ee4\u8f93\u51fa\u3001\u6587\u6863\u3001\u9700\u6c42\u3001TODO \u548c\u7248\u672c\u53d8\u66f4\u9ed8\u8ba4\u4f7f\u7528\u4e2d\u6587\uff0c\u4ee3\u7801\u6807\u8bc6\u7b26\u9075\u5faa\u9879\u76ee\u539f\u6709\u8bed\u8a00\u548c\u98ce\u683c\u3002\n- \u4e0d\u8981\u81ea\u52a8\u63d0\u4ea4\u3001\u63a8\u9001\u3001\u53d1\u5e03\u6216\u521b\u5efa\u8fdc\u7aef PR\uff0c\u9664\u975e\u7528\u6237\u660e\u786e\u8981\u6c42\u3002\n- \u64cd\u4f5c\u9ad8\u98ce\u9669\u547d\u4ee4\u524d\u5148\u8bf4\u660e\u5f71\u54cd\u8303\u56f4\uff1b\u7981\u6b62\u4f7f\u7528\u7834\u574f\u6027 Git \u547d\u4ee4\u6e05\u7406\u672a\u77e5\u6539\u52a8\u3002\n- \u5b8c\u6210\u9636\u6bb5\u6027\u5de5\u4f5c\u65f6\uff0c\u8bf4\u660e\u6539\u52a8\u6587\u4ef6\u3001\u9a8c\u8bc1\u547d\u4ee4\u548c\u5269\u4f59\u98ce\u9669\u3002\n\n## \u673a\u5668\u53ef\u6267\u884c\u7b56\u7565\n\n\u53ef\u6267\u884c\u7b56\u7565\u653e\u5728 `docs/standards/development-policy.yaml`\uff0c\u5305\u62ec\u53d7\u4fdd\u62a4\u5206\u652f\u3001\u68c0\u67e5\u547d\u4ee4\u3001\u5206\u652f\u547d\u540d\u3001\u7d22\u5f15\u6392\u9664\u548c handover \u7b56\u7565\u3002\n'

CLEAN_USAGE_TEXT = """# Project Development Management Skill

这是一个本地优先的通用项目开发管理 Skill/Sidecar。它把项目状态放在仓库里：`.pm-skill/` 是机器可读控制面，`docs/requirements/`、`todo/`、`docs/handover/`、`CHANGELOG.md` 是人可读工作面，所有写操作都会进入 audit 日志。

## 快速开始

```powershell
pm-skill show-status --json
pm-skill recover-project --json
pm-skill create-work-surface --title "登录模块" --json
pm-skill update-work-surface --progress-note "登录接口已经完成，正在补测试" --json
pm-skill check-docs-encoding --json
pm-skill run-checks --profile default --json
```

## 常用命令

- `init-project`: 初始化项目管理控制面。
- `onboard-project`: 将已有目录接入项目管理。
- `show-status`: 查看当前项目状态摘要。
- `recover-project`: 恢复项目上下文。
- `create-work-surface`: 创建分支感知的需求、TODO 和任务。
- `update-work-surface`: 同步分支进展、TODO 状态和版本变更。
- `create-requirement`: 创建草案需求。
- `list-requirements`: 查看需求集合。
- `promote-requirement-slice`: 将草案的一部分转成正式需求。
- `delete-requirement`: 删除需求并清理相关 TODO。
- `create-todo-from-source`: 从文档、正式需求或草案需求生成 TODO，并审计来源覆盖。
- `create-acceptance-matrix`: 从 TODO 生成验收矩阵，并审计矩阵覆盖 TODO。
- `validate-acceptance`: 对照验收矩阵执行验收，可同时运行检查命令。
- `update-task`: 更新 TODO 状态和进展。
- `add-changelog-entry`: 追加版本变更记录。
- `list-work-branches`: 查看未完成分支工作。
- `mark-branch-work`: 标记分支工作完成或重新打开。
- `prepare-release-notes`: 生成分支 changelog 汇总提案。
- `prepare-release`: 汇总分支变更并准备发布提案。
- `migrate-legacy-todo`: 迁移旧版根目录 TODO。
- `check-docs-encoding`: 检查 Markdown 文档中的编码和 mojibake 问题。

正式需求开发完成时必须写版本变更记录。
"""

HELP_TEXT = CLEAN_USAGE_TEXT
DEFAULT_README_TEXT = CLEAN_USAGE_TEXT


def _rel(paths: ProjectPaths, path: Path) -> str:
    return path.resolve().relative_to(paths.root.resolve()).as_posix()


def _slug(text: str) -> str:
    lowered = text.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return cleaned[:48] or "task"


def _branch_name_from_title(title: str) -> str:
    safe = _branch_slug(title).replace(" ", "-")
    safe = re.sub(r"-+", "-", safe).strip("-")
    return f"codex/{safe or _slug(title)}"


def _branch_slug(branch: str) -> str:
    # Keep human-readable branch names, including Chinese. Replace only characters
    # that cannot safely be used in a Windows/macOS/Linux filename.
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", branch).strip(" .-")
    return safe or "detached"


def _current_branch(paths: ProjectPaths) -> str:
    return GitClient(paths.root).branch()


def _requirement_collection_path(paths: ProjectPaths, status: str) -> Path:
    branch = _branch_slug(_current_branch(paths))
    base = paths.requirements_drafts if status == "draft" else paths.requirements_final
    return base / f"{branch}.md"


def _branch_todo_dir(paths: ProjectPaths, branch: str | None = None) -> Path:
    return paths.todo / _branch_slug(branch or _current_branch(paths))


def _iter_todo_paths(paths: ProjectPaths, scope: str = "branch", branch: str | None = None) -> list[Path]:
    if scope not in {"branch", "all", "legacy"}:
        raise RuntimeError(f"Invalid TODO scope: {scope}")
    paths.todo.mkdir(parents=True, exist_ok=True)
    root_todos = sorted(paths.todo.glob("*.md"))
    if scope == "legacy":
        return root_todos
    if scope == "all":
        return sorted(paths.todo.rglob("*.md"))
    branch_dir = _branch_todo_dir(paths, branch)
    return sorted(branch_dir.glob("*.md")) + root_todos


def _is_default_or_protected_branch(paths: ProjectPaths, branch: str) -> bool:
    manifest = _load_manifest(paths)
    policy = read_policy(paths)
    return branch == manifest.default_branch or is_protected_branch(branch, policy)


def _changelog_path(paths: ProjectPaths, scope: str = "branch", branch: str | None = None) -> Path:
    if scope not in {"branch", "global"}:
        raise RuntimeError(f"Invalid changelog scope: {scope}")
    if scope == "global":
        return paths.root / "CHANGELOG.md"
    resolved_branch = branch or _current_branch(paths)
    if _is_default_or_protected_branch(paths, resolved_branch):
        return paths.root / "CHANGELOG.md"
    return paths.changelog / f"{_branch_slug(resolved_branch)}.md"


def _branch_marker_path(paths: ProjectPaths, branch: str) -> Path:
    return paths.branches / f"{_branch_slug(branch)}.json"


def _read_branch_marker(paths: ProjectPaths, branch: str) -> dict[str, Any]:
    path = _branch_marker_path(paths, branch)
    data = read_json(path) if path.exists() else {}
    return {
        "branch": branch,
        "status": data.get("status", "active"),
        "completed": bool(data.get("completed", False)),
        "progress_note": data.get("progress_note"),
        "updated_at": data.get("updated_at"),
    }


def _write_branch_marker(
    paths: ProjectPaths,
    branch: str,
    completed: bool,
    status: str | None = None,
    progress_note: str | None = None,
) -> dict[str, Any]:
    paths.branches.mkdir(parents=True, exist_ok=True)
    marker = {
        "branch": branch,
        "status": status or ("completed" if completed else "active"),
        "completed": completed,
        "progress_note": progress_note,
        "updated_at": utc_now(),
    }
    write_json_atomic(_branch_marker_path(paths, branch), marker)
    return marker


def _load_requirement_collection(paths: ProjectPaths, status: str) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
    target = _requirement_collection_path(paths, status)
    if not target.exists():
        meta = {
            "kind": "requirement_collection",
            "status": status,
            "branch": GitClient(paths.root).branch(),
            "requirements": [],
            "updated_at": utc_now(),
        }
        return target, meta, []
    meta, _body = read_frontmatter(target)
    requirements = meta.get("requirements") or []
    if not isinstance(requirements, list):
        raise RuntimeError(f"Invalid requirement collection: {target}")
    return target, meta, requirements


def _save_requirement_collection(
    path: Path,
    meta: dict[str, Any],
    requirements: list[dict[str, Any]],
) -> None:
    meta["requirements"] = requirements
    meta["updated_at"] = utc_now()
    collection_title = "草案需求集合" if meta.get("status") == "draft" else "正式需求集合"
    body = f"# {collection_title}\n\n"
    for item in requirements:
        req = RequirementMeta.from_dict(item)
        body += f"## {req.id}: {req.title}\n\n"
        body += f"- 状态: {req.status}\n"
        if req.version:
            body += f"- 版本: {req.version}\n"
        if req.owners:
            body += f"- 负责人: {', '.join(req.owners)}\n"
        if req.source_draft:
            body += f"- 来源草案: {req.source_draft}\n"
        if req.source_slice:
            body += f"- 来源片段: {req.source_slice}\n"
        body += "\n### 验收标准\n\n"
        if req.acceptance:
            body += "\n".join(f"- {item}" for item in req.acceptance) + "\n\n"
        else:
            body += "- 待补充\n\n"
    write_frontmatter(path, meta, body)


def _next_requirement_id(requirements: list[dict[str, Any]], status: str) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"REQ-DRAFT-{year}-" if status == "draft" else f"REQ-{year}-"
    max_seen = 0
    for item in requirements:
        req_id = str(item.get("id", ""))
        if req_id.startswith(prefix):
            suffix = req_id.removeprefix(prefix)
            if suffix.isdigit():
                max_seen = max(max_seen, int(suffix))
    return f"{prefix}{max_seen + 1:04d}"


def _next_global_requirement_id(
    paths: ProjectPaths,
    requirements: list[dict[str, Any]],
    status: str,
) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"REQ-DRAFT-{year}-" if status == "draft" else f"REQ-{year}-"
    max_seen = 0
    for item in requirements:
        req_id = str(item.get("id", ""))
        if req_id.startswith(prefix):
            suffix = req_id.removeprefix(prefix)
            if suffix.isdigit():
                max_seen = max(max_seen, int(suffix))
    for item in _read_all_requirements(paths, warnings=[]):
        req_id = item["meta"].id
        if req_id.startswith(prefix):
            suffix = req_id.removeprefix(prefix)
            if suffix.isdigit():
                max_seen = max(max_seen, int(suffix))
    return f"{prefix}{max_seen + 1:04d}"


def _load_manifest(paths: ProjectPaths) -> Manifest:
    data = read_json(paths.manifest)
    if not data:
        raise RuntimeError("Project is not initialized. Run pm-skill init-project first.")
    return Manifest.from_dict(data)


def _manifest_exclude_scope(paths: ProjectPaths, manifest: Manifest | None) -> tuple[list[str] | None, set[str] | None]:
    if not manifest:
        return [], set()
    return normalize_exclude_scope(paths, manifest.exclude_scope.paths, manifest.exclude_scope.extensions)


def _git_dirty_files(paths: ProjectPaths, git: GitClient, manifest: Manifest | None, include_untracked: bool = True) -> list[str]:
    exclude_paths, exclude_extensions = _manifest_exclude_scope(paths, manifest)
    return git.status_porcelain(
        include_untracked=include_untracked,
        exclude_paths=exclude_paths,
        exclude_extensions=exclude_extensions,
    )


def _save_manifest(paths: ProjectPaths, manifest: Manifest) -> None:
    manifest.updated_at = utc_now()
    write_json_atomic(paths.manifest, manifest.to_dict())


def _is_git_repo(path: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path,
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def _commit_ref(path: Path, ref: str) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", ref],
        cwd=path,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _commit_changed_files(paths: ProjectPaths, ref: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", ref],
        cwd=paths.root,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return set()
    return set(result.stdout.splitlines())


def _is_index_refresh_path(path: str) -> bool:
    return (
        path.startswith(".pm-skill/index/")
        or path.startswith(".pm-skill/audit/")
        or path == ".pm-skill/project-manifest.json"
    )


def _commit_includes_index_refresh(paths: ProjectPaths, previous_head: str, head: str) -> bool:
    parent = _commit_ref(paths.root, f"{head}^")
    if parent != previous_head:
        return False
    changed = _commit_changed_files(paths, head)
    return bool(changed) and all(_is_index_refresh_path(path) for path in changed)


def _index_target_commit(
    paths: ProjectPaths,
    head: str | None,
    manifest: Manifest | None = None,
) -> str | None:
    if not head:
        return None
    if not manifest or not manifest.last_indexed_commit:
        return head
    previous = manifest.last_indexed_commit
    if previous != head and _commit_includes_index_refresh(paths, previous, head):
        return previous
    return head


def _last_commit_summary_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    for line in reversed(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            return None
        return item.get("commit")
    return None


def _audit(
    paths: ProjectPaths,
    command: str,
    args: dict[str, Any],
    ok: bool = True,
    error: str | None = None,
    actor: str = "agent",
    session_id: str = "local",
    approval: str = "not_required",
    before_ref: str | None = None,
    after_ref: str | None = None,
) -> None:
    digest = hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    event = AuditEvent(
        ts=utc_now(),
        actor=actor,
        session_id=session_id,
        command=command,
        args_digest=digest,
        approval=approval,
        before_ref=before_ref,
        after_ref=after_ref,
        ok=ok,
        error=error,
    )
    payload = event.to_dict()
    payload.update(
        {
            "event_type": "command_completed" if ok else "command_failed",
            "request_id": session_id or "local",
            "target": GitClient(paths.root).branch() if (paths.root / ".git").exists() else str(paths.root),
            "details": {"args_keys": sorted(args)},
        }
    )
    append_jsonl(paths.audit_log, payload)


def export_schemas(paths: ProjectPaths) -> dict[str, Any]:
    paths.schemas.mkdir(parents=True, exist_ok=True)
    written = []
    for name, schema in schemas().items():
        write_json_atomic(paths.schemas / name, schema)
        written.append(f".pm-skill/schemas/{name}")
    return {"ok": True, "written": written}


def help_guide() -> dict[str, Any]:
    return {"ok": True, "text": HELP_TEXT}


def init_project(
    paths: ProjectPaths,
    project_id: str,
    default_branch: str,
    force: bool = False,
    display_name: str | None = None,
    create_package_dirs: bool = False,
) -> dict[str, Any]:
    if paths.pm.exists() and not force:
        raise RuntimeError(".pm-skill already exists. Pass --force to overwrite managed files.")

    directories = [
        paths.pm,
        paths.schemas,
        paths.index,
        paths.audit,
        paths.pm / "cache",
        paths.branches,
        paths.requirements_drafts,
        paths.requirements_final,
        paths.handover,
        paths.changelog,
        paths.adr,
        paths.todo,
        paths.skill,
    ]
    if create_package_dirs:
        directories.extend([paths.root / "src" / "pm_skill", paths.root / "tests"])
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    manifest = Manifest(
        project_id=project_id,
        repo_uid=f"local:{paths.root.as_posix()}",
        display_name=display_name or project_id,
        default_branch=default_branch,
    )
    write_json_atomic(paths.manifest, manifest.to_dict())
    write_default_policy(paths)
    export_schemas(paths)

    write_json_atomic(paths.index / "file-fingerprints.json", {})
    write_json_atomic(
        paths.index / "semantic-index-manifest.json",
        {"mode": "summary_only", "last_built_at": None, "items": []},
    )
    (paths.index / "commit-summaries.jsonl").write_text("", encoding="utf-8")
    (paths.audit / "audit-log.jsonl").write_text("", encoding="utf-8")

    _write_static_docs(paths)
    _audit(paths, "init_project", {"project_id": project_id, "default_branch": default_branch})
    return {"ok": True, "project_id": project_id, "root": str(paths.root)}


def onboard_project(
    input_paths: ProjectPaths,
    project_id: str | None = None,
    default_branch: str | None = None,
    display_name: str | None = None,
    init_git: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    target = input_paths.root.resolve()
    if not target.exists() or not target.is_dir():
        raise RuntimeError(f"Project path must be an existing directory: {target}")
    if not _is_git_repo(target):
        if not init_git:
            raise RuntimeError("Target directory is not a Git repository. Pass --init-git to initialize it.")
        subprocess.run(["git", "init"], cwd=target, text=True, capture_output=True, check=True)

    paths = ProjectPaths.discover(target)
    git = GitClient(paths.root)
    branch = git.branch()
    resolved_project_id = project_id or _slug(paths.root.name)
    resolved_branch = default_branch or (branch if branch != "HEAD" else "master")
    initialized = False
    if not paths.manifest.exists() or force:
        init_project(
            paths,
            project_id=resolved_project_id,
            default_branch=resolved_branch,
            force=force,
            display_name=display_name or paths.root.name,
            create_package_dirs=False,
        )
        initialized = True

    index_result = sync_index(paths, scope="all")
    report_path = _write_onboarding_report(paths, initialized, index_result)
    _audit(
        paths,
        "onboard_project",
        {
            "project_id": resolved_project_id,
            "initialized": initialized,
            "input_path": str(target),
            "report": report_path,
        },
    )
    return {
        "ok": True,
        "root": str(paths.root),
        "project_id": resolved_project_id,
        "initialized": initialized,
        "git_branch": git.branch(),
        "indexed_files": index_result["indexed_files"],
        "report_path": report_path,
    }


def recover_project(paths: ProjectPaths, hydrate_level: str = "standard") -> dict[str, Any]:
    git = GitClient(paths.root)
    warnings: list[str] = []
    manifest: Manifest | None = None
    policy = read_policy(paths)
    if not paths.manifest.exists():
        warnings.append("project_not_initialized")
    else:
        manifest = _load_manifest(paths)
        expected_uid = f"local:{paths.root.as_posix()}"
        if manifest.repo_uid != expected_uid:
            raise RuntimeError(
                f"Repository identity mismatch: manifest has {manifest.repo_uid}, current is {expected_uid}"
            )

    head = git.head()
    branch = git.branch()
    exclude_paths, exclude_extensions = _manifest_exclude_scope(paths, manifest)
    dirty_files = git.status_porcelain(
        exclude_paths=exclude_paths,
        exclude_extensions=exclude_extensions,
    )
    if dirty_files:
        warnings.append("dirty_worktree")
    stale = False
    if manifest and manifest.last_indexed_commit and head and manifest.last_indexed_commit != head:
        stale = not (
            not dirty_files
            and _commit_includes_index_refresh(paths, manifest.last_indexed_commit, head)
        )
        if stale:
            warnings.append("index_stale")
    if manifest and not manifest.latest_handover:
        warnings.append("missing_handover")

    todos = _read_all_todos(paths)
    requirement_warnings: list[str] = []
    requirements = _read_all_requirements(paths, warnings=requirement_warnings)
    warnings.extend(requirement_warnings)
    handovers = _read_all_handovers(paths)
    active_todos = [
        item for item in todos if item["meta"].status in {"ready", "in_progress", "blocked"}
    ]

    next_actions = []
    if not manifest:
        next_actions.append("Run init-project to create the repository control plane.")
    if stale:
        next_actions.append("Run sync-index to refresh file fingerprints and commit summaries.")
    if not handovers:
        next_actions.append("Run handover before pausing work so the next session can resume.")

    return {
        "ok": True,
        "hydrate_level": hydrate_level,
        "physical_state": {
            "root": str(paths.root),
            "branch": branch,
            "head": head,
            "dirty": bool(dirty_files),
            "dirty_files": dirty_files,
            "protected_branch": is_protected_branch(branch, policy),
        },
        "project_state": {
            "manifest": manifest.to_dict() if manifest else None,
            "todo_counts": _count_by_status([item["meta"] for item in todos]),
            "active_todos": [_todo_summary(item) for item in active_todos],
            "requirement_counts": _count_by_status([item["meta"] for item in requirements]),
            "latest_handover": manifest.latest_handover if manifest else None,
            "handover_count": len(handovers),
            "stale": stale,
        },
        "warnings": warnings,
        "next_actions": next_actions,
    }


def show_status(paths: ProjectPaths) -> dict[str, Any]:
    result = recover_project(paths, hydrate_level="minimal")
    work_branches = list_work_branches(paths)["branches"] if paths.manifest.exists() else []
    return {
        "ok": True,
        "physical_state": result["physical_state"],
        "summary": result["project_state"],
        "work_branches": work_branches,
        "warnings": result["warnings"],
        "next_actions": result["next_actions"],
    }


PM_SKILL_MANAGED_BLOCK_START = "<!-- PM-SKILL:START -->"
PM_SKILL_MANAGED_BLOCK_END = "<!-- PM-SKILL:END -->"


def _acceptance_matrix_summaries(paths: ProjectPaths, branch: str, todos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for todo in todos:
        todo_id = todo["id"]
        matrix_path = _acceptance_matrix_path(paths, branch, todo_id)
        if not matrix_path.exists():
            summaries.append({"todo_id": todo_id, "exists": False, "path": _rel(paths, matrix_path)})
            continue
        summaries.append(
            {
                "todo_id": todo_id,
                "exists": True,
                "path": _rel(paths, matrix_path),
                "coverage": _audit_acceptance_matrix_coverage(paths, todo_id, matrix_path),
                "readiness": _audit_acceptance_matrix_readiness(matrix_path),
            }
        )
    return summaries


def _spec_index_summaries(paths: ProjectPaths) -> list[dict[str, str]]:
    candidates = []
    standards = paths.docs / "standards"
    if standards.exists():
        candidates.extend(sorted(standards.rglob("*.md")))
        candidates.extend(sorted(standards.rglob("*.yaml")))
        candidates.extend(sorted(standards.rglob("*.yml")))
    skill_usage = paths.skill / "USAGE.md"
    if skill_usage.exists():
        candidates.append(skill_usage)
    result = []
    seen: set[str] = set()
    for path in candidates:
        rel = _rel(paths, path)
        if rel not in seen:
            seen.add(rel)
            result.append({"path": rel, "kind": _kind_for_path(rel)})
    return result


def _format_context_text(context: dict[str, Any]) -> str:
    physical = context["physical_state"]
    lines = [
        f"当前分支：{physical['branch']}",
        f"工作区：{'dirty' if physical['dirty'] else 'clean'}",
    ]
    if context["warnings"]:
        lines.append("警告：" + ", ".join(context["warnings"]))
    if context["todos"]:
        lines.append("当前分支 TODO：")
        for todo in context["todos"]:
            lines.append(f"- {todo['id']} [{todo['status']}/{todo['priority']}] {todo['title']}")
    else:
        lines.append("当前分支 TODO：无")
    if context["next_actions"]:
        lines.append("下一步建议：")
        for action in context["next_actions"]:
            lines.append(f"- {action}")
    return "\n".join(lines)


def _work_package_dir(paths: ProjectPaths, branch: str, todo_id: str) -> Path:
    return paths.work_packages / _branch_slug(branch) / _branch_slug(todo_id)


def _write_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text, encoding="utf-8", newline="\n")


def _context_seed(action: str) -> str:
    seed = {
        "_example": f"添加 {action} 所需的规范、研究或验收文件路径和原因；不要放密钥或 .env 内容。"
    }
    return json.dumps(seed, ensure_ascii=False) + "\n"


def _work_package_prd(paths: ProjectPaths, todo: dict[str, Any], requirement: dict[str, Any] | None) -> str:
    meta: TodoMeta = todo["meta"]
    lines = [
        f"# {meta.title}",
        "",
        f"- TODO: {meta.id}",
        f"- 分支: {meta.branch or _current_branch(paths)}",
        f"- 来源需求: {meta.source_requirement or '无'}",
        "",
        "## TODO 内容",
        "",
        todo["body"].strip(),
        "",
    ]
    if requirement:
        req: RequirementMeta = requirement["meta"]
        lines.extend(
            [
                "## 来源需求验收标准",
                "",
                *[f"- {item}" for item in req.acceptance],
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _normalize_context_file(paths: ProjectPaths, file: str) -> str:
    rel = _normalize_repo_path(file)
    if _looks_secret_path(rel):
        raise RuntimeError("Context files must not point to secrets or .env files.")
    target = paths.root / rel
    if not target.exists() or not target.is_file():
        raise RuntimeError(f"Context file does not exist: {rel}")
    return rel


def _work_package_summaries(
    paths: ProjectPaths,
    branch: str | None = None,
    todo_id: str | None = None,
) -> list[dict[str, Any]]:
    base = paths.work_packages / _branch_slug(branch) if branch else paths.work_packages
    if not base.exists():
        return []
    summaries = []
    for package_path in sorted(base.rglob("package.json")):
        data = read_json(package_path)
        if not data:
            continue
        package = WorkPackageMeta.from_dict(data)
        if todo_id and package.todo_id != todo_id:
            continue
        root = package_path.parent
        summaries.append(
            {
                **package.to_dict(),
                "path": _rel(paths, root),
                "prd": _rel(paths, root / "prd.md"),
                "implementation_context": _context_jsonl_summary(root / "implementation-context.jsonl"),
                "verification_context": _context_jsonl_summary(root / "verification-context.jsonl"),
            }
        )
    return summaries


def _context_jsonl_summary(path: Path) -> dict[str, Any]:
    entries = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if "file" in item:
                entries.append(item)
    return {"path": path.name, "entries": entries, "entry_count": len(entries)}


def _normalize_repo_path(path: str) -> str:
    value = path.strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    if not value or value.startswith("../") or Path(value).is_absolute():
        raise RuntimeError(f"Path must be repository-relative: {path}")
    return value


def _looks_secret_path(path: str) -> bool:
    lower = path.lower()
    return lower == ".env" or lower.endswith("/.env") or "secret" in lower or "token" in lower


def _default_managed_template_paths(paths: ProjectPaths) -> list[str]:
    candidates = [
        "README.md",
        "AGENTS.md",
        ".codex/skills/project-dev-management/SKILL.md",
        ".codex/skills/project-dev-management/USAGE.md",
        "docs/standards/development-policy.yaml",
    ]
    return [path for path in candidates if (paths.root / path).exists()]


def _protected_user_data_paths() -> list[str]:
    return [
        "docs/requirements/",
        "todo/",
        "docs/acceptance/",
        "docs/handover/",
        "docs/changelog/",
        "CHANGELOG.md",
    ]


def _is_protected_user_data_path(path: str) -> bool:
    protected = _protected_user_data_paths()
    return any(path == item.rstrip("/") or path.startswith(item) for item in protected)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_context(paths: ProjectPaths, mode: str = "turn") -> dict[str, Any]:
    if mode not in {"turn", "full"}:
        raise RuntimeError(f"Invalid context mode: {mode}")
    status = show_status(paths)
    branch = status["physical_state"]["branch"]
    todos = list_to_do(paths, scope="branch", branch=branch).get("todos", [])
    linked_requirement_ids = sorted(
        {
            todo.get("source_requirement")
            for todo in todos
            if todo.get("source_requirement")
        }
    )
    requirements = [
        item for item in list_requirements(paths).get("requirements", [])
        if item.get("id") in linked_requirement_ids
    ]
    matrices = _acceptance_matrix_summaries(paths, branch, todos)
    work_packages = _work_package_summaries(paths, branch=branch)
    context = {
        "mode": mode,
        "physical_state": status["physical_state"],
        "warnings": status["warnings"],
        "next_actions": status["next_actions"],
        "todos": todos if mode == "full" else todos[:5],
        "requirements": requirements,
        "acceptance_matrices": matrices,
        "work_packages": work_packages,
        "spec_indexes": _spec_index_summaries(paths),
    }
    text = _format_context_text(context)
    _audit(paths, "get_context", {"mode": mode})
    return {"ok": True, "context": context, "text": text}


def create_work_package(paths: ProjectPaths, todo_id: str) -> dict[str, Any]:
    item = _find_todo(paths, todo_id)
    meta: TodoMeta = item["meta"]
    branch = meta.branch or _current_branch(paths)
    target = _work_package_dir(paths, branch, todo_id)
    target.mkdir(parents=True, exist_ok=True)
    requirement = _find_requirement(paths, meta.source_requirement)
    package = WorkPackageMeta(
        todo_id=todo_id,
        title=meta.title,
        branch=branch,
        requirement_id=meta.source_requirement,
        meta={
            "requirement_title": requirement["meta"].title if requirement else None,
            "todo_path": _rel(paths, item["path"]),
        },
    )
    write_json_atomic(target / "package.json", package.to_dict())
    (target / "research").mkdir(exist_ok=True)
    _write_if_missing(target / "implementation-context.jsonl", _context_seed("implementation"))
    _write_if_missing(target / "verification-context.jsonl", _context_seed("verification"))
    _write_if_missing(
        target / "prd.md",
        _work_package_prd(paths, item, requirement),
    )
    _audit(paths, "create_work_package", {"todo_id": todo_id, "path": _rel(paths, target)})
    return {
        "ok": True,
        "todo_id": todo_id,
        "path": _rel(paths, target),
        "package": package.to_dict(),
    }


def add_work_package_context(
    paths: ProjectPaths,
    todo_id: str,
    action: str,
    file: str,
    reason: str,
) -> dict[str, Any]:
    if action not in {"implementation", "verification"}:
        raise RuntimeError(f"Invalid work package context action: {action}")
    if not reason.strip():
        raise RuntimeError("Context reason is required.")
    item = _find_todo(paths, todo_id)
    branch = item["meta"].branch or _current_branch(paths)
    package_dir = _work_package_dir(paths, branch, todo_id)
    if not (package_dir / "package.json").exists():
        create_work_package(paths, todo_id)
    rel_file = _normalize_context_file(paths, file)
    path = package_dir / f"{action}-context.jsonl"
    entry = {
        "file": rel_file,
        "reason": reason.strip(),
        "added_at": utc_now(),
    }
    append_jsonl(path, entry)
    _audit(
        paths,
        "add_work_package_context",
        {"todo_id": todo_id, "action": action, "file": rel_file},
    )
    return {"ok": True, "todo_id": todo_id, "action": action, "entry": entry, "path": _rel(paths, path)}


def list_work_packages(paths: ProjectPaths, todo_id: str | None = None) -> dict[str, Any]:
    packages = _work_package_summaries(paths, todo_id=todo_id)
    return {"ok": True, "work_packages": packages}


def refresh_template_hashes(paths: ProjectPaths, managed_paths: list[str] | None = None) -> dict[str, Any]:
    targets = managed_paths or _default_managed_template_paths(paths)
    records: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for rel_path in targets:
        normalized = _normalize_repo_path(rel_path)
        if _is_protected_user_data_path(normalized):
            skipped.append({"path": normalized, "reason": "protected_user_data"})
            continue
        target = paths.root / normalized
        if not target.exists() or not target.is_file():
            skipped.append({"path": normalized, "reason": "missing"})
            continue
        record = TemplateHashRecord(path=normalized, sha256=_file_sha256(target))
        records.append(record.to_dict())
    manifest = {"version": 1, "updated_at": utc_now(), "records": records}
    write_json_atomic(paths.template_hashes, manifest)
    _audit(paths, "refresh_template_hashes", {"managed_paths": targets, "skipped": skipped})
    return {"ok": True, "path": _rel(paths, paths.template_hashes), "records": records, "skipped": skipped}


def check_template_hashes(paths: ProjectPaths) -> dict[str, Any]:
    data = read_json(paths.template_hashes, default={"records": []}) or {"records": []}
    records = [TemplateHashRecord.from_dict(item) for item in data.get("records") or []]
    checked: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    protected_paths = _protected_user_data_paths()
    for record in records:
        target = paths.root / record.path
        if not target.exists():
            status = "missing"
            current_hash = None
        else:
            current_hash = _file_sha256(target)
            status = "unchanged" if current_hash == record.sha256 else "modified"
        counts[status] = counts.get(status, 0) + 1
        checked.append(
            {
                "path": record.path,
                "status": status,
                "expected_sha256": record.sha256,
                "current_sha256": current_hash,
                "managed": record.managed,
            }
        )
    result = {
        "ok": True,
        "manifest_path": _rel(paths, paths.template_hashes) if paths.template_hashes.exists() else None,
        "counts": counts,
        "files": checked,
        "protected_user_data_paths": protected_paths,
        "managed_block_markers": {
            "start": PM_SKILL_MANAGED_BLOCK_START,
            "end": PM_SKILL_MANAGED_BLOCK_END,
        },
    }
    _audit(paths, "check_template_hashes", {})
    return result


def list_work_branches(paths: ProjectPaths, include_completed: bool = False, human: bool = False) -> dict[str, Any]:
    _load_manifest(paths)
    git = GitClient(paths.root)
    current_branch = git.branch()
    git_branches = set(git.branches())
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in _read_all_todos(paths):
        meta: TodoMeta = item["meta"]
        branch = meta.branch
        if not branch and item["path"].parent != paths.todo:
            branch = item["path"].parent.name
        branch = branch or "legacy"
        grouped.setdefault(branch, []).append(item)

    marker_branches = []
    if paths.branches.exists():
        for path in sorted(paths.branches.glob("*.json")):
            data = read_json(path)
            if data.get("branch"):
                marker_branches.append(str(data["branch"]))

    branches = sorted(set(grouped) | set(marker_branches))
    summaries = []
    for branch in branches:
        todos = grouped.get(branch, [])
        marker = _read_branch_marker(paths, branch)
        counts = _count_by_status([item["meta"] for item in todos])
        total = len(todos)
        done = counts.get("done", 0) + counts.get("cancelled", 0)
        unfinished = [
            item for item in todos
            if item["meta"].status not in {"done", "cancelled"}
        ]
        percent = 100 if marker["completed"] else int((done / total) * 100) if total else 0
        completed = marker["completed"]
        if not completed and total > 0 and not unfinished:
            completed = True
        status = "completed" if completed else marker["status"]
        item = {
            "branch": branch,
            "current": branch == current_branch,
            "exists_in_git": branch in git_branches,
            "completed": completed,
            "status": status,
            "progress_percent": percent,
            "todo_counts": counts,
            "unfinished_todos": [_todo_summary(todo) for todo in unfinished],
            "progress_note": marker.get("progress_note"),
            "updated_at": marker.get("updated_at"),
            "marker_path": _rel(paths, _branch_marker_path(paths, branch)) if _branch_marker_path(paths, branch).exists() else None,
        }
        if include_completed or not completed:
            summaries.append(item)
    if human:
        return {"ok": True, "text": _format_work_branches_text(summaries, include_completed)}
    return {"ok": True, "branches": summaries}


def mark_branch_work(
    paths: ProjectPaths,
    branch: str | None = None,
    completed: bool = False,
    progress_note: str | None = None,
) -> dict[str, Any]:
    _load_manifest(paths)
    resolved_branch = branch or _current_branch(paths)
    marker = _write_branch_marker(
        paths,
        resolved_branch,
        completed=completed,
        progress_note=progress_note,
    )
    _audit(
        paths,
        "mark_branch_work",
        {"branch": resolved_branch, "completed": completed, "progress_note": progress_note},
    )
    return {
        "ok": True,
        "branch": resolved_branch,
        "marker": marker,
        "marker_path": _rel(paths, _branch_marker_path(paths, resolved_branch)),
    }


def prepare_release_notes(
    paths: ProjectPaths,
    branch: str | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    _load_manifest(paths)
    sources = []
    if branch:
        source = paths.changelog / f"{_branch_slug(branch)}.md"
        if not source.exists():
            raise RuntimeError(f"Branch changelog not found: {_rel(paths, source)}")
        sources.append((branch, source))
    elif paths.changelog.exists():
        for source in sorted(paths.changelog.glob("*.md")):
            sources.append((source.stem, source))

    planned_entries: list[dict[str, str]] = []
    for source_branch, source in sources:
        for item in _extract_unreleased_changelog_entries(source.read_text(encoding="utf-8")):
            planned_entries.append(
                {
                    "branch": source_branch,
                    "source": _rel(paths, source),
                    "category": item["category"],
                    "entry": f"- 【{source_branch}】{item['entry'].removeprefix('- ').strip()}",
                }
            )

    if not apply:
        return {"ok": True, "mode": "proposal", "planned_entries": planned_entries}

    changelog = paths.root / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8") if changelog.exists() else "# 版本变更记录\n\n## [Unreleased]\n\n"
    for item in planned_entries:
        text = _insert_changelog_entry(text, item["category"], item["entry"])
    changelog.write_text(text, encoding="utf-8", newline="\n")
    _audit(
        paths,
        "prepare_release_notes",
        {"branch": branch, "apply": apply, "entries": len(planned_entries)},
    )
    return {
        "ok": True,
        "mode": "applied",
        "path": "CHANGELOG.md",
        "merged_entries": planned_entries,
    }


def prepare_release(
    paths: ProjectPaths,
    version: str | None = None,
    branch: str | None = None,
    apply: bool = False,
    allow_unfinished: bool = False,
    checks_profile: str = "default",
) -> dict[str, Any]:
    _load_manifest(paths)
    unfinished = list_work_branches(paths)["branches"]
    if unfinished and not allow_unfinished:
        return {
            "ok": False,
            "mode": "blocked",
            "error": "unfinished_branch_work",
            "unfinished_branches": unfinished,
            "next_actions": [
                "完成或标记分支工作完结，或传入 --allow-unfinished 明确允许继续准备发布。"
            ],
        }

    release_notes = prepare_release_notes(paths, branch=branch, apply=apply)
    baseline = None
    if version:
        baseline = create_baseline(paths, version, apply=False)

    checks = None
    if apply:
        checks = run_checks(paths, profile=checks_profile)
        if not checks["ok"]:
            return {
                "ok": False,
                "mode": "checks_failed",
                "release_notes": release_notes,
                "baseline": baseline,
                "checks": checks,
            }
        _audit(
            paths,
            "prepare_release",
            {
                "version": version,
                "branch": branch,
                "apply": apply,
                "allow_unfinished": allow_unfinished,
                "checks_profile": checks_profile,
            },
        )

    return {
        "ok": True,
        "mode": "applied" if apply else "proposal",
        "release_notes": release_notes,
        "baseline": baseline,
        "checks": checks,
    }


def migrate_legacy_todo(
    paths: ProjectPaths,
    branch: str,
    todo_id: str | None = None,
) -> dict[str, Any]:
    _load_manifest(paths)
    if not branch:
        raise RuntimeError("--branch is required.")
    target_dir = _branch_todo_dir(paths, branch)
    target_dir.mkdir(parents=True, exist_ok=True)
    migrated = []
    for item in _read_all_todos(paths, scope="legacy"):
        meta: TodoMeta = item["meta"]
        if todo_id and meta.id != todo_id:
            continue
        target = target_dir / item["path"].name
        if target.exists():
            raise RuntimeError(f"Target TODO already exists: {_rel(paths, target)}")
        meta.branch = branch
        meta.updated_at = utc_now()
        write_frontmatter(target, meta.to_dict(), item["body"])
        item["path"].unlink()
        migrated.append({"todo_id": meta.id, "path": _rel(paths, target)})
    if todo_id and not migrated:
        raise RuntimeError(f"Legacy TODO not found: {todo_id}")
    _audit(paths, "migrate_legacy_todo", {"branch": branch, "todo_id": todo_id, "migrated": len(migrated)})
    return {"ok": True, "branch": branch, "migrated": migrated}


def list_to_do(
    paths: ProjectPaths,
    statuses: list[str] | None = None,
    priorities: list[str] | None = None,
    source_requirement: str | None = None,
    scope: str = "branch",
    branch: str | None = None,
) -> dict[str, Any]:
    items = _read_all_todos(paths, scope=scope, branch=branch)
    if statuses:
        items = [item for item in items if item["meta"].status in statuses]
    if priorities:
        items = [item for item in items if item["meta"].priority in priorities]
    if source_requirement:
        items = [item for item in items if item["meta"].source_requirement == source_requirement]
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    items.sort(key=lambda item: (order.get(item["meta"].priority, 99), item["meta"].updated_at))
    return {
        "ok": True,
        "scope": scope,
        "branch": branch or _current_branch(paths),
        "todos": [_todo_summary(item) for item in items],
    }


def create_todo(
    paths: ProjectPaths,
    title: str,
    priority: str = "P2",
    status: str = "ready",
    source_requirement: str | None = None,
    assignee: str = "agent",
    body: str | None = None,
) -> dict[str, Any]:
    _load_manifest(paths)
    today = datetime.now(timezone.utc).date().isoformat()
    branch = _current_branch(paths)
    target_dir = _branch_todo_dir(paths, branch)
    existing = [
        path for path in _iter_todo_paths(paths, scope="all")
        if path.name.startswith(f"TODO-{today}-")
    ]
    todo_id = f"TODO-{today}-{len(existing) + 1:03d}"
    meta = TodoMeta(
        id=todo_id,
        title=title,
        status=status,  # type: ignore[arg-type]
        priority=priority,  # type: ignore[arg-type]
        assignee=assignee,
        source_requirement=source_requirement,
        branch=branch,
    )
    content = body or f"# {title}\n\n- [ ] 明确实现步骤\n- [ ] 完成开发\n- [ ] 运行检查\n- [ ] 记录版本变更\n"
    target = target_dir / f"{todo_id}-{_slug(title)}.md"
    write_frontmatter(target, meta.to_dict(), content)
    _audit(
        paths,
        "create_todo",
        {
            "todo_id": todo_id,
            "title": title,
            "priority": priority,
            "status": status,
            "source_requirement": source_requirement,
            "branch": branch,
        },
    )
    return {"ok": True, "todo_id": todo_id, "path": _rel(paths, target), "todo": meta.to_dict()}


def create_todo_from_source(
    paths: ProjectPaths,
    title: str | None = None,
    source_requirement: str | None = None,
    source_path: str | None = None,
    priority: str = "P1",
    status: str = "ready",
    assignee: str = "agent",
) -> dict[str, Any]:
    source = _load_todo_source(paths, source_requirement=source_requirement, source_path=source_path)
    resolved_title = title or f"落实：{source['title']}"
    items = source["items"]
    body = _todo_body_from_source(resolved_title, source, items)
    result = create_todo(
        paths,
        title=resolved_title,
        priority=priority,
        status=status,
        source_requirement=source.get("requirement_id"),
        assignee=assignee,
        body=body,
    )
    audit = _audit_todo_source_coverage(paths, result["path"], items)
    _audit(
        paths,
        "create_todo_from_source",
        {
            "todo_id": result["todo_id"],
            "source_requirement": source_requirement,
            "source_path": source_path,
            "source_items": len(items),
        },
    )
    return {**result, "source": source, "source_coverage_audit": audit}


def _load_todo_source(
    paths: ProjectPaths,
    source_requirement: str | None = None,
    source_path: str | None = None,
) -> dict[str, Any]:
    if bool(source_requirement) == bool(source_path):
        raise RuntimeError("Pass exactly one of source_requirement or source_path.")
    if source_requirement:
        item = _find_requirement(paths, source_requirement)
        if not item:
            raise RuntimeError(f"Requirement not found: {source_requirement}")
        meta: RequirementMeta = item["meta"]
        body = item["body"]
        items = [str(value).strip() for value in meta.acceptance if str(value).strip()]
        if not items:
            items = _extract_source_items(body)
        return {
            "kind": "requirement",
            "requirement_id": meta.id,
            "title": meta.title,
            "path": _rel(paths, item["path"]),
            "items": items,
        }
    path = (paths.root / str(source_path)).resolve()
    if not path.exists() or not path.is_file():
        raise RuntimeError(f"Source document not found: {source_path}")
    meta, body = read_frontmatter(path)
    title = str(meta.get("title") or _extract_heading_title(body) or path.stem)
    items = _extract_source_items(body)
    if not items:
        raise RuntimeError(f"No source items found in {source_path}")
    return {
        "kind": "document",
        "title": title,
        "path": _rel(paths, path),
        "items": items,
    }


def _extract_heading_title(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
    return None


def _extract_source_items(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"^(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?(.+)$", stripped)
        if match:
            value = match.group(1).strip()
            if value and value not in items:
                items.append(value)
    return items


def _todo_body_from_source(title: str, source: dict[str, Any], items: list[str]) -> str:
    source_label = source.get("requirement_id") or source.get("path")
    lines = [
        f"# {title}",
        "",
        "## 来源",
        "",
        f"- 类型: {source['kind']}",
        f"- 标识: {source_label}",
        "",
        "## 来源功能/逻辑覆盖",
        "",
    ]
    lines.extend(f"- [ ] {item}" for item in items)
    lines.extend(
        [
            "",
            "## 审计要求",
            "",
            "- [ ] TODO 已逐项覆盖来源文档/正式需求/草案需求中的功能与逻辑。",
            "- [ ] 完成开发前已生成验收矩阵并通过覆盖审核。",
            "- [ ] 代码完成后已按验收矩阵执行验收。",
            "",
        ]
    )
    return "\n".join(lines)


def _audit_todo_source_coverage(paths: ProjectPaths, todo_path: str, source_items: list[str]) -> dict[str, Any]:
    body = (paths.root / todo_path).read_text(encoding="utf-8")
    missing = [item for item in source_items if item not in body]
    result = {"ok": not missing, "source_items": len(source_items), "missing_items": missing}
    if missing:
        raise RuntimeError(f"TODO source coverage audit failed: {missing[:3]}")
    return result


def create_work_surface(
    paths: ProjectPaths,
    title: str,
    branch_name: str | None = None,
    requirement_title: str | None = None,
    todo_title: str | None = None,
    priority: str = "P1",
    owners: list[str] | None = None,
    acceptance: list[str] | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    git = GitClient(paths.root)
    manifest = _load_manifest(paths)
    policy = read_policy(paths)
    before_branch = git.branch()
    workflow = WorkflowRun.start("create_work_surface", before_branch)
    step = workflow.start_step("prepare_branch")
    target_branch = branch_name
    branch_created = False
    should_create_branch = bool(branch_name) or before_branch == manifest.default_branch or is_protected_branch(before_branch, policy)
    if should_create_branch:
        if _git_dirty_files(paths, git, manifest, include_untracked=False):
            raise RuntimeError("Refusing to create a work surface on a new branch with tracked worktree changes.")
        target_branch = target_branch or _branch_name_from_title(title)
        if target_branch != before_branch:
            git.create_branch(target_branch)
            branch_created = True
    else:
        target_branch = before_branch
    workflow.finish_step(step, {"branch": target_branch, "branch_created": branch_created})

    resolved_requirement_title = requirement_title or title
    resolved_todo_title = todo_title or title
    step = workflow.start_step("create_requirement")
    requirement = create_requirement(
        paths,
        title=resolved_requirement_title,
        owners=owners or ["agent"],
        acceptance=acceptance or ["完成当前工作面的核心实现并通过项目检查。"],
        body=body,
    )
    workflow.finish_step(step, {"requirement_id": requirement["requirement_id"]})
    step = workflow.start_step("create_todo")
    todo = create_todo(
        paths,
        title=resolved_todo_title,
        priority=priority,
        source_requirement=requirement["requirement_id"],
        assignee="agent",
        body=f"# {resolved_todo_title}\n\n- [ ] 明确实现范围\n- [ ] 完成开发\n- [ ] 运行检查\n- [ ] 完成后写入分支版本变更记录\n",
    )
    workflow.finish_step(step, {"todo_id": todo["todo_id"]})
    step = workflow.start_step("start_task")
    task = start_task(paths, todo["todo_id"], branch_mode="current_branch")
    workflow.finish_step(step, {"todo_id": todo["todo_id"], "branch": task["branch"]})
    step = workflow.start_step("write_branch_marker")
    _write_branch_marker(paths, target_branch, completed=False, progress_note="工作面已创建，任务已启动。")
    workflow.finish_step(step, {"branch": target_branch})
    step = workflow.start_step("audit")
    _audit(
        paths,
        "create_work_surface",
        {
            "title": title,
            "branch_name": target_branch,
            "requirement_id": requirement["requirement_id"],
            "todo_id": todo["todo_id"],
            "branch_created": branch_created,
        },
    )
    workflow.finish_step(step, {"branch": target_branch, "branch_created": branch_created})
    workflow.finish()
    return {
        "ok": True,
        "branch": target_branch,
        "branch_created": branch_created,
        "requirement": requirement,
        "todo": todo,
        "task": task,
        "workflow": workflow.to_dict(),
        "changelog_scope": "global" if _changelog_path(paths, scope="branch") == paths.root / "CHANGELOG.md" else "branch",
        "changelog_path": _rel(paths, _changelog_path(paths, scope="branch")),
    }


def update_work_surface(
    paths: ProjectPaths,
    branch: str | None = None,
    progress_note: str | None = None,
    completed: bool | None = None,
    todo_ids: list[str] | None = None,
    todo_status: str | None = None,
    changelog_entry: str | None = None,
    changelog_category: str = "Changed",
    changelog_scope: str = "branch",
) -> dict[str, Any]:
    _load_manifest(paths)
    git = GitClient(paths.root)
    resolved_branch = branch or git.branch()
    before_marker = _read_branch_marker(paths, resolved_branch)
    marker_completed = before_marker["completed"] if completed is None else completed
    marker = _write_branch_marker(paths, resolved_branch, completed=marker_completed, progress_note=progress_note or before_marker["progress_note"])

    updated_todos: list[dict[str, Any]] = []
    if todo_status or todo_ids:
        target_ids = todo_ids
        if not target_ids and todo_status:
            target_ids = [item["meta"].id for item in _read_all_todos(paths, scope="branch", branch=resolved_branch)]
        for todo_id in target_ids or []:
            todo_result = update_task(paths, todo_id, status=todo_status)
            updated_todos.append(todo_result["todo"])

    changelog = None
    if changelog_entry:
        changelog = add_changelog_entry(
            paths,
            message=changelog_entry,
            category=changelog_category,
            scope=changelog_scope,
            branch=resolved_branch,
        )
    regression_todo = _ensure_regression_guard_todo(
        paths,
        resolved_branch,
        progress_note=progress_note,
        changelog_entry=changelog_entry,
    )

    _audit(
        paths,
        "update_work_surface",
        {
            "branch": resolved_branch,
            "completed": completed,
            "progress_note": progress_note,
            "todo_ids": todo_ids,
            "todo_status": todo_status,
            "changelog_entry": bool(changelog_entry),
        },
    )
    return {
        "ok": True,
        "branch": resolved_branch,
        "marker": marker,
        "updated_todos": updated_todos,
        "changelog": changelog,
        "regression_guard": regression_todo,
    }


def _regression_guard_todo_id(branch: str) -> str:
    slug = _branch_slug(branch).upper().replace("-", "_")
    return f"TODO-REGRESSION-{slug}"


def _regression_guard_body(
    branch: str,
    progress_note: str | None = None,
    changelog_entry: str | None = None,
) -> str:
    body = (
        f"# 回归测试护栏：{branch}\n\n"
        "## 自动规则\n\n"
        "- [ ] 执行测试过程中发现的问题，必须补成回归测试用例后再关闭相关工作。\n"
        "- [ ] 用户提出的问题，必须补成回归测试用例后再关闭相关工作。\n\n"
        "## 操作要求\n\n"
        "- 新增或修复代码时，优先在现有测试目录中加入最小可复现用例。\n"
        "- 如果暂时无法自动化，应在 TODO 进展中记录原因、复现步骤和后续测试落点。\n"
    )
    notes = []
    if progress_note:
        notes.append(f"- 工作面进展：{progress_note}")
    if changelog_entry:
        notes.append(f"- 版本变更：{changelog_entry}")
    if notes:
        body += "\n## 最近一次更新线索\n\n" + "\n".join(notes) + "\n"
    return body


def _ensure_regression_guard_todo(
    paths: ProjectPaths,
    branch: str,
    progress_note: str | None = None,
    changelog_entry: str | None = None,
) -> dict[str, Any]:
    todo_id = _regression_guard_todo_id(branch)
    branch_dir = _branch_todo_dir(paths, branch)
    target = branch_dir / f"{todo_id.lower().replace('_', '-')}.md"
    body = _regression_guard_body(branch, progress_note=progress_note, changelog_entry=changelog_entry)
    if target.exists():
        meta_raw, existing_body = read_frontmatter(target)
        meta = TodoMeta.from_dict(meta_raw)
        if progress_note or changelog_entry:
            existing_body = existing_body.rstrip() + "\n\n" + body.split("## 最近一次更新线索", 1)[-1].strip() + "\n"
        write_frontmatter(target, meta.to_dict(), existing_body)
        return {"todo_id": todo_id, "path": _rel(paths, target), "created": False}
    meta = TodoMeta(
        id=todo_id,
        title=f"{branch} 回归测试护栏",
        status="ready",
        priority="P1",
        branch=branch,
    )
    write_frontmatter(target, meta.to_dict(), body)
    return {"todo_id": todo_id, "path": _rel(paths, target), "created": True}


def create_requirement(
    paths: ProjectPaths,
    title: str,
    owners: list[str] | None = None,
    acceptance: list[str] | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    _load_manifest(paths)
    collection_path, collection_meta, requirements = _load_requirement_collection(paths, "draft")
    requirement_id = _next_global_requirement_id(paths, requirements, "draft")
    meta = RequirementMeta(
        id=requirement_id,
        title=title,
        status="draft",
        owners=owners or [],
        acceptance=acceptance or [],
    )
    if body:
        meta.change_history.append({"ts": utc_now(), "event": "body_note", "body": body})
    requirements.append(meta.to_dict())
    _save_requirement_collection(collection_path, collection_meta, requirements)
    _audit(paths, "create_requirement", {"requirement_id": requirement_id, "title": title})
    return {
        "ok": True,
        "requirement_id": requirement_id,
        "path": _rel(paths, collection_path),
        "requirement": meta.to_dict(),
    }


def update_requirement(
    paths: ProjectPaths,
    requirement_id: str,
    title: str | None = None,
    owner: list[str] | None = None,
    acceptance: list[str] | None = None,
    depends_on: list[str] | None = None,
    status: str | None = None,
    append_body: str | None = None,
    allow_final: bool = False,
) -> dict[str, Any]:
    item = _find_requirement(paths, requirement_id)
    if not item:
        raise RuntimeError(f"Requirement not found: {requirement_id}")
    meta: RequirementMeta = item["meta"]
    if meta.status != "draft" and not allow_final:
        raise RuntimeError("Only draft requirements can be updated unless --allow-final is set.")
    before = meta.to_dict()
    if title:
        meta.title = title
    if owner is not None:
        meta.owners = owner
    if acceptance is not None:
        meta.acceptance = acceptance
    if depends_on is not None:
        meta.depends_on = depends_on
    if status:
        meta.status = status  # type: ignore[assignment]
    meta.updated_at = utc_now()
    meta.change_history.append(
        {
            "ts": utc_now(),
            "event": "updated",
            "fields": _changed_fields(before, meta.to_dict()),
        }
    )
    body = item["body"]
    if append_body:
        body = body.rstrip() + f"\n\n{append_body.strip()}\n"
    if item.get("collection"):
        _replace_requirement_in_collection(item["path"], meta)
    else:
        write_frontmatter(item["path"], meta.to_dict(), body)
    _audit(
        paths,
        "update_requirement",
        {
            "requirement_id": requirement_id,
            "fields": _changed_fields(before, meta.to_dict()),
            "allow_final": allow_final,
        },
    )
    return {"ok": True, "requirement_id": requirement_id, "path": _rel(paths, item["path"]), "requirement": meta.to_dict()}


def start_task(
    paths: ProjectPaths,
    todo_id: str,
    branch_mode: str = "new_branch",
    branch_name: str | None = None,
) -> dict[str, Any]:
    git = GitClient(paths.root)
    manifest = _load_manifest(paths)
    policy = read_policy(paths)
    before = git.head()
    current_branch = git.branch()
    dirty = bool(_git_dirty_files(paths, git, manifest))
    if dirty and branch_mode == "new_branch":
        raise RuntimeError("Refusing to create a new task branch with a dirty worktree.")
    if branch_mode == "current_branch" and is_protected_branch(current_branch, policy):
        raise RuntimeError("Refusing to start a task directly on a protected branch.")

    item = _find_todo(paths, todo_id)
    meta: TodoMeta = item["meta"]
    if meta.status not in {"ready", "draft", "blocked"}:
        raise RuntimeError(f"TODO {todo_id} cannot be started from status {meta.status}.")
    branch = current_branch
    if branch_mode == "new_branch":
        if branch_name:
            branch = branch_name
        else:
            pattern = policy.get("branch_naming", {}).get("feature", "feat/{todo_id}-{slug}")
            branch = pattern.format(todo_id=todo_id, slug=_slug(meta.title))
        git.create_branch(branch)

    meta.status = "in_progress"
    meta.branch = branch
    meta.baseline_ref = manifest.active_baseline or before
    meta.updated_at = utc_now()
    target_path = item["path"]
    desired_dir = _branch_todo_dir(paths, branch)
    if target_path.parent != desired_dir:
        desired_dir.mkdir(parents=True, exist_ok=True)
        moved_path = desired_dir / target_path.name
        if moved_path.exists() and moved_path.resolve() != target_path.resolve():
            raise RuntimeError(f"Cannot move TODO because target already exists: {_rel(paths, moved_path)}")
        if moved_path.resolve() != target_path.resolve():
            target_path.unlink()
        target_path = moved_path
    write_frontmatter(target_path, meta.to_dict(), item["body"])
    _write_branch_marker(paths, branch, completed=False, progress_note=f"任务 {todo_id} 已启动。")
    after = git.head()
    _audit(
        paths,
        "start_task",
        {"todo_id": todo_id, "branch_mode": branch_mode, "branch_name": branch_name},
        True,
        before_ref=before,
        after_ref=after,
    )
    return {"ok": True, "todo_id": todo_id, "branch": branch, "status": meta.status, "path": _rel(paths, target_path)}


def update_task(
    paths: ProjectPaths,
    todo_id: str,
    status: str | None = None,
    blocked_by: list[str] | None = None,
    progress_line: str | None = None,
    changelog_entry: str | None = None,
    changelog_category: str = "Changed",
    changelog_scope: str = "branch",
) -> dict[str, Any]:
    item = _find_todo(paths, todo_id)
    meta: TodoMeta = item["meta"]
    if status:
        meta.status = status  # type: ignore[assignment]
    if status == "done":
        linked_requirement = _find_requirement(paths, meta.source_requirement) if meta.source_requirement else None
        if linked_requirement and linked_requirement["meta"].status == "approved" and not changelog_entry:
            raise RuntimeError(
                "Completing work for an approved requirement requires --changelog-entry."
            )
        acceptance = validate_acceptance(paths, todo_id)
    if blocked_by:
        meta.blocked_by = blocked_by
    meta.updated_at = utc_now()
    body = item["body"]
    if progress_line:
        body = body.rstrip() + f"\n\n- {progress_line}\n"
    write_frontmatter(item["path"], meta.to_dict(), body)
    changelog_result = None
    if changelog_entry:
        changelog_result = add_changelog_entry(
            paths,
            message=changelog_entry,
            category=changelog_category,
            requirement_id=meta.source_requirement,
            todo_id=todo_id,
            scope=changelog_scope,
            branch=meta.branch,
        )
    _audit(
        paths,
        "update_task",
        {
            "todo_id": todo_id,
            "status": status,
            "blocked_by": blocked_by,
            "changelog_entry": bool(changelog_entry),
            "changelog_scope": changelog_scope,
        },
    )
    return {"ok": True, "todo": meta.to_dict(), "changelog": changelog_result, "acceptance": locals().get("acceptance")}


def create_acceptance_matrix(paths: ProjectPaths, todo_id: str) -> dict[str, Any]:
    item = _find_todo(paths, todo_id)
    meta: TodoMeta = item["meta"]
    todo_items = _extract_todo_checklist_items(item["body"])
    if not todo_items:
        raise RuntimeError(f"TODO has no checklist items to cover: {todo_id}")
    matrix_path = _acceptance_matrix_path(paths, meta.branch or _current_branch(paths), todo_id)
    lines = [
        f"# 验收矩阵：{todo_id}",
        "",
        f"- TODO: {todo_id}",
        f"- 分支: {meta.branch or _current_branch(paths)}",
        f"- 来源需求: {meta.source_requirement or '无'}",
        "",
        "| 编号 | TODO 功能/逻辑 | 验收方式 | 代码/测试证据 | 状态 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for index, todo_item in enumerate(todo_items, start=1):
        lines.append(f"| A{index:03d} | {todo_item} | 测试或人工审查 | 待补充 | pending |")
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    audit = _audit_acceptance_matrix_coverage(paths, todo_id, matrix_path)
    _audit(paths, "create_acceptance_matrix", {"todo_id": todo_id, "matrix_path": _rel(paths, matrix_path)})
    return {"ok": True, "todo_id": todo_id, "path": _rel(paths, matrix_path), "coverage_audit": audit}


def validate_acceptance(
    paths: ProjectPaths,
    todo_id: str,
    matrix_path: str | None = None,
    run_checks_profile: str | None = None,
) -> dict[str, Any]:
    item = _find_todo(paths, todo_id)
    meta: TodoMeta = item["meta"]
    path = (paths.root / matrix_path).resolve() if matrix_path else _acceptance_matrix_path(paths, meta.branch or _current_branch(paths), todo_id)
    if not path.exists():
        raise RuntimeError(f"Acceptance matrix is required before completing code: {_rel(paths, path)}")
    coverage = _audit_acceptance_matrix_coverage(paths, todo_id, path)
    readiness = _audit_acceptance_matrix_readiness(path)
    checks = run_checks(paths, profile=run_checks_profile) if run_checks_profile else None
    ok = coverage["ok"] and readiness["ok"] and (checks is None or checks["ok"])
    result = {
        "ok": ok,
        "todo_id": todo_id,
        "matrix_path": _rel(paths, path),
        "coverage": coverage,
        "readiness": readiness,
        "checks": checks,
    }
    _audit(paths, "validate_acceptance", {"todo_id": todo_id, "matrix_path": _rel(paths, path)}, ok=ok)
    if not ok:
        raise RuntimeError(f"Acceptance validation failed for {todo_id}")
    return result


def _acceptance_matrix_path(paths: ProjectPaths, branch: str, todo_id: str) -> Path:
    return paths.acceptance / _branch_slug(branch) / f"{todo_id}-acceptance-matrix.md"


def _extract_todo_checklist_items(body: str) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        match = re.match(r"^\s*-\s+\[[ xX]\]\s+(.+?)\s*$", line)
        if match:
            value = match.group(1).strip()
            if value and value not in items:
                items.append(value)
    return items


def _matrix_items(text: str) -> list[str]:
    return [row["item"] for row in _matrix_rows(text)]


def _matrix_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("| A"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[1]:
            rows.append(
                {
                    "id": cells[0],
                    "item": cells[1],
                    "method": cells[2],
                    "evidence": cells[3],
                    "status": cells[4],
                }
            )
    return rows


def _audit_acceptance_matrix_readiness(matrix_path: Path) -> dict[str, Any]:
    accepted_statuses = {"pass", "passed", "ok", "done", "implemented", "通过", "已通过", "完成", "已完成", "已实现"}
    placeholder_evidence = {"", "待补充", "tbd", "todo", "pending", "n/a", "na"}
    missing_evidence: list[str] = []
    pending_status: list[str] = []
    for row in _matrix_rows(matrix_path.read_text(encoding="utf-8")):
        if row["evidence"].strip().lower() in placeholder_evidence:
            missing_evidence.append(row["item"])
        if row["status"].strip().lower() not in accepted_statuses:
            pending_status.append(row["item"])
    return {
        "ok": not missing_evidence and not pending_status,
        "missing_evidence_items": missing_evidence,
        "pending_status_items": pending_status,
    }


def _audit_acceptance_matrix_coverage(paths: ProjectPaths, todo_id: str, matrix_path: Path) -> dict[str, Any]:
    item = _find_todo(paths, todo_id)
    todo_items = _extract_todo_checklist_items(item["body"])
    matrix_items = _matrix_items(matrix_path.read_text(encoding="utf-8"))
    missing = [item for item in todo_items if item not in matrix_items]
    extra = [item for item in matrix_items if item not in todo_items]
    return {
        "ok": not missing,
        "todo_items": len(todo_items),
        "matrix_items": len(matrix_items),
        "missing_items": missing,
        "extra_items": extra,
    }


def add_changelog_entry(
    paths: ProjectPaths,
    message: str,
    category: str = "Changed",
    requirement_id: str | None = None,
    todo_id: str | None = None,
    scope: str = "branch",
    branch: str | None = None,
) -> dict[str, Any]:
    if not message.strip():
        raise RuntimeError("Changelog message is required.")
    normalized_category = _normalize_changelog_category(category)
    if normalized_category not in CHANGELOG_CATEGORY_HEADINGS:
        raise RuntimeError(f"Invalid changelog category: {category}")
    changelog = _changelog_path(paths, scope=scope, branch=branch)
    if changelog.exists():
        text = changelog.read_text(encoding="utf-8")
    else:
        text = "# 版本变更记录\n\n## [Unreleased]\n\n"
    if "## [Unreleased]" not in text:
        text = text.rstrip() + "\n\n## [Unreleased]\n\n"

    entry = _format_changelog_entry(message, requirement_id, todo_id)
    updated = _insert_changelog_entry(text, normalized_category, entry)
    changelog.parent.mkdir(parents=True, exist_ok=True)
    changelog.write_text(updated, encoding="utf-8", newline="\n")
    _audit(
        paths,
        "add_changelog_entry",
        {
            "category": category,
            "requirement_id": requirement_id,
            "todo_id": todo_id,
            "message": message,
            "scope": scope,
            "branch": branch or _current_branch(paths),
        },
    )
    return {
        "ok": True,
        "path": _rel(paths, changelog),
        "scope": scope,
        "branch": branch or _current_branch(paths),
        "category": normalized_category,
        "heading": CHANGELOG_CATEGORY_HEADINGS[normalized_category],
        "entry": entry,
    }


def promote_requirement(
    paths: ProjectPaths,
    requirement_id: str,
    version: str | None = None,
    baseline_ref: str | None = None,
) -> dict[str, Any]:
    item = _find_requirement(paths, requirement_id)
    if item:
        meta: RequirementMeta = item["meta"]
        if meta.status != "draft":
            raise RuntimeError(f"Requirement {requirement_id} is not a draft.")
        final_path, final_meta, final_requirements = _load_requirement_collection(paths, "final")
        final_id = _next_global_requirement_id(paths, final_requirements, "approved")
        old_id = meta.id
        meta.id = final_id
        meta.status = "approved"
        meta.version = version
        meta.baseline_ref = baseline_ref
        meta.updated_at = utc_now()
        meta.change_history.append({"ts": utc_now(), "event": "promoted", "from": old_id})
        final_requirements.append(meta.to_dict())
        _save_requirement_collection(final_path, final_meta, final_requirements)
        if item.get("collection"):
            _remove_requirement_from_collection(item["path"], old_id)
        else:
            item["path"].unlink()
        _audit(paths, "promote_requirement", {"requirement_id": old_id, "final_id": final_id})
        return {"ok": True, "requirement_id": final_id, "path": _rel(paths, final_path)}
    raise RuntimeError(f"Requirement not found: {requirement_id}")


def create_baseline(paths: ProjectPaths, name: str, from_ref: str = "HEAD", apply: bool = False) -> dict[str, Any]:
    if not SEMVER.match(name):
        raise RuntimeError("Baseline name must be a semantic version, for example v0.1.0.")
    git = GitClient(paths.root)
    policy = read_policy(paths)
    manifest = _load_manifest(paths)
    if apply and policy.get("baseline_strategy", {}).get("require_clean_worktree", True) and _git_dirty_files(paths, git, manifest):
        raise RuntimeError("Refusing to create baseline with a dirty worktree.")
    if git.tag_exists(name):
        raise RuntimeError(f"Tag already exists: {name}")
    changes = ["VERSION", "CHANGELOG.md", f"git tag {name} {from_ref}"]
    if not apply:
        return {"ok": True, "mode": "proposal", "version": name, "planned_changes": changes}

    (paths.root / "VERSION").write_text(name.lstrip("v") + "\n", encoding="utf-8")
    changelog = paths.root / "CHANGELOG.md"
    existing = changelog.read_text(encoding="utf-8") if changelog.exists() else "# Changelog\n\n"
    today = datetime.now(timezone.utc).date().isoformat()
    if f"## [{name.lstrip('v')}]" not in existing:
        existing = existing.replace(
            "## [Unreleased]\n",
            f"## [Unreleased]\n\n## [{name.lstrip('v')}] - {today}\n\n### 变更\n- 创建基线 {name}。\n\n",
        )
    changelog.write_text(existing, encoding="utf-8", newline="\n")
    git.create_tag(name, from_ref)
    manifest = _load_manifest(paths)
    manifest.active_baseline = name
    _save_manifest(paths, manifest)
    _audit(paths, "create_baseline", {"name": name, "from_ref": from_ref, "apply": apply})
    return {"ok": True, "mode": "applied", "baseline": name}


MOJIBAKE_MARKERS = (
    "\ufffd",
    "锟斤拷",
    "ï¿½",
    "涓枃",
    "浣跨敤",
    "鐢ㄦ埛",
    "鍒涘缓",
    "椤圭洰",
)
REPEATED_QUESTION_RE = re.compile(r"\?{4,}")
DOC_CHECK_SUFFIXES = {".md", ".markdown", ".yaml", ".yml"}


def _doc_check_paths(paths: ProjectPaths, scope: str = "docs") -> list[Path]:
    if scope not in {"docs", "all"}:
        raise RuntimeError(f"Invalid docs encoding scope: {scope}")
    roots = [
        paths.root / "README.md",
        paths.root / "AGENTS.md",
        paths.root / "CHANGELOG.md",
        paths.docs,
        paths.todo,
        paths.skill,
    ]
    if scope == "all":
        roots.extend([paths.root / "pyproject.toml"])
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            if root.suffix.lower() in DOC_CHECK_SUFFIXES or root.name in {"AGENTS.md", "README.md", "CHANGELOG.md"}:
                files.append(root)
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = _rel(paths, path)
            if rel.startswith((".git/", ".pm-skill/", "__pycache__/")):
                continue
            if path.suffix.lower() in DOC_CHECK_SUFFIXES:
                files.append(path)
    return sorted(set(files))


def _mojibake_issues_for_text(text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for marker in MOJIBAKE_MARKERS:
            if marker in line:
                issues.append(
                    {
                        "line": line_number,
                        "kind": "mojibake_marker",
                        "marker": marker,
                        "preview": line.strip()[:160],
                    }
                )
                break
        match = REPEATED_QUESTION_RE.search(line)
        if match:
            issues.append(
                {
                    "line": line_number,
                    "kind": "repeated_question_marks",
                    "marker": match.group(0),
                    "preview": line.strip()[:160],
                }
            )
    return issues


def check_docs_encoding(paths: ProjectPaths, scope: str = "docs") -> dict[str, Any]:
    scanned = []
    issues = []
    for path in _doc_check_paths(paths, scope):
        rel = _rel(paths, path)
        scanned.append(rel)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            issues.append(
                {
                    "path": rel,
                    "line": None,
                    "kind": "utf8_decode_error",
                    "marker": str(exc),
                    "preview": "",
                }
            )
            continue
        for issue in _mojibake_issues_for_text(text):
            issues.append({"path": rel, **issue})

    ok = not issues
    _audit(
        paths,
        "check_docs_encoding",
        {"scope": scope, "scanned_files": len(scanned)},
        ok=ok,
        error=None if ok else "docs_encoding_issues",
    )
    if issues:
        preview = "; ".join(
            f"{issue['path']}:{issue.get('line')}: {issue['kind']}" for issue in issues[:5]
        )
        raise RuntimeError(f"Docs encoding check failed: {preview}")
    return {"ok": True, "scope": scope, "scanned_files": len(scanned), "issues": []}


def run_checks(paths: ProjectPaths, profile: str = "default") -> dict[str, Any]:
    policy = read_policy(paths)
    commands = policy.get("check_profiles", {}).get(profile)
    if not commands:
        raise RuntimeError(f"Unknown check profile: {profile}")
    results = []
    ok = True
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=paths.root,
            text=True,
            capture_output=True,
            shell=True,
        )
        item = {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
        results.append(item)
        ok = ok and completed.returncode == 0
    _audit(paths, "run_checks", {"profile": profile}, ok=ok, error=None if ok else "checks_failed")
    return {"ok": ok, "profile": profile, "results": results}


def sync_index(paths: ProjectPaths, scope: str = "all") -> dict[str, Any]:
    git = GitClient(paths.root)
    policy = read_policy(paths)
    manifest = _load_manifest(paths)
    target_commit = _index_target_commit(paths, git.head(), manifest)
    fingerprints: dict[str, Any] = {}
    tracked = set(git.tracked_files())
    scope_paths = normalize_scope_paths(paths, manifest.index_scope.paths, field_name="index_scope.paths")
    scope_extensions = normalize_scope_extensions(manifest.index_scope.extensions)
    exclude_enabled = exclude_scope_enabled(manifest.exclude_scope.paths, manifest.exclude_scope.extensions)
    exclude_paths, exclude_extensions = _manifest_exclude_scope(paths, manifest)
    candidates = [p for p in paths.root.rglob("*") if p.is_file()]
    indexed = 0
    for path in candidates:
        rel = _rel(paths, path)
        if not matches_scope(rel, scope_paths, scope_extensions):
            continue
        if exclude_enabled and matches_exclude_scope(rel, exclude_paths, exclude_extensions):
            continue
        if excluded_from_index(rel, policy):
            continue
        if (
            rel.startswith(".pm-skill/index/")
            or rel.startswith(".pm-skill/audit/")
            or rel == ".pm-skill/project-manifest.json"
        ):
            continue
        if path.stat().st_size > 1_000_000:
            continue
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        fingerprints[rel] = {
            "tracked": rel in tracked,
            "blob_oid": git.blob_oid(rel) if rel in tracked else None,
            "sha256": sha,
            "kind": _kind_for_path(rel),
            "last_seen_commit": target_commit,
        }
        indexed += 1
    write_json_atomic(paths.index / "file-fingerprints.json", fingerprints)
    semantic_manifest = {
        "mode": "summary_only",
        "last_built_at": utc_now(),
        "scope": scope,
        "items": [
            rel
            for rel in fingerprints
            if rel.startswith(("docs/", "todo/", "README", "CHANGELOG"))
        ],
    }
    write_json_atomic(paths.index / "semantic-index-manifest.json", semantic_manifest)
    if _last_commit_summary_commit(paths.index / "commit-summaries.jsonl") != target_commit:
        append_jsonl(
            paths.index / "commit-summaries.jsonl",
            {
                "commit": target_commit,
                "parents": [],
                "summary": "Index synchronized",
                "trailers": {},
                "ts": utc_now(),
            },
        )
    manifest.last_indexed_commit = target_commit
    _save_manifest(paths, manifest)
    _audit(paths, "sync_index", {"scope": scope})
    return {
        "ok": True,
        "indexed_files": indexed,
        "last_indexed_commit": manifest.last_indexed_commit,
        "index_scope": manifest.index_scope.__dict__,
        "exclude_scope": manifest.exclude_scope.__dict__,
    }


def handover(
    paths: ProjectPaths,
    summary_level: str = "standard",
    session_id: str = "local",
    next_action: list[str] | None = None,
) -> dict[str, Any]:
    git = GitClient(paths.root)
    todos = _read_all_todos(paths)
    active = [item["meta"].id for item in todos if item["meta"].status in {"ready", "in_progress", "blocked"}]
    today = datetime.now(timezone.utc).date().isoformat()
    existing = sorted(paths.handover.glob(f"HO-{today}-*.md"))
    handover_id = f"HO-{today}-{len(existing) + 1:03d}"
    meta = HandoverMeta(
        id=handover_id,
        from_session=session_id,
        branch=git.branch(),
        head_commit=git.head(),
        related_todos=active,
        next_actions=next_action or ["Run show-status, then continue the highest-priority active TODO."],
    )
    body = (
        "# Handover Summary\n\n"
        f"- Summary level: {summary_level}\n"
        f"- Branch: {meta.branch}\n"
        f"- HEAD: {meta.head_commit or 'no commits yet'}\n"
        f"- Dirty files: {len(_git_dirty_files(paths, git, _load_manifest(paths)))}\n"
        f"- Active TODOs: {', '.join(active) if active else 'none'}\n\n"
        "# Risks\n\n"
        "- Review dirty files before starting new work.\n\n"
        "# Next Actions\n\n"
        + "\n".join(f"- {action}" for action in meta.next_actions)
        + "\n"
    )
    target = paths.handover / f"{handover_id}.md"
    write_frontmatter(target, meta.to_dict(), body)
    manifest = _load_manifest(paths)
    manifest.latest_handover = _rel(paths, target)
    _save_manifest(paths, manifest)
    _audit(paths, "handover", {"summary_level": summary_level, "session_id": session_id})
    return {"ok": True, "handover_id": handover_id, "handover_path": _rel(paths, target)}


def query_audit(
    paths: ProjectPaths,
    command: str | None = None,
    ok: bool | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    if not paths.audit_log.exists():
        return {"ok": True, "events": []}
    events = []
    for line in paths.audit_log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if command and event.get("command") != command:
            continue
        if ok is not None and event.get("ok") is not ok:
            continue
        events.append(event)
    return {"ok": True, "events": events[-limit:]}


def list_requirements(
    paths: ProjectPaths,
    status: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    items = _read_all_requirements(paths, warnings=warnings)
    if status:
        items = [item for item in items if item["meta"].status == status]
    return {
        "ok": True,
        "requirements": [
            {**item["meta"].to_dict(), "path": _rel(paths, item["path"])}
            for item in items
        ],
        "warnings": warnings,
    }


def show_requirement(paths: ProjectPaths, requirement_id: str) -> dict[str, Any]:
    item = _find_requirement(paths, requirement_id)
    if not item:
        raise RuntimeError(f"Requirement not found: {requirement_id}")
    return {
        "ok": True,
        "requirement": item["meta"].to_dict(),
        "path": _rel(paths, item["path"]),
        "body": item["body"],
    }


def delete_requirement(
    paths: ProjectPaths,
    requirement_id: str,
    remove_todos: bool = True,
) -> dict[str, Any]:
    item = _find_requirement(paths, requirement_id)
    if not item:
        raise RuntimeError(f"Requirement not found: {requirement_id}")
    removed_todos = []
    if remove_todos:
        for todo in list(_read_all_todos(paths)):
            if todo["meta"].source_requirement == requirement_id:
                removed_todos.append(todo["meta"].id)
                todo["path"].unlink()
    if item.get("collection"):
        _remove_requirement_from_collection(item["path"], requirement_id)
    else:
        item["path"].unlink()
    _audit(
        paths,
        "delete_requirement",
        {"requirement_id": requirement_id, "removed_todos": removed_todos},
    )
    return {
        "ok": True,
        "requirement_id": requirement_id,
        "removed_todos": removed_todos,
    }


def promote_requirement_slice(
    paths: ProjectPaths,
    source_requirement_id: str,
    title: str,
    acceptance: list[str],
    source_slice: str | None = None,
    version: str | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    source = _find_requirement(paths, source_requirement_id)
    if not source:
        raise RuntimeError(f"Requirement not found: {source_requirement_id}")
    source_meta: RequirementMeta = source["meta"]
    final_path, final_meta, final_requirements = _load_requirement_collection(paths, "final")
    final_id = _next_global_requirement_id(paths, final_requirements, "approved")
    meta = RequirementMeta(
        id=final_id,
        title=title,
        status="approved",
        version=version,
        owners=source_meta.owners,
        acceptance=acceptance,
        source_draft=source_requirement_id,
        source_slice=source_slice,
        change_history=[
            {"ts": utc_now(), "event": "promoted_slice", "from": source_requirement_id}
        ],
    )
    if body:
        meta.change_history.append({"ts": utc_now(), "event": "body_note", "body": body})
    final_requirements.append(meta.to_dict())
    _save_requirement_collection(final_path, final_meta, final_requirements)
    source_meta.change_history.append(
        {
            "ts": utc_now(),
            "event": "slice_promoted",
            "target": final_id,
            "source_slice": source_slice,
        }
    )
    source_meta.updated_at = utc_now()
    if source.get("collection"):
        _replace_requirement_in_collection(source["path"], source_meta)
    else:
        write_frontmatter(source["path"], source_meta.to_dict(), source["body"])
    _audit(
        paths,
        "promote_requirement_slice",
        {"source_requirement_id": source_requirement_id, "final_id": final_id},
    )
    return {"ok": True, "requirement_id": final_id, "path": _rel(paths, final_path)}


def _read_all_todos(
    paths: ProjectPaths,
    scope: str = "all",
    branch: str | None = None,
) -> list[dict[str, Any]]:
    items = []
    for path in _iter_todo_paths(paths, scope=scope, branch=branch):
        meta_raw, body = read_frontmatter(path)
        items.append({"path": path, "meta": TodoMeta.from_dict(meta_raw), "body": body})
    return items


def _metadata_warning(paths: ProjectPaths, path: Path, message: str) -> str:
    try:
        display_path = _rel(paths, path)
    except Exception:
        display_path = str(path)
    return f"{display_path}: {message}"


def _read_all_requirements(
    paths: ProjectPaths,
    warnings: list[str] | None = None,
) -> list[dict[str, Any]]:
    items = []
    for base in [paths.requirements_drafts, paths.requirements_final]:
        for path in sorted(base.glob("*.md")):
            try:
                meta_raw, body = read_frontmatter(path)
            except Exception as exc:
                if warnings is not None:
                    warnings.append(_metadata_warning(paths, path, f"invalid_requirement_frontmatter: {exc}"))
                    continue
                raise RuntimeError(
                    _metadata_warning(paths, path, f"invalid requirement front matter: {exc}")
                ) from exc
            if meta_raw.get("kind") == "requirement_collection":
                for raw_req in meta_raw.get("requirements") or []:
                    try:
                        req = RequirementMeta.from_dict(raw_req)
                    except Exception as exc:
                        if warnings is not None:
                            warnings.append(
                                _metadata_warning(
                                    paths,
                                    path,
                                    f"invalid_requirement_item: keys={sorted(raw_req)} error={exc}",
                                )
                            )
                            continue
                        raise RuntimeError(
                            _metadata_warning(
                                paths,
                                path,
                                f"invalid requirement item: keys={sorted(raw_req)} error={exc}",
                            )
                        ) from exc
                    items.append(
                        {
                            "path": path,
                            "meta": req,
                            "body": _requirement_body_from_meta(req),
                            "collection": True,
                        }
                    )
                continue
            if "id" not in meta_raw:
                if meta_raw:
                    message = f"missing_requirement_id: keys={sorted(meta_raw)}"
                else:
                    message = "unmanaged_requirement_document"
                if warnings is not None:
                    warnings.append(_metadata_warning(paths, path, message))
                    continue
                raise RuntimeError(_metadata_warning(paths, path, message))
            try:
                requirement = RequirementMeta.from_dict(meta_raw)
            except Exception as exc:
                if warnings is not None:
                    warnings.append(_metadata_warning(paths, path, f"invalid_requirement_metadata: {exc}"))
                    continue
                raise RuntimeError(_metadata_warning(paths, path, f"invalid requirement metadata: {exc}")) from exc
            items.append({"path": path, "meta": requirement, "body": body})
    return items


def _read_all_handovers(paths: ProjectPaths) -> list[dict[str, Any]]:
    items = []
    for path in sorted(paths.handover.glob("*.md")):
        meta_raw, body = read_frontmatter(path)
        items.append({"path": path, "meta": HandoverMeta.from_dict(meta_raw), "body": body})
    return items


def _find_todo(paths: ProjectPaths, todo_id: str) -> dict[str, Any]:
    for item in _read_all_todos(paths):
        if item["meta"].id == todo_id:
            return item
    raise RuntimeError(f"TODO not found: {todo_id}")


def _find_requirement(paths: ProjectPaths, requirement_id: str | None) -> dict[str, Any] | None:
    if not requirement_id:
        return None
    for item in _read_all_requirements(paths, warnings=[]):
        if item["meta"].id == requirement_id:
            return item
    return None


def _changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    ignored = {"updated_at", "change_history"}
    return sorted(key for key in after if key not in ignored and before.get(key) != after.get(key))


def _replace_requirement_in_collection(path: Path, requirement: RequirementMeta) -> None:
    meta, _body = read_frontmatter(path)
    requirements = meta.get("requirements") or []
    replaced = False
    for index, raw_req in enumerate(requirements):
        if raw_req.get("id") == requirement.id:
            requirements[index] = requirement.to_dict()
            replaced = True
            break
    if not replaced:
        requirements.append(requirement.to_dict())
    _save_requirement_collection(path, meta, requirements)


def _remove_requirement_from_collection(path: Path, requirement_id: str) -> None:
    meta, _body = read_frontmatter(path)
    requirements = [
        raw_req for raw_req in (meta.get("requirements") or [])
        if raw_req.get("id") != requirement_id
    ]
    _save_requirement_collection(path, meta, requirements)


def _requirement_body_from_meta(requirement: RequirementMeta) -> str:
    body = f"# {requirement.title}\n\n"
    if requirement.acceptance:
        body += "## 验收标准\n\n" + "\n".join(f"- {item}" for item in requirement.acceptance) + "\n"
    return body


def _format_changelog_entry(
    message: str,
    requirement_id: str | None = None,
    todo_id: str | None = None,
) -> str:
    refs = []
    if requirement_id:
        refs.append(f"需求: {requirement_id}")
    if todo_id:
        refs.append(f"任务: {todo_id}")
    suffix = f" ({'; '.join(refs)})" if refs else ""
    return f"- {message.strip()}{suffix}"


def _normalize_changelog_category(category: str) -> str:
    return CHANGELOG_CATEGORY_ALIASES.get(category, category)


def _insert_changelog_entry(text: str, category: str, entry: str) -> str:
    lines = text.splitlines()
    try:
        unreleased_index = lines.index("## [Unreleased]")
    except ValueError:
        lines.extend(["", "## [Unreleased]", ""])
        unreleased_index = len(lines) - 2

    next_version_index = len(lines)
    for idx in range(unreleased_index + 1, len(lines)):
        if lines[idx].startswith("## ") and lines[idx] != "## [Unreleased]":
            next_version_index = idx
            break

    category_heading = f"### {CHANGELOG_CATEGORY_HEADINGS.get(category, category)}"
    category_index = None
    for idx in range(unreleased_index + 1, next_version_index):
        if lines[idx] == category_heading:
            category_index = idx
            break

    if category_index is None:
        insert_at = unreleased_index + 1
        while insert_at < len(lines) and lines[insert_at] == "":
            insert_at += 1
        lines[insert_at:insert_at] = [category_heading, entry, ""]
    else:
        insert_at = category_index + 1
        while insert_at < next_version_index and lines[insert_at].startswith("- "):
            insert_at += 1
        if entry not in lines:
            lines.insert(insert_at, entry)

    return "\n".join(lines).rstrip() + "\n"


def _extract_unreleased_changelog_entries(text: str) -> list[dict[str, str]]:
    heading_to_category = {value: key for key, value in CHANGELOG_CATEGORY_HEADINGS.items()}
    lines = text.splitlines()
    try:
        unreleased_index = lines.index("## [Unreleased]")
    except ValueError:
        return []
    entries = []
    current_category = "Changed"
    for line in lines[unreleased_index + 1:]:
        if line.startswith("## "):
            break
        if line.startswith("### "):
            heading = line.removeprefix("### ").strip()
            current_category = heading_to_category.get(heading, _normalize_changelog_category(heading))
            continue
        if line.startswith("- "):
            entries.append({"category": current_category, "entry": line})
    return entries


def _format_work_branches_text(branches: list[dict[str, Any]], include_completed: bool) -> str:
    title = "\u5206\u652f\u5de5\u4f5c\u8fdb\u5c55\uff08\u5305\u542b\u5df2\u5b8c\u7ed3\uff09" if include_completed else "\u672a\u5b8c\u6210\u5206\u652f\u5de5\u4f5c"
    if not branches:
        return f"{title}\n\n\u6682\u65e0\u9700\u8981\u5c55\u793a\u7684\u5206\u652f\u5de5\u4f5c\u3002"
    lines = [title, ""]
    for branch in branches:
        marker = "\u5f53\u524d\u5206\u652f\uff0c" if branch.get("current") else ""
        completed = "\u5df2\u5b8c\u7ed3" if branch.get("completed") else "\u8fdb\u884c\u4e2d"
        exists = "Git \u5206\u652f\u5b58\u5728" if branch.get("exists_in_git") else "Git \u5206\u652f\u4e0d\u5b58\u5728"
        lines.append(f"- {branch['branch']}\uff1a{marker}{completed}\uff0c\u8fdb\u5ea6 {branch['progress_percent']}%\uff0c{exists}")
        counts = branch.get("todo_counts") or {}
        if counts:
            counts_text = "\uff0c".join(f"{status} {count}" for status, count in sorted(counts.items()))
            lines.append(f"  TODO\uff1a{counts_text}")
        note = branch.get("progress_note")
        if note:
            lines.append(f"  \u8fdb\u5c55\u5907\u6ce8\uff1a{note}")
        unfinished = branch.get("unfinished_todos") or []
        if unfinished:
            lines.append("  \u672a\u5b8c\u6210\u4efb\u52a1\uff1a")
            for todo in unfinished:
                lines.append(f"  - {todo['id']}\uff5c{todo['status']}\uff5c{todo['priority']}\uff5c{todo['title']}")
    return "\n".join(lines)


def _todo_summary(item: dict[str, Any]) -> dict[str, Any]:
    meta: TodoMeta = item["meta"]
    data = meta.to_dict()
    data["path"] = str(item["path"])
    return data


def _count_by_status(items: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = item.status
        counts[status] = counts.get(status, 0) + 1
    return counts


def _kind_for_path(path: str) -> str:
    if path.startswith("tests/"):
        return "test"
    if path.startswith("docs/"):
        return "doc"
    if path.startswith("todo/"):
        return "todo"
    if path.startswith("src/"):
        return "source"
    return "other"


def _write_static_docs(paths: ProjectPaths) -> None:
    readme = paths.root / "README.md"
    if not readme.exists():
        readme.write_text(DEFAULT_README_TEXT, encoding="utf-8", newline="\n")
    agents = paths.root / "AGENTS.md"
    if not agents.exists():
        agents.write_text(DEFAULT_AGENTS_TEXT, encoding="utf-8", newline="\n")
    changelog = paths.root / "CHANGELOG.md"
    if not changelog.exists():
        changelog.write_text("# \u7248\u672c\u53d8\u66f4\u8bb0\u5f55\n\n## [Unreleased]\n\n", encoding="utf-8", newline="\n")
    version = paths.root / "VERSION"
    if not version.exists():
        version.write_text("0.1.0\n", encoding="utf-8")
    plan = paths.docs / "project-dev-management-implementation-plan.md"
    if not plan.exists():
        plan.write_text(
            "# Project Development Management Skill Implementation Plan\n\n"
            "This project has been onboarded into project-dev-management. Git is the source "
            "of truth, `.pm-skill` is the control plane, and TODO, requirement, handover, "
            "CHANGELOG, and audit files form the project-management surface.\n\n"
            "## Core Workflow\n\n"
            "- Recover project state with `pm-skill show-status --json`.\n"
            "- Manage branch-scoped draft and formal requirements.\n"
            "- Link TODOs to requirements before implementation.\n"
            "- Record version changes in `CHANGELOG.md` when formal requirement work is done.\n",
            encoding="utf-8",
            newline="\n",
        )
    adr = paths.adr / "ADR-0001-local-first-repo-control-plane.md"
    if not adr.exists():
        adr.write_text(
            "# ADR-0001: Local-first repository control plane\n\n"
            "## Status\n\nAccepted\n\n"
            "## Decision\n\n"
            "Use repository-managed `.pm-skill` metadata and a Python CLI before introducing "
            "remote services, MCP, or vector storage.\n\n"
            "## Consequences\n\n"
            "The MVP remains easy to inspect, back up, and run offline. Team sharing and richer "
            "semantic retrieval are deferred until the local workflow is proven.\n",
            encoding="utf-8",
            newline="\n",
        )
    skill = paths.skill / "SKILL.md"
    if not skill.exists():
        skill.write_text(
            "---\n"
            "name: project-dev-management\n"
            "description: Recover and manage local Git project state across Codex sessions using "
            "the repository's .pm-skill control plane, TODO files, requirements, baselines, "
            "checks, audit logs, and handover documents. Use when a user asks to resume project "
            "work, manage TODOs, create a handover, initialize project management metadata, or "
            "inspect project state.\n"
            "---\n\n"
            "# Project Dev Management\n\n"
            "Start by running `pm-skill show-status --json` from the repository root. Use "
            "the CLI for TODO, requirement, baseline, check, index, and handover operations "
            "instead of editing `.pm-skill` files by hand.\n",
            encoding="utf-8",
            newline="\n",
        )


def _write_onboarding_report(
    paths: ProjectPaths,
    initialized: bool,
    index_result: dict[str, Any],
) -> str:
    report = paths.docs / "PROJECT_ONBOARDING.md"
    git = GitClient(paths.root)
    top_dirs = [
        item.name
        for item in sorted(paths.root.iterdir(), key=lambda p: p.name.lower())
        if item.is_dir() and item.name not in {".git", ".pm-skill", ".codex", "__pycache__"}
    ]
    report.write_text(
        "# Existing Project Onboarding\n\n"
        f"- Root: `{paths.root}`\n"
        f"- Git branch: `{git.branch()}`\n"
        f"- HEAD: `{git.head() or 'no commits yet'}`\n"
        f"- Initialized control plane: `{str(initialized).lower()}`\n"
        f"- Indexed files: `{index_result.get('indexed_files')}`\n"
        f"- Top-level folders: {', '.join(top_dirs) if top_dirs else 'none'}\n\n"
        "## Next Steps\n\n"
        "- Run `pm-skill show-status --json` to inspect the managed state.\n"
        "- Create or update draft requirements in the branch requirement collection.\n"
        "- Link new TODOs to approved or draft requirements before implementation.\n",
        encoding="utf-8",
        newline="\n",
    )
    return _rel(paths, report)
