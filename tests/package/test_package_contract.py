"""Tests for Commit 12.1 — Package Contract Freeze."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from agent_workbench.package import PackageLoader, PackageManifest, PackageValidationError


class TestPackageManifest:
    def test_from_dict_minimal(self) -> None:
        data = {
            "id": "starter_agent",
            "version": "1.0.0",
            "schema_version": "1.0",
        }
        manifest = PackageManifest.from_dict(data, package_dir="/tmp/starter_agent")
        assert manifest.id == "starter_agent"
        assert manifest.version == "1.0.0"
        assert manifest.schema_version == "1.0"
        assert manifest.package_dir == "/tmp/starter_agent"
        assert manifest.metadata == "metadata.json"
        assert manifest.capabilities == "capabilities.json"
        assert manifest.view_schema == "view_schema.json"
        assert manifest.runtime == "runtime.json"

    def test_from_dict_custom_paths(self) -> None:
        data = {
            "id": "custom",
            "version": "2.0.0",
            "schema_version": "1.0",
            "metadata": "meta.json",
            "capabilities": "caps.json",
            "view_schema": "view.json",
            "runtime": "run.json",
        }
        manifest = PackageManifest.from_dict(data, package_dir="/tmp/custom")
        assert manifest.metadata == "meta.json"
        assert manifest.capabilities == "caps.json"
        assert manifest.view_schema == "view.json"
        assert manifest.runtime == "run.json"

    def test_missing_id_raises(self) -> None:
        data = {"version": "1.0.0", "schema_version": "1.0"}
        with pytest.raises(PackageValidationError) as exc_info:
            PackageManifest.from_dict(data, package_dir="/tmp/x")
        assert "id" in str(exc_info.value)

    def test_missing_version_raises(self) -> None:
        data = {"id": "x", "schema_version": "1.0"}
        with pytest.raises(PackageValidationError) as exc_info:
            PackageManifest.from_dict(data, package_dir="/tmp/x")
        assert "version" in str(exc_info.value)

    def test_missing_schema_version_raises(self) -> None:
        data = {"id": "x", "version": "1.0.0"}
        with pytest.raises(PackageValidationError) as exc_info:
            PackageManifest.from_dict(data, package_dir="/tmp/x")
        assert "schema_version" in str(exc_info.value)

    def test_unsupported_schema_version_raises(self) -> None:
        data = {"id": "x", "version": "1.0.0", "schema_version": "2.0"}
        with pytest.raises(PackageValidationError) as exc_info:
            PackageManifest.from_dict(data, package_dir="/tmp/x")
        assert "unsupported schema_version" in str(exc_info.value)

    def test_from_file_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "id": "file_agent",
                        "version": "1.2.3",
                        "schema_version": "1.0",
                    },
                    f,
                )
            manifest = PackageManifest.from_file(tmpdir)
            assert manifest.id == "file_agent"
            assert manifest.version == "1.2.3"
            assert manifest.schema_version == "1.0"

    def test_from_file_invalid_json_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write("not json")
            with pytest.raises(PackageValidationError):
                PackageManifest.from_file(tmpdir)

    def test_from_file_missing_manifest_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(PackageValidationError):
                PackageManifest.from_file(tmpdir)


class TestPackageLoader:
    def test_scan_finds_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            package_dir = os.path.join(packages_dir, "abc")
            os.makedirs(package_dir)
            with open(os.path.join(package_dir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "id": "abc",
                        "version": "1.0.0",
                        "schema_version": "1.0",
                    },
                    f,
                )

            loader = PackageLoader(packages_dir)
            manifests = loader.scan()
            assert len(manifests) == 1
            assert manifests[0].id == "abc"

    def test_scan_ignores_directory_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            os.makedirs(os.path.join(packages_dir, "empty_dir"))
            loader = PackageLoader(packages_dir)
            assert loader.scan() == []

    def test_scan_ignores_files(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            with open(os.path.join(packages_dir, "not_a_package.txt"), "w", encoding="utf-8") as f:
                f.write("hello")
            loader = PackageLoader(packages_dir)
            assert loader.scan() == []

    def test_scan_skips_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as packages_dir:
            valid_dir = os.path.join(packages_dir, "valid")
            invalid_dir = os.path.join(packages_dir, "invalid")
            os.makedirs(valid_dir)
            os.makedirs(invalid_dir)

            with open(os.path.join(valid_dir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump({"id": "valid", "version": "1.0.0", "schema_version": "1.0"}, f)

            with open(os.path.join(invalid_dir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump({"id": "invalid", "version": "1.0.0"}, f)

            loader = PackageLoader(packages_dir)
            manifests = loader.scan()
            assert len(manifests) == 1
            assert manifests[0].id == "valid"

    def test_scan_returns_empty_when_dir_missing(self) -> None:
        loader = PackageLoader("/nonexistent/path")
        assert loader.scan() == []
