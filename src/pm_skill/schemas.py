from __future__ import annotations

from typing import Any

from .pydantic_models import pydantic_schema


def schemas() -> dict[str, dict[str, Any]]:
    base_string = {"type": ["string", "null"]}
    fallback = {
        "command-envelope.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["request_id", "command", "args"],
            "properties": {
                "request_id": {"type": "string"},
                "command": {"type": "string"},
                "args": {"type": "object"},
                "actor": {"type": "string"},
                "session_id": base_string,
                "approval": {"type": "string"},
                "dry_run": {"type": "boolean"},
                "metadata": {"type": "object"},
            },
            "additionalProperties": False,
        },
        "project-manifest.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["project_id", "repo_uid", "display_name", "default_branch", "storage"],
            "properties": {
                "project_id": {"type": "string"},
                "repo_uid": {"type": "string"},
                "display_name": {"type": "string"},
                "default_branch": {"type": "string"},
                "remote": {"type": ["object", "null"]},
                "storage": {"type": "object", "required": ["mode"]},
                "index_scope": {
                    "type": "object",
                    "properties": {
                        "paths": {"oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]},
                        "extensions": {"oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]},
                    },
                },
                "exclude_scope": {
                    "type": "object",
                    "properties": {
                        "paths": {"oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]},
                        "extensions": {"oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]},
                    },
                },
                "active_baseline": base_string,
                "latest_handover": base_string,
                "last_indexed_commit": base_string,
                "policy_ref": {"type": "string"},
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"},
            },
        },
        "todo.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id", "title", "status", "priority"],
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "status": {"enum": ["draft", "ready", "in_progress", "blocked", "done", "cancelled"]},
                "priority": {"enum": ["P0", "P1", "P2", "P3"]},
                "assignee": {"type": "string"},
                "source_requirement": base_string,
                "branch": base_string,
                "baseline_ref": base_string,
                "issue_refs": {"type": "array"},
                "pr_refs": {"type": "array"},
                "blocked_by": {"type": "array"},
                "updated_at": {"type": "string"},
            },
        },
        "requirement.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id", "title", "status"],
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "status": {"enum": ["draft", "approved", "superseded", "rejected"]},
                "version": base_string,
                "owners": {"type": "array"},
                "depends_on": {"type": "array"},
                "acceptance": {"type": "array"},
                "baseline_ref": base_string,
                "change_history": {"type": "array"},
            },
        },
        "handover.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id", "from_session", "to_session", "branch", "status"],
            "properties": {
                "id": {"type": "string"},
                "from_session": {"type": "string"},
                "to_session": {"type": "string"},
                "branch": {"type": "string"},
                "head_commit": base_string,
                "status": {"enum": ["paused", "complete", "blocked"]},
                "related_todos": {"type": "array"},
                "blocked_by": {"type": "array"},
                "next_actions": {"type": "array"},
                "created_at": {"type": "string"},
            },
        },
    }
    return {name: pydantic_schema(name) or schema for name, schema in fallback.items()}
