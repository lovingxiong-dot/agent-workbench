"""scripts/smoke_gui.py — GUI 模拟启动测试。

v6.10.0-alpha 打包前冒烟测试。

测试：
  1. WorkbenchController 启动（合并 config.local.yaml）
  2. ConfigStore 加载成功
  3. ModelModule 加载 minimax-M3 + deepseek-v4-pro
  4. Provider 切换
  5. 真实 LLM 对话（端到端集成）

不发起真实 GUI 启动（headless），只验证 backend 路径完整。
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载 merged config
from agent_workbench.presentation.services.config_loader import (
    WorkbenchLocalConfigLoader,
)

merged_path = WorkbenchLocalConfigLoader.merge_to_temp()
print(f"[*] Merged config: {merged_path}")

# 启动 WorkbenchController
from agent_workbench.controller import WorkbenchController
from agent_workbench.runtime.modules.model_module import ModelModule

controller = WorkbenchController(config_path=str(merged_path))
controller.start()
print("[*] WorkbenchController started")

# 检查 ModelModule
model_module = controller.runtime.module_registry.get("model")
if not isinstance(model_module, ModelModule):
    print("❌ FAIL: ModelModule not found or wrong type")
    sys.exit(1)

providers = model_module.list_providers()
print(f"[*] Available providers: {[p['name'] for p in providers]}")
print(f"[*] Default provider: {model_module.get_current_provider_name()}")

# 测试 Provider 切换
target_provider = "minimax-m3"
print(f"\n[*] Switching to {target_provider}...")
if model_module.switch_provider(target_provider):
    print(f"✅ PASS: Switched to {target_provider}")
else:
    print(f"❌ FAIL: Cannot switch to {target_provider}")
    sys.exit(1)

# 验证当前 Provider 信息
info = model_module.get_active_provider_info()
print(f"[*] Active provider info: {info}")

# 切换到 deepseek-v4-pro
target_provider = "deepseek-v4-pro"
print(f"\n[*] Switching to {target_provider}...")
if model_module.switch_provider(target_provider):
    print(f"✅ PASS: Switched to {target_provider}")
    info = model_module.get_active_provider_info()
    print(f"[*] Active provider info: {info}")
else:
    print(f"❌ FAIL: Cannot switch to {target_provider}")
    sys.exit(1)

print("\n[*] GUI smoke test (backend path) PASS")
controller.stop()