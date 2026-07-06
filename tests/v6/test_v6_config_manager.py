"""tests/v6/test_v6_config_manager.py — ConfigManager 单元测试。"""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(["test"])
    yield app


def test_default_values(tmp_path, qapp):
    from v6.config_manager import ConfigManager

    cm = ConfigManager(data_dir=tmp_path)
    assert cm.get("app.version") == "v6.3.0-alpha"
    assert cm.get("app.last_mode") == "Agent"
    assert cm.get("app.last_model") == "gpt-4o"
    assert cm.get("theme.name") == "dark"
    assert cm.get("window.geometry") is None
    assert cm.get("missing.path", "fallback") == "fallback"


def test_creates_config_file(tmp_path, qapp):
    from v6.config_manager import ConfigManager

    cm = ConfigManager(data_dir=tmp_path)
    config_file = tmp_path / "config.yaml"
    assert config_file.exists()
    content = config_file.read_text(encoding="utf-8")
    assert "app:" in content
    assert "theme:" in content


def test_set_and_persist(tmp_path, qapp):
    from v6.config_manager import ConfigManager

    cm = ConfigManager(data_dir=tmp_path)
    changed = []
    cm.changed.connect(lambda path, value: changed.append((path, value)))

    cm.set("theme.name", "light")
    assert cm.get("theme.name") == "light"
    assert ("theme.name", "light") in changed

    # 重新实例化应读取已持久化的值
    cm2 = ConfigManager(data_dir=tmp_path)
    assert cm2.get("theme.name") == "light"


def test_nested_path_set(tmp_path, qapp):
    from v6.config_manager import ConfigManager

    cm = ConfigManager(data_dir=tmp_path)
    cm.set("window.geometry.x", 10)
    cm.set("window.geometry.y", 20)
    assert cm.get("window.geometry") == {"x": 10, "y": 20}

    cm.set("window.geometry", {"width": 1280})
    assert cm.get("window.geometry.width") == 1280
    assert cm.get("window.geometry.x") is None


def test_load_merges_with_defaults(tmp_path, qapp):
    from v6.config_manager import ConfigManager

    cm = ConfigManager(data_dir=tmp_path)
    cm.set("theme.name", "light")

    cm2 = ConfigManager(data_dir=tmp_path)
    assert cm2.get("theme.name") == "light"
    assert cm2.get("app.version") == "v6.3.0-alpha"


def test_isolated_instances(tmp_path, qapp):
    from v6.config_manager import ConfigManager

    cm_a = ConfigManager(data_dir=tmp_path / "a")
    cm_b = ConfigManager(data_dir=tmp_path / "b")
    cm_a.set("theme.name", "light")
    cm_b.set("theme.name", "dark")
    assert cm_a.get("theme.name") == "light"
    assert cm_b.get("theme.name") == "dark"
