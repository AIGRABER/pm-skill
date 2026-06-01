from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


def find_repo_root(start: Path | None = None) -> Path:
    cwd = (start or Path.cwd()).resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Not inside a git repository: {cwd}") from exc


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @classmethod
    def discover(cls, start: Path | None = None) -> "ProjectPaths":
        return cls(find_repo_root(start))

    @property
    def pm(self) -> Path:
        return self.root / ".pm-skill"

    @property
    def manifest(self) -> Path:
        return self.pm / "project-manifest.json"

    @property
    def schemas(self) -> Path:
        return self.pm / "schemas"

    @property
    def index(self) -> Path:
        return self.pm / "index"

    @property
    def audit(self) -> Path:
        return self.pm / "audit"

    @property
    def audit_log(self) -> Path:
        return self.audit / "audit-log.jsonl"

    @property
    def branches(self) -> Path:
        return self.pm / "branches"

    @property
    def runtime(self) -> Path:
        return self.pm / "runtime"

    @property
    def template_hashes(self) -> Path:
        return self.pm / "template-hashes.json"

    @property
    def docs(self) -> Path:
        return self.root / "docs"

    @property
    def requirements_drafts(self) -> Path:
        return self.docs / "requirements" / "drafts"

    @property
    def requirements_final(self) -> Path:
        return self.docs / "requirements" / "final"

    @property
    def handover(self) -> Path:
        return self.docs / "handover"

    @property
    def changelog(self) -> Path:
        return self.docs / "changelog"

    @property
    def acceptance(self) -> Path:
        return self.docs / "acceptance"

    @property
    def work_packages(self) -> Path:
        return self.docs / "work-packages"

    @property
    def policy(self) -> Path:
        return self.docs / "standards" / "development-policy.yaml"

    @property
    def adr(self) -> Path:
        return self.docs / "adr"

    @property
    def todo(self) -> Path:
        return self.root / "todo"

    @property
    def skill(self) -> Path:
        return self.root / ".codex" / "skills" / "project-dev-management"
