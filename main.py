#!/usr/bin/env python3
"""
AI Agent Workbench · V5 新 UI 主入口
"""
import sys
import os
import traceback

# 确保项目根在 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _diagnostic_hook(exc_type, exc_value, exc_tb):
    """全局异常钩子：把未捕获异常打印到 stderr 并刷新"""
    print("=" * 60, file=sys.stderr)
    print("UNCAUGHT PYTHON EXCEPTION", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_tb)
    print("=" * 60, file=sys.stderr)
    sys.stderr.flush()


sys.excepthook = _diagnostic_hook

from v5.main import main


if __name__ == "__main__":
    main()
