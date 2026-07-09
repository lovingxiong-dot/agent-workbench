"""Tests for Commit 12.4 — Starter Agent Runtime (Execute Action)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.controller import WorkbenchController
from agent_workbench.package import (
    PackageExecutor,
    PackageInfo,
    PackageManifest,
    PackageRegistry,
)
from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def _make_starter_package(package_id: str = "starter_agent") -> PackageInfo:
    manifest = PackageManifest(
        id=package_id,
        version="1.0.0",
        schema_version="1.0",
        package_dir=f"/tmp/{package_id}",
    )
    return PackageInfo(
        manifest=manifest,
        metadata={
            "id": package_id,
            "name": "Starter Agent",
            "type": "agent",
            "statistics": [
                {
                    "id": "execution_count",
                    "name": "Executions",
                    "value": 0,
                    "unit": "times",
                }
            ],
        },
    )


def _make_starter_agent_package_dir(packages_dir: str, package_id: str = "starter_agent") -> str:
    package_dir = os.path.join(packages_dir, package_id)
    os.makedirs(package_dir, exist_ok=True)

    manifest = {
        "id": package_id,
        "version": "1.0.0",
        "schema_version": "1.0",
    }
    metadata = {
        "id": package_id,
        "type": "agent",
        "name": "Starter Agent",
        "description": "A sample agent.",
        "icon": "🚀",
        "properties": [],
        "statistics": [
            {
                "id": "execution_count",
                "name": "Executions",
                "value": 0,
                "unit": "times",
            }
        ],
        "actions": [
            {
                "id": "execute",
                "label": "Execute",
                "description": "Run the agent.",
                "icon": "▶️",
                "enabled": True,
            }
        ],
        "tags": ["sample"],
    }
    view_schema = {
        "schema_id": f"{package_id}_workspace",
        "name": "Starter Agent Workspace",
        "workspace": {
            "toolbar": {"items": ["execute"]},
            "inspector": {
                "tabs": [
                    {"id": "actions", "title": "Actions", "source": "actions"},
                    {"id": "statistics", "title": "Statistics", "source": "statistics"},
                ],
                "default_tab": "actions",
            },
            "status": {
                "items": [
                    {"name": "execution_count", "source": "statistics"},
                ]
            },
        },
    }

    for filename, data in [
        ("manifest.json", manifest),
        ("metadata.json", metadata),
        ("view_schema.json", view_schema),
    ]:
        with open(os.path.join(package_dir, filename), "w", encoding="utf-8") as f:
            json.dump(data, f)

    return package_dir


class TestPackageExecutor:
    def test_execute_increments_execution_count(self) -> None:
        package = _make_starter_package()
        executor = PackageExecutor()

        result = executor.execute(package, "execute")

        assert result["status"] == "completed"
        assert result["package_id"] == "starter_agent"
        assert result["action_id"] == "execute"
        assert result["execution_count"] == 1

        stats = package.metadata["statistics"]
        execution_count = next(s for s in stats if s["id"] == "execution_count")
        assert execution_count["value"] == 1

    def test_execute_multiple_times_accumulates(self) -> None:
        package = _make_starter_package()
        executor = PackageExecutor()

        for expected in range(1, 4):
            result = executor.execute(package, "execute")
            assert result["execution_count"] == expected

    def test_execute_creates_execution_count_if_missing(self) -> None:
        package = _make_starter_package()
        package.metadata["statistics"] = []
        executor = PackageExecutor()

        result = executor.execute(package, "execute")

        assert result["execution_count"] == 1
        assert any(s["id"] == "execution_count" for s in package.metadata["statistics"])

    def test_execute_missing_package_returns_error(self) -> None:
        executor = PackageExecutor()
        result = executor.execute(None, "execute")
        assert result["status"] == "failed"

    def test_execute_missing_action_id_returns_error(self) -> None:
        package = _make_starter_package()
        executor = PackageExecutor()
        result = executor.execute(package, "")
        assert result["status"] == "failed"

    def test_execute_uses_real_starter_agent_script(self) -> None:
        here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        package_dir = os.path.join(here, "packages", "starter_agent")
        manifest = PackageManifest.from_file(package_dir)
        registry = PackageRegistry(os.path.join(here, "packages"))
        package = registry.load(manifest)

        executor = PackageExecutor()
        result = executor.execute(package, "execute")

        assert result["status"] == "completed"
        assert result["message"] == "Task executed successfully."
        assert result["execution_count"] == 1

        stats = package.metadata["statistics"]
        execution_count = next(s for s in stats if s["id"] == "execution_count")
        assert execution_count["value"] == 1


class TestWorkbenchControllerAgentAction:
    def test_execute_agent_action_updates_package_statistics(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            _make_starter_agent_package_dir(packages_dir)
            registry = PackageRegistry(packages_dir)
            manifests = registry.discover()
            assert manifests
            registry.load(manifests[0])

            controller = WorkbenchController(
                config_path=None,
                package_registry=registry,
            )
            result = controller.execute_agent_action("starter_agent", "execute")

            assert result["status"] == "completed"
            assert result["execution_count"] == 1

            package = registry.get("starter_agent")
            stats = package.metadata["statistics"]
            execution_count = next(s for s in stats if s["id"] == "execution_count")
            assert execution_count["value"] == 1

    def test_execute_agent_action_without_registry_returns_error(self, qt_app) -> None:
        controller = WorkbenchController(config_path=None)
        result = controller.execute_agent_action("starter_agent", "execute")
        assert result["status"] == "failed"
        assert "package registry not configured" in result["error"]

    def test_execute_agent_action_unknown_package_returns_error(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            registry = PackageRegistry(packages_dir)
            controller = WorkbenchController(
                config_path=None,
                package_registry=registry,
            )
            result = controller.execute_agent_action("missing", "execute")
            assert result["status"] == "failed"
            assert "package not found" in result["error"]


class TestWorkbenchUIControllerAgentAction:
    def test_on_action_triggered_executes_package_action(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            _make_starter_agent_package_dir(packages_dir)
            controller = WorkbenchUIController(packages_dir=packages_dir)
            controller._load_packages()

            # 模拟选中 starter_agent
            controller._current_module_id = "starter_agent"
            controller._on_action_triggered("starter_agent", "execute")

            package = controller._package_registry.get("starter_agent")
            stats = package.metadata["statistics"]
            execution_count = next(s for s in stats if s["id"] == "execution_count")
            assert execution_count["value"] == 1

    def test_on_action_triggered_refreshes_presentation_cache(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            _make_starter_agent_package_dir(packages_dir)
            controller = WorkbenchUIController(packages_dir=packages_dir)
            controller._load_packages()
            old_presentation = MagicMock()
            controller._presentations["starter_agent"] = old_presentation

            controller._current_module_id = "starter_agent"
            controller._on_action_triggered("starter_agent", "execute")

            # action 执行后会重新构建 presentation，旧的 MagicMock 被替换，且 statistics 已刷新。
            assert controller._presentations["starter_agent"] is not old_presentation
            stat = next(
                s for s in controller._presentations["starter_agent"].statistics if s.name == "execution_count"
            )
            assert stat.value == 1
