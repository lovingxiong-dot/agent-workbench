"""tests/v6/conftest.py — V6 测试共享 fixtures。"""
from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """提供唯一的 QApplication 实例。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["test"])
    yield app


@pytest.fixture(scope="session", autouse=True)
def _v6_test_data_dir(tmp_path_factory):
    """通过环境变量隔离所有使用默认数据目录的 V6 测试。"""
    path = tmp_path_factory.mktemp("v6_test_data")
    os.environ["V6_DATA_DIR"] = str(path)
    yield path
    os.environ.pop("V6_DATA_DIR", None)
