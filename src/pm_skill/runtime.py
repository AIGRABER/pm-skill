from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from .git_client import GitClient
from .json_io import append_jsonl, read_json
from .models import Manifest, utc_now
from .paths import ProjectPaths
from .policy import DEFAULT_POLICY, is_protected_branch, read_policy
from .scope import normalize_exclude_scope


@dataclass(frozen=True)
class CommandEffects:
    read_repo: bool = True
    write_repo: bool = False
    git_read: bool = True
    git_write: bool = False
    run_shell: bool = False
    network: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


@dataclass
class RunContext:
    paths: ProjectPaths
    git: GitClient | None
    policy: dict[str, Any]
    manifest: Manifest | None
    branch: str
    head: str | None
    dirty_files: list[str]
    protected_branch: bool
    request_id: str
    actor: str
    session_id: str
    approval: str
    dry_run: bool
    metadata: dict[str, Any] = field(default_factory=dict)


CommandHandler = Callable[[RunContext, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class CommandSpec:
    name: str
    handler: CommandHandler
    aliases: tuple[str, ...] = ()
    arg_names: tuple[str, ...] = ()
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    effects: CommandEffects = field(default_factory=CommandEffects)
    requires_manifest: bool = True
    requires_clean_worktree: bool = False
    allow_protected_branch: bool = True
    audit: bool = True
    discover_repo: bool = True

    def names(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "aliases": list(self.aliases),
            "description": self.description,
            "arg_names": list(self.arg_names),
            "effects": self.effects.to_dict(),
            "requires_manifest": self.requires_manifest,
            "requires_clean_worktree": self.requires_clean_worktree,
            "allow_protected_branch": self.allow_protected_branch,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }

    def tool_schema(self) -> dict[str, Any]:
        properties = {
            "project_path": {
                "type": "string",
                "default": ".",
                "description": "Target project root.",
            }
        }
        required: list[str] = []
        if self.input_schema:
            properties.update(self.input_schema.get("properties", {}))
            required = list(self.input_schema.get("required", []))
        else:
            for name in self.arg_names:
                properties[name] = {"type": ["string", "array", "boolean", "object", "null"]}
        return {
            "description": self.description or f"Run {self.name}.",
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
            "effects": self.effects.to_dict(),
        }


@dataclass
class RunEvent:
    event_type: str
    command: str
    request_id: str
    actor: str
    session_id: str
    ok: bool
    args: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    approval: str = "not_required"
    before_ref: str | None = None
    after_ref: str | None = None
    error: str | None = None
    target: str | None = None
    ts: str = field(default_factory=utc_now)

    def to_audit_dict(self) -> dict[str, Any]:
        args_digest = hashlib.sha256(
            json.dumps(self.args, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return {
            "ts": self.ts,
            "actor": self.actor,
            "session_id": self.session_id,
            "command": self.command,
            "args_digest": args_digest,
            "approval": self.approval,
            "before_ref": self.before_ref,
            "after_ref": self.after_ref,
            "ok": self.ok,
            "error": self.error,
            "event_type": self.event_type,
            "request_id": self.request_id,
            "target": self.target,
            "details": self.details,
        }


@dataclass
class WorkflowStep:
    name: str
    status: str = "running"
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def finish(self, result: dict[str, Any] | None = None) -> None:
        self.status = "completed"
        self.finished_at = utc_now()
        self.result = result or {}

    def fail(self, error: str) -> None:
        self.status = "failed"
        self.finished_at = utc_now()
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowRun:
    id: str
    command: str
    branch: str
    status: str = "running"
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    steps: list[WorkflowStep] = field(default_factory=list)
    error: str | None = None

    @classmethod
    def start(cls, command: str, branch: str) -> "WorkflowRun":
        compact_ts = utc_now().replace("-", "").replace(":", "")
        return cls(id=f"WF-{compact_ts}", command=command, branch=branch)

    def start_step(self, name: str) -> WorkflowStep:
        step = WorkflowStep(name=name)
        self.steps.append(step)
        return step

    def finish_step(self, step: WorkflowStep, result: dict[str, Any] | None = None) -> None:
        step.finish(result)

    def fail_step(self, step: WorkflowStep, error: str) -> None:
        step.fail(error)
        self.fail(error)

    def finish(self) -> None:
        self.status = "completed"
        self.finished_at = utc_now()

    def fail(self, error: str) -> None:
        self.status = "failed"
        self.finished_at = utc_now()
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "branch": self.branch,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "steps": [step.to_dict() for step in self.steps],
        }


def build_run_context(project_path: str | Path, envelope: dict[str, Any], spec: CommandSpec) -> RunContext:
    root = Path(project_path).resolve()
    paths = ProjectPaths.discover(root) if spec.discover_repo else ProjectPaths(root)
    git: GitClient | None = None
    branch = ""
    head: str | None = None
    dirty_files: list[str] = []
    manifest: Manifest | None = None
    try:
        git = GitClient(paths.root)
        branch = git.branch()
        head = git.head()
        manifest = Manifest.from_dict(read_json(paths.manifest)) if paths.manifest.exists() else None
        exclude_paths: list[str] | None = []
        exclude_extensions: set[str] | None = set()
        if manifest:
            exclude_paths, exclude_extensions = normalize_exclude_scope(
                paths,
                manifest.exclude_scope.paths,
                manifest.exclude_scope.extensions,
            )
        dirty_files = git.status_porcelain(
            exclude_paths=exclude_paths,
            exclude_extensions=exclude_extensions,
        )
    except Exception:
        if spec.discover_repo:
            raise
    policy = read_policy(paths) if paths.policy.exists() else DEFAULT_POLICY.copy()
    protected = is_protected_branch(branch, policy) if branch else False
    return RunContext(
        paths=paths,
        git=git,
        policy=policy,
        manifest=manifest,
        branch=branch,
        head=head,
        dirty_files=dirty_files,
        protected_branch=protected,
        request_id=envelope.get("request_id", "local"),
        actor=envelope.get("actor", "agent"),
        session_id=envelope.get("session_id") or "local",
        approval=envelope.get("approval", "not_required"),
        dry_run=bool(envelope.get("dry_run", False)),
        metadata=envelope.get("metadata") or {},
    )


def preflight(spec: CommandSpec, context: RunContext) -> list[str]:
    checks: list[str] = []
    if spec.requires_manifest and not context.manifest:
        raise RuntimeError("Project is not initialized. Run pm-skill init-project first.")
    checks.append("manifest")
    if spec.requires_clean_worktree and context.dirty_files:
        raise RuntimeError("Refusing to run command with a dirty worktree.")
    checks.append("clean_worktree")
    if not spec.allow_protected_branch and context.protected_branch:
        raise RuntimeError(f"Refusing to run {spec.name} on protected branch {context.branch}.")
    checks.append("protected_branch")
    return checks


def record_event(
    context: RunContext,
    spec: CommandSpec,
    event_type: str,
    args: dict[str, Any],
    ok: bool,
    details: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    if not spec.audit:
        return
    if not context.paths.pm.exists():
        return
    context.paths.audit.mkdir(parents=True, exist_ok=True)
    event = RunEvent(
        event_type=event_type,
        command=spec.name,
        request_id=context.request_id,
        actor=context.actor,
        session_id=context.session_id,
        ok=ok,
        args=args,
        details=details or {},
        approval=context.approval,
        before_ref=context.head,
        after_ref=context.git.head() if context.git else context.head,
        error=error,
        target=context.branch or str(context.paths.root),
    )
    append_jsonl(context.paths.audit_log, event.to_audit_dict())


def execute_with_runtime(project_path: str | Path, envelope: dict[str, Any], spec: CommandSpec) -> dict[str, Any]:
    args = envelope.get("args") or {}
    context = build_run_context(project_path, envelope, spec)
    record_event(
        context,
        spec,
        "command_started",
        args,
        ok=True,
        details={"effects": spec.effects.to_dict()},
    )
    try:
        checks = preflight(spec, context)
        record_event(context, spec, "preflight_passed", args, ok=True, details={"checks": checks})
        if context.dry_run and (spec.effects.write_repo or spec.effects.git_write or spec.effects.run_shell):
            result = {
                "ok": True,
                "mode": "dry_run",
                "command": spec.name,
                "effects": spec.effects.to_dict(),
            }
        else:
            result = spec.handler(context, args)
        record_event(
            context,
            spec,
            "command_completed",
            args,
            ok=bool(result.get("ok", True)),
            details={"result_keys": sorted(result.keys())},
        )
        return result
    except Exception as exc:
        record_event(context, spec, "command_failed", args, ok=False, error=str(exc))
        raise

