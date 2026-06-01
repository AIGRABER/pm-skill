from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class _FrontmatterDumper(yaml.SafeDumper):
    pass


def _represent_str(dumper: yaml.Dumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_FrontmatterDumper.add_representer(str, _represent_str)


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"Missing closing front matter marker in {path}")
    raw_meta = text[4:end]
    body = text[end + 5 :]
    meta = yaml.safe_load(raw_meta) or {}
    if not isinstance(meta, dict):
        raise ValueError(f"Front matter in {path} must be a mapping")
    return meta, body


def write_frontmatter(path: Path, meta: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    front = yaml.dump(
        meta,
        Dumper=_FrontmatterDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    clean_body = body.lstrip("\n")
    path.write_text(f"---\n{front}\n---\n\n{clean_body}", encoding="utf-8", newline="\n")
