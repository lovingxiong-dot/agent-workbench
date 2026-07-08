#!/usr/bin/env python3
"""Repository audit script.

Scans the workspace for:
- duplicate architecture documents
- legacy / deprecated / old / backup / copy / tmp / draft names
- generated / ignored directories that still occupy workspace
- build artifacts
- forbidden top-level items

Usage:
    python scripts/audit_repository.py
"""
from __future__ import annotations

import fnmatch
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_FILE_PATTERNS = [
    "*.bak",
    "*.tmp",
    "*.draft",
    "*copy*",
    "*copy2*",
    "*backup*",
    "*old*",
    "*legacy*",
    "*deprecated*",
]

FORBIDDEN_DIR_NAMES = {
    "v4",
    "v5",
    "old",
    "backup",
    "copy",
    "tmp",
    "draft",
    "legacy",
    "deprecated",
}

GENERATED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
    "coverage",
}

ALWAYS_SKIP_DIRS = {
    "venv",
    ".git",
    ".trae",
    ".reference",
    ".memory",
    ".scripts",
    ".workbuddy",
    ".handoff",
    "review",
}

OFFICIAL_DOC_AUTHORITIES = {
    "README.md": "README.md",
    "PROJECT_BLUEPRINT.md": "PROJECT_BLUEPRINT.md",
    "CHANGELOG.md": "CHANGELOG.md",
    "PROJECT_LINEAGE.md": "PROJECT_LINEAGE.md",
}

OFFICIAL_DOC_PATHS = {
    "runtime-kernel-spec.md": "docs/v6/runtime-kernel-spec.md",
    "runtime-glossary.md": "docs/v6/runtime-glossary.md",
    "repository-governance.md": "docs/v6/repository-governance.md",
    "repository-map.md": "docs/v6/repository-map.md",
    "SPEC.md": "docs/v6/SPEC.md",
    "ROADMAP.md": "docs/v6/ROADMAP.md",
}


@dataclass
class AuditReport:
    duplicate_docs: list[str] = field(default_factory=list)
    legacy_files: list[str] = field(default_factory=list)
    generated_dirs: list[str] = field(default_factory=list)
    build_artifacts: list[str] = field(default_factory=list)
    forbidden_top_level: list[str] = field(default_factory=list)

    def score(self) -> int:
        total = (
            len(self.duplicate_docs)
            + len(self.legacy_files)
            + len(self.generated_dirs)
            + len(self.build_artifacts)
            + len(self.forbidden_top_level)
        )
        return max(0, 100 - total * 5)


def _is_ignored(path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "check-ignore", str(path)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _should_skip_dir(path: Path) -> bool:
    parts = set(path.relative_to(ROOT).parts)
    if parts & ALWAYS_SKIP_DIRS:
        return True
    if parts & GENERATED_DIRS:
        return True
    if _is_ignored(path):
        return True
    return False


def find_duplicate_docs(report: AuditReport) -> None:
    for candidate in ROOT.rglob("*.md"):
        if _should_skip_dir(candidate.parent):
            continue
        name = candidate.name
        if name in OFFICIAL_DOC_AUTHORITIES:
            official = ROOT / OFFICIAL_DOC_AUTHORITIES[name]
            if candidate.resolve() != official.resolve():
                report.duplicate_docs.append(str(candidate.relative_to(ROOT)))
        elif name in OFFICIAL_DOC_PATHS:
            official = ROOT / OFFICIAL_DOC_PATHS[name]
            if candidate.resolve() != official.resolve():
                report.duplicate_docs.append(str(candidate.relative_to(ROOT)))


def find_legacy_files(report: AuditReport) -> None:
    for dirpath, dirnames, filenames in os.walk(ROOT):
        current = Path(dirpath)
        if _should_skip_dir(current):
            # prevent recursion into skipped dirs
            dirnames[:] = []
            continue

        rel_dir = current.relative_to(ROOT)

        for dirname in list(dirnames):
            if dirname.lower() in FORBIDDEN_DIR_NAMES:
                report.legacy_files.append(str(rel_dir / dirname))
                dirnames.remove(dirname)

        for filename in filenames:
            lower = filename.lower()
            if any(fnmatch.fnmatch(lower, pat) for pat in FORBIDDEN_FILE_PATTERNS):
                report.legacy_files.append(str(rel_dir / filename))


def find_generated_dirs_and_build_artifacts(report: AuditReport) -> None:
    for name in GENERATED_DIRS:
        for path in ROOT.rglob(name):
            if path.is_dir() and path.relative_to(ROOT).parts[0] not in ALWAYS_SKIP_DIRS:
                report.generated_dirs.append(str(path.relative_to(ROOT)))

    for ext in (".exe", ".msi", ".zip", ".tar.gz", ".pkg"):
        for path in ROOT.rglob(f"*{ext}"):
            if path.is_file() and not _is_ignored(path):
                report.build_artifacts.append(str(path.relative_to(ROOT)))


def find_forbidden_top_level(report: AuditReport) -> None:
    allowed_top_level = {
        ".git",
        ".gitignore",
        "CHANGELOG.md",
        "PROJECT_BLUEPRINT.md",
        "PROJECT_LINEAGE.md",
        "README.md",
        "agent_engine",
        "agent_workbench",
        "agent_workbench.spec",
        "assets",
        "config",
        "core",
        "docs",
        "main.py",
        "pytest.ini",
        "requirements.txt",
        "scripts",
        "services",
        "storage",
        "tests",
        "tools",
        "v5",  # Active V5 runtime library used by V6 adapter tests
        "v6",
        "workers",
    }
    for path in ROOT.iterdir():
        if path.name in allowed_top_level:
            continue
        if _is_ignored(path):
            continue
        report.forbidden_top_level.append(path.name)


def main() -> int:
    report = AuditReport()
    find_duplicate_docs(report)
    find_legacy_files(report)
    find_generated_dirs_and_build_artifacts(report)
    find_forbidden_top_level(report)

    print("=" * 60)
    print("Repository Audit Report")
    print("=" * 60)
    print(f"Repository Score: {report.score()}/100")
    print()

    print(f"Duplicate Docs ({len(report.duplicate_docs)}):")
    for item in report.duplicate_docs:
        print(f"  - {item}")
    print()

    print(f"Legacy / Forbidden Names ({len(report.legacy_files)}):")
    for item in report.legacy_files:
        print(f"  - {item}")
    print()

    print(f"Generated Dirs ({len(report.generated_dirs)}):")
    for item in report.generated_dirs:
        print(f"  - {item}")
    print()

    print(f"Build Artifacts ({len(report.build_artifacts)}):")
    for item in report.build_artifacts:
        print(f"  - {item}")
    print()

    print(f"Forbidden Top-Level Items ({len(report.forbidden_top_level)}):")
    for item in report.forbidden_top_level:
        print(f"  - {item}")
    print()

    return 0 if report.score() >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())
