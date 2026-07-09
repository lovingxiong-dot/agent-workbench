"""scripts/acceptance_test_starter_agent.py — Starter Agent 完整生命周期验收脚本。

运行方式：
    python scripts/acceptance_test_starter_agent.py

验收步骤：
    ① 临时 packages/ 目录没有 starter_agent → Workbench 正常加载，Navigator 无 Starter Agent
    ② 复制 packages/starter_agent → 临时 packages/ 目录
    ③ 重新加载 → Navigator 自动出现 Starter Agent
    ④ 选中 Starter Agent → Workspace 可解析，Inspector 显示属性
    ⑤ 点击 Execute → Runtime 返回结果 → statistics.execution_count 更新
    ⑥ 删除 starter_agent → 重新加载 → Navigator 自动消失
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController


def main() -> int:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_package = os.path.join(project_root, "packages", "starter_agent")

    with tempfile.TemporaryDirectory() as packages_dir:
        print("[1/6] packages/ 没有 starter_agent → Navigator 无 Starter Agent")
        controller = WorkbenchUIController(packages_dir=packages_dir)
        controller._load_packages()
        presentations = controller._build_navigator_presentations()
        assert "starter_agent" not in [p.id for p in presentations], "starter_agent should not appear"
        print("      PASS")

        print("[2/6] 复制 packages/starter_agent → 临时 packages/")
        target = os.path.join(packages_dir, "starter_agent")
        shutil.copytree(source_package, target)
        print("      PASS")

        print("[3/6] 重新加载 → Navigator 自动出现 Starter Agent")
        controller._load_packages()
        presentations = controller._build_navigator_presentations()
        assert "starter_agent" in [p.id for p in presentations], "starter_agent should appear"
        print("      PASS")

        print("[4/6] 选中 Starter Agent → Workspace / Inspector 可渲染")
        pres = next(p for p in presentations if p.id == "starter_agent")
        assert pres.view_schema_id == "starter_agent_workspace"
        schema = controller._view_schema_registry.resolve(pres)
        assert schema is not None
        print("      PASS")

        print("[5/6] 点击 Execute → Runtime 返回结果 → execution_count 更新")
        controller._current_module_id = "starter_agent"
        controller._on_action_triggered("starter_agent", "execute")
        package = controller._package_registry.get("starter_agent")
        execution_count = next(
            s["value"] for s in package.metadata["statistics"] if s["id"] == "execution_count"
        )
        assert execution_count == 1, f"expected execution_count=1, got {execution_count}"
        print(f"      PASS (execution_count={execution_count})")

        print("[6/6] 删除 starter_agent → 重新加载 → Navigator 自动消失")
        shutil.rmtree(target)
        controller._load_packages()
        presentations = controller._build_navigator_presentations()
        assert "starter_agent" not in [p.id for p in presentations], "starter_agent should disappear"
        print("      PASS")

    print("\n=== Starter Agent Acceptance Test: ALL PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
