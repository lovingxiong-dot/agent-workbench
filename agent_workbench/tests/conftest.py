"""agent_workbench/tests/conftest.py — Workbench 测试共享 fixtures。"""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """提供唯一的 QApplication 实例。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["test"])
    yield app
