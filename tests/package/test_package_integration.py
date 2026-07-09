"""Tests for Commit 12.3 — Package Workbench Integration."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.package import (
    PackageInfo,
    PackageIntegration,
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


def _make_starter_agent_package(packages_dir: str, package_id: str = "starter_agent") -> str:
    """在 packages_dir 下创建一个最小但完整的 Agent Package。"""
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
        "description": "A sample agent for integration tests.",
        "icon": "🚀",
        "properties": [
            {
                "id": "version",
                "name": "Version",
                "description": "Package version.",
                "value_type": "string",
                "current_value": "1.0.0",
                "editable": False,
            }
        ],
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
        "tags": ["sample", "builtin"],
    }
    view_schema = {
        "schema_id": f"{package_id}_workspace",
        "name": "Starter Agent Workspace",
        "workspace": {
            "toolbar": {"items": ["execute"]},
            "inspector": {
                "tabs": [
                    {"id": "properties", "title": "Properties", "source": "properties"},
                    {"id": "statistics", "title": "Statistics", "source": "statistics"},
                    {"id": "actions", "title": "Actions", "source": "actions"},
                ],
                "default_tab": "actions",
            },
            "status": {
                "items": [
                    {"name": "runtime", "source": "binding", "binding": {"path": "runtime.status"}},
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


def _make_fake_host():
    """返回一个 MagicMock host，使 WorkbenchUIController 可在无真实 Qt 骨架时测试渲染路径。"""
    host = MagicMock()
    host.workbench.tool_bar.set_actions = MagicMock()
    host.workbench.status_bar.set_statistics = MagicMock()
    host.workbench.inspector.set_schema = MagicMock()
    host.workbench.inspector.set_object = MagicMock()
    host.workbench.workspace.register_workspace = MagicMock()
    host.workbench.workspace.switch_to = MagicMock()
    host.workbench.navigator.load_presentations = MagicMock()
    host.set_status = MagicMock()
    return host


class TestPackageIntegration:
    def test_to_module_presentation_preserves_view_schema_id(self) -> None:
        manifest = PackageManifest(
            id="starter_agent",
            version="1.0.0",
            schema_version="1.0",
            package_dir="/tmp/starter_agent",
        )
        package = PackageInfo(
            manifest=manifest,
            metadata={"name": "Starter Agent", "type": "agent"},
            view_schema={"schema_id": "starter_agent_workspace"},
        )
        integration = PackageIntegration()
        presentation = integration.to_module_presentation(package)

        assert presentation.id == "starter_agent"
        assert presentation.view_schema_id == "starter_agent_workspace"

    def test_to_module_presentation_uses_default_view_schema_when_missing(self) -> None:
        manifest = PackageManifest(
            id="custom_agent",
            version="1.0.0",
            schema_version="1.0",
            package_dir="/tmp/custom_agent",
        )
        package = PackageInfo(
            manifest=manifest,
            metadata={"name": "Custom Agent", "type": "agent"},
            view_schema={},
        )
        integration = PackageIntegration()
        presentation = integration.to_module_presentation(package)

        assert presentation.id == "custom_agent"
        assert presentation.view_schema_id == "generic_workspace"

    def test_to_view_schema_parses_package_workspace(self) -> None:
        manifest = PackageManifest(
            id="starter_agent",
            version="1.0.0",
            schema_version="1.0",
            package_dir="/tmp/starter_agent",
        )
        package = PackageInfo(
            manifest=manifest,
            view_schema={
                "schema_id": "starter_agent_workspace",
                "workspace": {
                    "toolbar": {"items": ["execute"]},
                    "inspector": {"tabs": [], "default_tab": "properties"},
                    "status": {"items": []},
                },
            },
        )
        integration = PackageIntegration()
        schema = integration.to_view_schema(package)

        assert schema is not None
        assert schema.schema_id == "starter_agent_workspace"
        assert schema.workspace.toolbar.items == ["execute"]

    def test_to_view_schema_returns_none_for_empty_dict(self) -> None:
        manifest = PackageManifest(
            id="minimal",
            version="1.0.0",
            schema_version="1.0",
            package_dir="/tmp/minimal",
        )
        package = PackageInfo(manifest=manifest, view_schema={})
        integration = PackageIntegration()

        assert integration.to_view_schema(package) is None


class TestWorkbenchUIControllerPackageIntegration:
    def test_default_packages_dir_resolution(self, qt_app) -> None:
        controller = WorkbenchUIController(config_path=None)
        expected_suffix = os.path.join("agent_workbench", "packages")
        assert expected_suffix.replace("\\", "/") in controller._packages_dir.replace("\\", "/")

    def test_build_navigator_presentations_includes_agent_packages(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            _make_starter_agent_package(packages_dir)
            controller = WorkbenchUIController(packages_dir=packages_dir)
            controller._load_packages()

            presentations = controller._build_navigator_presentations()
            ids = [p.id for p in presentations]

            assert "starter_agent" in ids
            agent_pres = next(p for p in presentations if p.id == "starter_agent")
            assert agent_pres.category == "agent"
            assert agent_pres.view_schema_id == "starter_agent_workspace"

    def test_navigator_presentations_excludes_unloaded_packages(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            _make_starter_agent_package(packages_dir)
            controller = WorkbenchUIController(packages_dir=packages_dir)
            # 不调用 _load_packages()

            presentations = controller._build_navigator_presentations()
            assert "starter_agent" not in [p.id for p in presentations]

    def test_load_packages_registers_view_schema(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            _make_starter_agent_package(packages_dir)
            controller = WorkbenchUIController(packages_dir=packages_dir)
            controller._load_packages()

            schema = controller._view_schema_registry.get("starter_agent_workspace")
            assert schema is not None
            assert schema.name == "Starter Agent Workspace"

    def test_selection_change_renders_package_view_schema(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            _make_starter_agent_package(packages_dir)
            host = _make_fake_host()
            controller = WorkbenchUIController(packages_dir=packages_dir, workbench_host=host)
            controller._setup_workbench_ui()
            controller._load_packages()
            controller._on_selection_changed("starter_agent")

            assert controller._current_module_id == "starter_agent"
            host.workbench.inspector.set_schema.assert_called()
            host.workbench.inspector.set_object.assert_called()
            host.workbench.workspace.switch_to.assert_called_with("generic")

    def test_selection_change_falls_back_to_package_registry(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            _make_starter_agent_package(packages_dir)
            controller = WorkbenchUIController(packages_dir=packages_dir)
            controller._load_packages()
            controller._presentations.clear()

            host = _make_fake_host()
            controller._host = host
            controller._view_schema_renderer = MagicMock()
            controller._generic_workspace = MagicMock()

            controller._on_selection_changed("starter_agent")
            assert "starter_agent" in controller._presentations

    def test_load_packages_unloads_removed_packages(self, qt_app) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            _make_starter_agent_package(packages_dir)
            controller = WorkbenchUIController(packages_dir=packages_dir)
            controller._load_packages()
            assert controller._package_registry.get("starter_agent") is not None

            import shutil

            shutil.rmtree(os.path.join(packages_dir, "starter_agent"))
            controller._load_packages()

            assert controller._package_registry.get("starter_agent") is None
            assert "starter_agent" not in [
                p.id for p in controller._build_navigator_presentations()
            ]
