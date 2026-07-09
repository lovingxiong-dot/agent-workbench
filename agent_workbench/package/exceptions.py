"""agent_workbench/package/exceptions.py — Package 层异常。"""
from __future__ import annotations


class PackageError(Exception):
    """Package 层基础异常。"""


class PackageValidationError(PackageError):
    """manifest 校验失败。"""
