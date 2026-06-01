from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

try:  # pragma: no cover - exercised when optional runtime dependency is installed.
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True

    class CommandEnvelopeModel(BaseModel):
        request_id: str
        command: str
        args: dict[str, Any] = Field(default_factory=dict)
        actor: str = "agent"
        session_id: str | None = None
        approval: str = "not_required"
        dry_run: bool = False
        metadata: dict[str, Any] = Field(default_factory=dict)

    class StorageModel(BaseModel):
        mode: str = "repo_only"

    class IndexScopeModel(BaseModel):
        paths: str | list[str] = "*"
        extensions: str | list[str] = "*"

    class ExcludeScopeModel(BaseModel):
        paths: str | list[str] = Field(default_factory=list)
        extensions: str | list[str] = Field(default_factory=list)

    class ManifestModel(BaseModel):
        project_id: str
        repo_uid: str
        display_name: str
        default_branch: str
        remote: dict[str, Any] | None = None
        storage: StorageModel = Field(default_factory=StorageModel)
        index_scope: IndexScopeModel = Field(default_factory=IndexScopeModel)
        exclude_scope: ExcludeScopeModel = Field(default_factory=ExcludeScopeModel)
        active_baseline: str | None = None
        latest_handover: str | None = None
        last_indexed_commit: str | None = None
        policy_ref: str = "docs/standards/development-policy.yaml"
        created_at: str = Field(default_factory=_utc_now)
        updated_at: str = Field(default_factory=_utc_now)

    class TodoMetaModel(BaseModel):
        id: str
        title: str
        status: Literal["draft", "ready", "in_progress", "blocked", "done", "cancelled"] = "draft"
        priority: Literal["P0", "P1", "P2", "P3"] = "P2"
        assignee: str = "agent"
        source_requirement: str | None = None
        branch: str | None = None
        baseline_ref: str | None = None
        issue_refs: list[Any] = Field(default_factory=list)
        pr_refs: list[Any] = Field(default_factory=list)
        blocked_by: list[str] = Field(default_factory=list)
        updated_at: str = Field(default_factory=_utc_now)

    class RequirementMetaModel(BaseModel):
        id: str
        title: str
        status: Literal["draft", "approved", "superseded", "rejected"] = "draft"
        version: str | None = None
        owners: list[str] = Field(default_factory=list)
        depends_on: list[str] = Field(default_factory=list)
        acceptance: list[str] = Field(default_factory=list)
        baseline_ref: str | None = None
        change_history: list[Any] = Field(default_factory=list)
        issue_refs: list[Any] = Field(default_factory=list)
        pr_refs: list[Any] = Field(default_factory=list)
        source_draft: str | None = None
        source_slice: str | None = None
        created_at: str = Field(default_factory=_utc_now)
        updated_at: str = Field(default_factory=_utc_now)

    class HandoverMetaModel(BaseModel):
        id: str
        from_session: str
        to_session: str = "any"
        branch: str = ""
        head_commit: str | None = None
        status: Literal["paused", "complete", "blocked"] = "paused"
        related_todos: list[str] = Field(default_factory=list)
        blocked_by: list[str] = Field(default_factory=list)
        next_actions: list[str] = Field(default_factory=list)
        created_at: str = Field(default_factory=_utc_now)

    class WorkPackageMetaModel(BaseModel):
        todo_id: str
        title: str
        branch: str
        requirement_id: str | None = None
        status: Literal["active", "archived"] = "active"
        created_at: str = Field(default_factory=_utc_now)
        updated_at: str = Field(default_factory=_utc_now)
        meta: dict[str, Any] = Field(default_factory=dict)

    class TemplateHashRecordModel(BaseModel):
        path: str
        sha256: str
        managed: bool = True
        updated_at: str = Field(default_factory=_utc_now)

except Exception:  # pragma: no cover - fallback is covered by local test environment.
    PYDANTIC_AVAILABLE = False

    class _FallbackModel:
        def __init__(self, **data: Any) -> None:
            self.__dict__.update(data)

        @classmethod
        def model_validate(cls, data: dict[str, Any]) -> "_FallbackModel":
            return cls(**data)

        def model_dump(self) -> dict[str, Any]:
            return dict(self.__dict__)

        @classmethod
        def model_json_schema(cls) -> dict[str, Any]:
            return {"type": "object"}

    CommandEnvelopeModel = _FallbackModel
    StorageModel = _FallbackModel
    IndexScopeModel = _FallbackModel
    ExcludeScopeModel = _FallbackModel
    ManifestModel = _FallbackModel
    TodoMetaModel = _FallbackModel
    RequirementMetaModel = _FallbackModel
    HandoverMetaModel = _FallbackModel
    WorkPackageMetaModel = _FallbackModel
    TemplateHashRecordModel = _FallbackModel


MODEL_BY_SCHEMA = {
    "command-envelope.schema.json": CommandEnvelopeModel,
    "project-manifest.schema.json": ManifestModel,
    "todo.schema.json": TodoMetaModel,
    "requirement.schema.json": RequirementMetaModel,
    "handover.schema.json": HandoverMetaModel,
    "work-package.schema.json": WorkPackageMetaModel,
    "template-hash-record.schema.json": TemplateHashRecordModel,
}


def validate_command_envelope(data: dict[str, Any]) -> dict[str, Any]:
    envelope = CommandEnvelopeModel.model_validate(data)
    return envelope.model_dump()


def pydantic_schema(name: str) -> dict[str, Any] | None:
    if not PYDANTIC_AVAILABLE:
        return None
    model = MODEL_BY_SCHEMA.get(name)
    return model.model_json_schema() if model else None
