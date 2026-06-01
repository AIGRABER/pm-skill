from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from .pydantic_models import (
    HandoverMetaModel,
    ManifestModel,
    PYDANTIC_AVAILABLE,
    RequirementMetaModel,
    TemplateHashRecordModel,
    TodoMetaModel,
    WorkPackageMetaModel,
)

TODO_STATUSES = {"draft", "ready", "in_progress", "blocked", "done", "cancelled"}
TODO_PRIORITIES = {"P0", "P1", "P2", "P3"}
REQUIREMENT_STATUSES = {"draft", "approved", "superseded", "rejected"}
HANDOVER_STATUSES = {"paused", "complete", "blocked"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def strip_nulls(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: strip_nulls(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [strip_nulls(v) for v in value]
    return value


@dataclass
class Storage:
    mode: str = "repo_only"

    def __post_init__(self) -> None:
        if not self.mode:
            raise ValueError("storage.mode is required")


@dataclass
class IndexScope:
    paths: str | list[str] = "*"
    extensions: str | list[str] = "*"

    def __post_init__(self) -> None:
        self.paths = _ensure_string_or_string_list("index_scope.paths", self.paths)
        self.extensions = _ensure_string_or_string_list("index_scope.extensions", self.extensions)


@dataclass
class ExcludeScope:
    paths: str | list[str] = field(default_factory=list)
    extensions: str | list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.paths = _ensure_string_or_string_list("exclude_scope.paths", self.paths)
        self.extensions = _ensure_string_or_string_list("exclude_scope.extensions", self.extensions)


@dataclass
class Manifest:
    project_id: str
    repo_uid: str
    display_name: str
    default_branch: str
    remote: dict[str, Any] | None = None
    storage: Storage = field(default_factory=Storage)
    index_scope: IndexScope = field(default_factory=IndexScope)
    exclude_scope: ExcludeScope = field(default_factory=ExcludeScope)
    active_baseline: str | None = None
    latest_handover: str | None = None
    last_indexed_commit: str | None = None
    policy_ref: str = "docs/standards/development-policy.yaml"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in ["project_id", "repo_uid", "display_name", "default_branch"]:
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} is required")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Manifest":
        if PYDANTIC_AVAILABLE:
            data = ManifestModel.model_validate(data).model_dump()
        storage = data.get("storage") or {"mode": "repo_only"}
        index_scope = data.get("index_scope") or {}
        exclude_scope = data.get("exclude_scope") or {}
        return cls(
            project_id=data["project_id"],
            repo_uid=data["repo_uid"],
            display_name=data.get("display_name") or data["project_id"],
            default_branch=data.get("default_branch") or "master",
            remote=data.get("remote"),
            storage=Storage(**storage) if isinstance(storage, dict) else Storage(),
            index_scope=IndexScope(**index_scope) if isinstance(index_scope, dict) else IndexScope(),
            exclude_scope=ExcludeScope(**exclude_scope) if isinstance(exclude_scope, dict) else ExcludeScope(),
            active_baseline=data.get("active_baseline"),
            latest_handover=data.get("latest_handover"),
            last_indexed_commit=data.get("last_indexed_commit"),
            policy_ref=data.get("policy_ref") or "docs/standards/development-policy.yaml",
            created_at=data.get("created_at") or utc_now(),
            updated_at=data.get("updated_at") or utc_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TodoMeta:
    id: str
    title: str
    status: Literal["draft", "ready", "in_progress", "blocked", "done", "cancelled"] = "draft"
    priority: Literal["P0", "P1", "P2", "P3"] = "P2"
    assignee: str = "agent"
    source_requirement: str | None = None
    branch: str | None = None
    baseline_ref: str | None = None
    issue_refs: list[Any] = field(default_factory=list)
    pr_refs: list[Any] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("todo.id is required")
        if not self.title:
            raise ValueError("todo.title is required")
        if self.status not in TODO_STATUSES:
            raise ValueError(f"Invalid todo.status: {self.status}")
        if self.priority not in TODO_PRIORITIES:
            raise ValueError(f"Invalid todo.priority: {self.priority}")
        self.issue_refs = _ensure_list("todo.issue_refs", self.issue_refs)
        self.pr_refs = _ensure_list("todo.pr_refs", self.pr_refs)
        self.blocked_by = _ensure_list("todo.blocked_by", self.blocked_by)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TodoMeta":
        if PYDANTIC_AVAILABLE:
            data = TodoMetaModel.model_validate(data).model_dump()
        return cls(
            id=data["id"],
            title=data["title"],
            status=data.get("status", "draft"),
            priority=data.get("priority", "P2"),
            assignee=data.get("assignee", "agent"),
            source_requirement=data.get("source_requirement"),
            branch=data.get("branch"),
            baseline_ref=data.get("baseline_ref"),
            issue_refs=data.get("issue_refs") or [],
            pr_refs=data.get("pr_refs") or [],
            blocked_by=data.get("blocked_by") or [],
            updated_at=data.get("updated_at") or utc_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RequirementMeta:
    id: str
    title: str
    status: Literal["draft", "approved", "superseded", "rejected"] = "draft"
    version: str | None = None
    owners: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    acceptance: list[str] = field(default_factory=list)
    baseline_ref: str | None = None
    change_history: list[Any] = field(default_factory=list)
    issue_refs: list[Any] = field(default_factory=list)
    pr_refs: list[Any] = field(default_factory=list)
    source_draft: str | None = None
    source_slice: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("requirement.id is required")
        if not self.title:
            raise ValueError("requirement.title is required")
        if self.status not in REQUIREMENT_STATUSES:
            raise ValueError(f"Invalid requirement.status: {self.status}")
        self.owners = _ensure_list("requirement.owners", self.owners)
        self.depends_on = _ensure_list("requirement.depends_on", self.depends_on)
        self.acceptance = _ensure_list("requirement.acceptance", self.acceptance)
        self.change_history = _ensure_list("requirement.change_history", self.change_history)
        self.issue_refs = _ensure_list("requirement.issue_refs", self.issue_refs)
        self.pr_refs = _ensure_list("requirement.pr_refs", self.pr_refs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementMeta":
        if PYDANTIC_AVAILABLE:
            data = RequirementMetaModel.model_validate(data).model_dump()
        return cls(
            id=data["id"],
            title=data["title"],
            status=data.get("status", "draft"),
            version=data.get("version"),
            owners=data.get("owners") or [],
            depends_on=data.get("depends_on") or [],
            acceptance=data.get("acceptance") or [],
            baseline_ref=data.get("baseline_ref"),
            change_history=data.get("change_history") or [],
            issue_refs=data.get("issue_refs") or [],
            pr_refs=data.get("pr_refs") or [],
            source_draft=data.get("source_draft"),
            source_slice=data.get("source_slice"),
            created_at=data.get("created_at") or utc_now(),
            updated_at=data.get("updated_at") or utc_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HandoverMeta:
    id: str
    from_session: str
    to_session: str = "any"
    branch: str = ""
    head_commit: str | None = None
    status: Literal["paused", "complete", "blocked"] = "paused"
    related_todos: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("handover.id is required")
        if not self.from_session:
            raise ValueError("handover.from_session is required")
        if self.status not in HANDOVER_STATUSES:
            raise ValueError(f"Invalid handover.status: {self.status}")
        self.related_todos = _ensure_list("handover.related_todos", self.related_todos)
        self.blocked_by = _ensure_list("handover.blocked_by", self.blocked_by)
        self.next_actions = _ensure_list("handover.next_actions", self.next_actions)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HandoverMeta":
        if PYDANTIC_AVAILABLE:
            data = HandoverMetaModel.model_validate(data).model_dump()
        return cls(
            id=data["id"],
            from_session=data.get("from_session", "unknown"),
            to_session=data.get("to_session", "any"),
            branch=data.get("branch", ""),
            head_commit=data.get("head_commit"),
            status=data.get("status", "paused"),
            related_todos=data.get("related_todos") or [],
            blocked_by=data.get("blocked_by") or [],
            next_actions=data.get("next_actions") or [],
            created_at=data.get("created_at") or utc_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkPackageMeta:
    todo_id: str
    title: str
    branch: str
    requirement_id: str | None = None
    status: Literal["active", "archived"] = "active"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.todo_id:
            raise ValueError("work_package.todo_id is required")
        if not self.title:
            raise ValueError("work_package.title is required")
        if not self.branch:
            raise ValueError("work_package.branch is required")
        if self.status not in {"active", "archived"}:
            raise ValueError(f"Invalid work_package.status: {self.status}")
        if not isinstance(self.meta, dict):
            raise ValueError("work_package.meta must be a mapping")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkPackageMeta":
        if PYDANTIC_AVAILABLE:
            data = WorkPackageMetaModel.model_validate(data).model_dump()
        return cls(
            todo_id=data["todo_id"],
            title=data["title"],
            branch=data["branch"],
            requirement_id=data.get("requirement_id"),
            status=data.get("status", "active"),
            created_at=data.get("created_at") or utc_now(),
            updated_at=data.get("updated_at") or utc_now(),
            meta=data.get("meta") or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TemplateHashRecord:
    path: str
    sha256: str
    managed: bool = True
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("template_hash.path is required")
        if not self.sha256:
            raise ValueError("template_hash.sha256 is required")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemplateHashRecord":
        if PYDANTIC_AVAILABLE:
            data = TemplateHashRecordModel.model_validate(data).model_dump()
        return cls(
            path=data["path"],
            sha256=data["sha256"],
            managed=bool(data.get("managed", True)),
            updated_at=data.get("updated_at") or utc_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEvent:
    ts: str
    actor: str
    session_id: str
    command: str
    args_digest: str
    approval: str
    before_ref: str | None
    after_ref: str | None
    ok: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _ensure_list(field_name: str, value: Any) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _ensure_string_or_string_list(field_name: str, value: Any) -> str | list[str]:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise ValueError(f"{field_name} must be a string or a list of strings")
