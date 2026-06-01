from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from .scope import filter_status_by_exclude_scope


@dataclass
class GitClient:
    root: Path

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=check,
        )

    def branch(self) -> str:
        result = self.run("branch", "--show-current", check=False)
        branch = result.stdout.strip()
        if branch:
            return branch
        result = self.run("rev-parse", "--abbrev-ref", "HEAD", check=False)
        return result.stdout.strip() or "HEAD"

    def head(self) -> str | None:
        result = self.run("rev-parse", "HEAD", check=False)
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def short_head(self) -> str | None:
        head = self.head()
        return head[:7] if head else None

    def status_porcelain(
        self,
        include_untracked: bool = True,
        exclude_paths: list[str] | None = None,
        exclude_extensions: set[str] | None = None,
    ) -> list[str]:
        args = ["status", "--porcelain"]
        if not include_untracked:
            args.append("--untracked-files=no")
        result = self.run(*args, check=True)
        entries = [line for line in result.stdout.splitlines() if line.strip()]
        if exclude_paths is not None or exclude_extensions is not None:
            return filter_status_by_exclude_scope(entries, exclude_paths, exclude_extensions)
        return entries

    def is_dirty(
        self,
        include_untracked: bool = True,
        exclude_paths: list[str] | None = None,
        exclude_extensions: set[str] | None = None,
    ) -> bool:
        return bool(
            self.status_porcelain(
                include_untracked=include_untracked,
                exclude_paths=exclude_paths,
                exclude_extensions=exclude_extensions,
            )
        )

    def create_branch(self, branch: str) -> None:
        self.run("switch", "-c", branch)

    def switch_branch(self, branch: str) -> None:
        self.run("switch", branch)

    def branches(self) -> list[str]:
        result = self.run("branch", "--format=%(refname:short)", check=False)
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def tag_exists(self, tag: str) -> bool:
        result = self.run("show-ref", "--tags", "--verify", f"refs/tags/{tag}", check=False)
        return result.returncode == 0

    def create_tag(self, tag: str, ref: str) -> None:
        self.run("tag", tag, ref)

    def tracked_files(self) -> list[str]:
        result = self.run("ls-files", check=True)
        return [line for line in result.stdout.splitlines() if line]

    def blob_oid(self, path: str) -> str | None:
        result = self.run("ls-files", "-s", "--", path, check=False)
        if result.returncode != 0 or not result.stdout.strip():
            return None
        parts = result.stdout.split()
        return parts[1] if len(parts) > 1 else None
