from __future__ import annotations

from pathlib import Path

from .paths import ProjectPaths


def scope_values(value: str | list[str]) -> list[str]:
    return [value] if isinstance(value, str) else list(value)


def normalize_scope_paths(
    paths: ProjectPaths,
    value: str | list[str],
    *,
    field_name: str,
    default_all: bool = True,
) -> list[str] | None:
    values = [item.strip().replace("\\", "/") for item in scope_values(value) if item.strip()]
    if not values:
        return None if default_all else []
    if "*" in values:
        return None
    normalized_paths: list[str] = []
    root = paths.root.resolve()
    for raw in values:
        if Path(raw).is_absolute():
            raise RuntimeError(f"{field_name} must be relative to the project root: {raw}")
        if raw.startswith("../") or raw == ".." or "/../" in raw:
            raise RuntimeError(f"{field_name} cannot point outside the project root: {raw}")
        candidate = (root / raw).resolve()
        try:
            rel = candidate.relative_to(root).as_posix()
        except ValueError as exc:
            raise RuntimeError(f"{field_name} cannot point outside the project root: {raw}") from exc
        normalized_paths.append(rel.rstrip("/"))
    return normalized_paths


def normalize_scope_extensions(value: str | list[str], *, default_all: bool = True) -> set[str] | None:
    values = [item.strip().lower() for item in scope_values(value) if item.strip()]
    if not values:
        return None if default_all else set()
    if "*" in values:
        return None
    return {item if item.startswith(".") else f".{item}" for item in values}


def scope_has_values(value: str | list[str]) -> bool:
    return any(item.strip() for item in scope_values(value))


def matches_scope(rel: str, scope_paths: list[str] | None, extensions: set[str] | None) -> bool:
    normalized = rel.replace("\\", "/").strip("/")
    if scope_paths is not None and not any(
        normalized == base or normalized.startswith(f"{base}/") for base in scope_paths
    ):
        return False
    if extensions is not None and Path(normalized).suffix.lower() not in extensions:
        return False
    return True


def exclude_scope_enabled(paths_value: str | list[str], extensions_value: str | list[str]) -> bool:
    return scope_has_values(paths_value) or scope_has_values(extensions_value)


def normalize_exclude_scope(
    paths: ProjectPaths,
    paths_value: str | list[str],
    extensions_value: str | list[str],
) -> tuple[list[str] | None, set[str] | None]:
    if not exclude_scope_enabled(paths_value, extensions_value):
        return [], set()
    return (
        normalize_scope_paths(paths, paths_value, field_name="exclude_scope.paths", default_all=False),
        normalize_scope_extensions(extensions_value, default_all=False),
    )


def matches_exclude_scope(
    rel: str,
    exclude_paths: list[str] | None,
    exclude_extensions: set[str] | None,
) -> bool:
    normalized = rel.replace("\\", "/").strip("/")
    path_match = exclude_paths is None or any(
        normalized == base or normalized.startswith(f"{base}/") for base in exclude_paths
    )
    ext_match = exclude_extensions is None or Path(normalized).suffix.lower() in exclude_extensions
    return path_match or ext_match


def status_entry_paths(entry: str) -> list[str]:
    payload = entry[3:].strip() if len(entry) > 3 else entry.strip()
    if " -> " in payload:
        return [part.strip().strip('"') for part in payload.split(" -> ") if part.strip()]
    return [payload.strip('"')] if payload else []


def filter_status_by_exclude_scope(
    entries: list[str],
    exclude_paths: list[str] | None,
    exclude_extensions: set[str] | None,
) -> list[str]:
    filtered: list[str] = []
    for entry in entries:
        paths = status_entry_paths(entry)
        if paths and all(matches_exclude_scope(path, exclude_paths, exclude_extensions) for path in paths):
            continue
        filtered.append(entry)
    return filtered
