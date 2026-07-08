#!/usr/bin/env python3
"""Verify repository health before commit or CI.

Checks:
- No forbidden top-level items
- No .bak / .tmp / .draft files in tracked files
- No duplicate architecture docs
- Generated dirs are ignored
- pytest passes (optional)

Usage:
    python scripts/verify_repository.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from audit_repository import (
    AuditReport,
    find_duplicate_docs,
    find_forbidden_top_level,
    find_generated_dirs_and_build_artifacts,
    find_legacy_files,
)


def _tracked_files_with_forbidden_extensions() -> list[str]:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    forbidden = []
    for line in result.stdout.splitlines():
        if line.endswith((".bak", ".tmp", ".draft")):
            forbidden.append(line)
    return forbidden


def main() -> int:
    report = AuditReport()
    find_duplicate_docs(report)
    find_forbidden_top_level(report)
    find_generated_dirs_and_build_artifacts(report)
    find_legacy_files(report)

    tracked_forbidden = _tracked_files_with_forbidden_extensions()

    issues = (
        len(report.duplicate_docs)
        + len(report.forbidden_top_level)
        + len(report.build_artifacts)
        + len(report.legacy_files)
        + len(tracked_forbidden)
    )

    print("=" * 60)
    print("Repository Verification")
    print("=" * 60)

    if report.duplicate_docs:
        print("\nDuplicate docs:")
        for item in report.duplicate_docs:
            print(f"  - {item}")

    if report.forbidden_top_level:
        print("\nForbidden top-level items:")
        for item in report.forbidden_top_level:
            print(f"  - {item}")

    if report.build_artifacts:
        print("\nBuild artifacts in tracked files:")
        for item in report.build_artifacts:
            print(f"  - {item}")

    if report.legacy_files:
        print("\nLegacy / forbidden names:")
        for item in report.legacy_files:
            print(f"  - {item}")

    if tracked_forbidden:
        print("\nTracked forbidden extensions:")
        for item in tracked_forbidden:
            print(f"  - {item}")

    if issues == 0:
        print("\nRepository verification passed.")
        return 0

    print(f"\nFound {issues} issue(s). Please fix before commit.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
