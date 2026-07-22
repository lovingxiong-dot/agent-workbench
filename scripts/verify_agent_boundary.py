#!/usr/bin/env python3
"""Agent Boundary Verification Script.

Checks whether modified files violate frozen architecture boundaries.
Reads .agent-entry.json to determine frozen/requires_review/allowed zones.

Usage:
    python scripts/verify_agent_boundary.py              # check all git diff
    python scripts/verify_agent_boundary.py <file>       # check specific file
    python scripts/verify_agent_boundary.py --staged     # check staged changes
    python scripts/verify_agent_boundary.py --list       # list all frozen zones
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

# Frozen zone → file path mapping
FROZEN_ZONE_PATHS: dict[str, list[str]] = {
    "RuntimeContext": ["v6/runtime/context.py"],
    "Task Contract": ["v6/runtime/task.py"],
    "Capability Contract": [
        "agent_workbench/runtime/capability/model.py",
        "agent_workbench/runtime/capability/context.py",
        "agent_workbench/runtime/capability/state.py",
    ],
    "CapabilityDefinition": ["agent_workbench/runtime/capability/model.py"],
    "CapabilityContext": ["agent_workbench/runtime/capability/context.py"],
    "CapabilityState": ["agent_workbench/runtime/capability/state.py"],
    "Decision Layer (RuntimeDecision ABI)": [
        "agent_workbench/runtime/decision/schema.py",
        "agent_workbench/runtime/decision/policy.py",
        "agent_workbench/runtime/decision/resolver.py",
    ],
    "Interaction Boundary (RuntimeRequest / InteractionEvent)": [
        "agent_workbench/runtime/interaction/request.py",
        "agent_workbench/runtime/interaction/event.py",
        "agent_workbench/runtime/interaction/layer.py",
        "agent_workbench/runtime/interaction/mapper.py",
    ],
    "Orchestrator": ["v6/runtime/orchestrator.py"],
    "CapabilityRegistry": [
        "v6/runtime/capability_registry.py",
        "agent_workbench/runtime/capability_router.py",
    ],
    "EventBus": ["v6/runtime/event_bus.py"],
    "Metadata Contract (MetadataDefinition, ValueType, MetadataType)": [
        "agent_workbench/metadata/model.py",
        "agent_workbench/metadata/types.py",
    ],
}

REQUIRES_REVIEW_PATHS: list[str] = [
    "v6/runtime/engines/",
    "v6/runtime/manager.py",
    "v6/runtime/planner_loop.py",
    "v6/services/",
]


def load_entry() -> dict:
    """Load .agent-entry.json."""
    entry_path = ROOT / ".agent-entry.json"
    if not entry_path.exists():
        print("ERROR: .agent-entry.json not found. Run AISE Runtime Alignment first.")
        sys.exit(1)
    with open(entry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_changed_files(staged: bool = False) -> list[str]:
    """Get list of changed files from git."""
    try:
        if staged:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, cwd=str(ROOT),
            )
        else:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True, text=True, cwd=str(ROOT),
            )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception:
        return []


def check_file(filepath: str) -> tuple[str | None, str | None]:
    """Check a single file against frozen and review zones.
    
    Returns (frozen_zone_name, review_zone) or (None, None) if allowed.
    """
    # Normalize path
    fp = filepath.replace("\\", "/")

    # Check frozen zones
    for zone_name, paths in FROZEN_ZONE_PATHS.items():
        for p in paths:
            if fp.endswith(p.replace("\\", "/")) or fp == p.replace("\\", "/"):
                return (zone_name, None)

    # Check requires_review zones
    for p in REQUIRES_REVIEW_PATHS:
        if fp.startswith(p.replace("\\", "/")):
            return (None, p)

    return (None, None)


def list_frozen_zones() -> None:
    """Print all frozen zones and their paths."""
    print("=" * 60)
    print("FROZEN ZONES (v6.9.6-foundation)")
    print("=" * 60)
    for zone, paths in FROZEN_ZONE_PATHS.items():
        print(f"\n  {zone}:")
        for p in paths:
            exists = (ROOT / p).exists()
            status = "✓" if exists else "✗ (missing)"
            print(f"    {status}  {p}")

    print("\n" + "=" * 60)
    print("REQUIRES REVIEW")
    print("=" * 60)
    for p in REQUIRES_REVIEW_PATHS:
        exists = (ROOT / p).exists()
        status = "✓" if exists else "✗ (missing)"
        print(f"    {status}  {p}")


def main() -> int:
    args = sys.argv[1:]

    if "--list" in args:
        list_frozen_zones()
        return 0

    staged = "--staged" in args
    files = [a for a in args if not a.startswith("--")]

    if not files:
        files = get_changed_files(staged=staged)

    if not files:
        print("No files to check.")
        return 0

    violations = 0
    reviews = 0

    for fp in files:
        frozen_zone, review_zone = check_file(fp)
        if frozen_zone:
            print(f"❌ FROZEN ZONE VIOLATION: {fp}")
            print(f"   Zone: {frozen_zone}")
            print(f"   Action: Architecture review REQUIRED before modifying this file.")
            print()
            violations += 1
        elif review_zone:
            print(f"⚠️  REQUIRES REVIEW: {fp}")
            print(f"   Zone: {review_zone}")
            print(f"   Action: Proceed with caution. Document your reasoning.")
            print()
            reviews += 1

    if violations > 0:
        print(f"\n{violations} frozen zone violation(s) detected.")
        print("These files are protected by v6.9.6-foundation freeze.")
        print("Do NOT modify without explicit architecture review.")
        return 1
    elif reviews > 0:
        print(f"\n{reviews} file(s) in review-required zones.")
        print("Proceed with caution.")
        return 0
    else:
        print("All changes are in allowed zones. Safe to proceed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())