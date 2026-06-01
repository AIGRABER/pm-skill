from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any
import fnmatch

import yaml

from .paths import ProjectPaths


DEFAULT_POLICY: dict[str, Any] = {
    "version": "1.0",
    "baseline_strategy": {
        "mode": "semver_tag",
        "require_clean_worktree": True,
        "changelog_required": True,
    },
    "review_policy": {
        "protected_branches": ["master", "main", "release/*"],
        "min_reviewers": 0,
        "require_passing_checks": False,
    },
    "branch_naming": {
        "feature": "feat/{todo_id}-{slug}",
        "fix": "fix/{todo_id}-{slug}",
        "chore": "chore/{slug}",
    },
    "commit_policy": {
        "conventional_commits": True,
        "require_trailers": ["Task", "Requirement"],
    },
    "handover_policy": {
        "require_handover_for_paused_work": True,
        "max_handover_age_hours": 72,
    },
    "index_policy": {
        "exclude_globs": [
            ".git/**",
            ".env",
            "**/.env",
            "**/*.pem",
            "**/*.key",
            "**/node_modules/**",
            "**/dist/**",
            "**/.venv/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.egg-info/**",
            ".pytest_cache/**",
            ".ruff_cache/**",
        ],
    },
    "check_profiles": {
        "default": [
            "pm-skill check-docs-encoding --json",
            "py -3.11 -m unittest discover -s tests",
        ],
        "lint": ["py -3.11 -m ruff check ."],
    },
}


def read_policy(paths: ProjectPaths) -> dict[str, Any]:
    if not paths.policy.exists():
        return DEFAULT_POLICY.copy()
    with paths.policy.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def write_default_policy(paths: ProjectPaths) -> None:
    paths.policy.parent.mkdir(parents=True, exist_ok=True)
    with paths.policy.open("w", encoding="utf-8", newline="\n") as handle:
        yaml.safe_dump(DEFAULT_POLICY, handle, allow_unicode=True, sort_keys=False)


def is_protected_branch(branch: str, policy: dict[str, Any]) -> bool:
    patterns = policy.get("review_policy", {}).get("protected_branches", [])
    posix = PurePosixPath(branch)
    return any(posix.match(pattern) for pattern in patterns)


def excluded_from_index(path: str, policy: dict[str, Any]) -> bool:
    patterns = policy.get("index_policy", {}).get("exclude_globs", [])
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized == ".git" or normalized.startswith(".git/"):
        return True
    if normalized == ".env" or normalized.endswith("/.env"):
        return True
    if "__pycache__/" in normalized or normalized.endswith(".pyc"):
        return True
    posix = PurePosixPath(normalized)
    return any(
        posix.match(pattern)
        or fnmatch.fnmatch(normalized, pattern)
        or normalized == pattern.rstrip("/")
        or normalized.startswith(pattern.rstrip("/").rstrip("*"))
        for pattern in patterns
    )
