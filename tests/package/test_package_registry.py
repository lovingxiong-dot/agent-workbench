"""Tests for Commit 12.2 — Package Registry lifecycle."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from agent_workbench.package import PackageManifest, PackageRegistry, PackageValidationError


class TestPackageRegistry:
    def _create_package(self, packages_dir: str, package_id: str, *, metadata: dict | None = None) -> str:
        package_dir = os.path.join(packages_dir, package_id)
        os.makedirs(package_dir, exist_ok=True)
        with open(os.path.join(package_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "id": package_id,
                    "version": "1.0.0",
                    "schema_version": "1.0",
                },
                f,
            )
        if metadata is not None:
            with open(os.path.join(package_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f)
        return package_dir

    def test_discover_returns_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            self._create_package(packages_dir, "agent_a")
            self._create_package(packages_dir, "agent_b")

            registry = PackageRegistry(packages_dir)
            manifests = registry.discover()
            assert len(manifests) == 2
            assert {m.id for m in manifests} == {"agent_a", "agent_b"}

    def test_discover_without_dir_raises(self) -> None:
        registry = PackageRegistry()
        with pytest.raises(PackageValidationError):
            registry.discover()

    def test_load_registers_package(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            self._create_package(packages_dir, "agent_a", metadata={"name": "Agent A"})
            registry = PackageRegistry(packages_dir)
            manifests = registry.discover()
            info = registry.load(manifests[0])

            assert info.manifest.id == "agent_a"
            assert info.metadata == {"name": "Agent A"}
            assert info.loaded_at is not None

    def test_list_returns_loaded_packages(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            self._create_package(packages_dir, "agent_a")
            self._create_package(packages_dir, "agent_b")

            registry = PackageRegistry(packages_dir)
            for manifest in registry.discover():
                registry.load(manifest)

            packages = registry.list()
            assert len(packages) == 2
            assert {p.manifest.id for p in packages} == {"agent_a", "agent_b"}

    def test_unload_removes_package(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            self._create_package(packages_dir, "agent_a")
            registry = PackageRegistry(packages_dir)
            manifest = registry.discover()[0]
            registry.load(manifest)
            assert len(registry.list()) == 1

            registry.unload("agent_a")
            assert registry.list() == []
            assert registry.get("agent_a") is None

    def test_get_returns_loaded_package(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            self._create_package(packages_dir, "agent_a")
            registry = PackageRegistry(packages_dir)
            manifest = registry.discover()[0]
            registry.load(manifest)
            assert registry.get("agent_a") is not None
            assert registry.get("missing") is None

    def test_load_missing_json_files_is_graceful(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            self._create_package(packages_dir, "minimal")
            registry = PackageRegistry(packages_dir)
            manifest = registry.discover()[0]
            info = registry.load(manifest)
            assert info.capabilities == {}
            assert info.view_schema == {}
            assert info.runtime == {}

    def test_reload_is_not_implemented(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            self._create_package(packages_dir, "agent_a")
            registry = PackageRegistry(packages_dir)
            manifest = registry.discover()[0]
            registry.load(manifest)
            with pytest.raises(NotImplementedError):
                registry.reload("agent_a")
