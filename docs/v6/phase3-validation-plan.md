# Phase 3 — Product Shell Validation Plan

> **Date**: 2026-07-24
> **Status**: ENTRY REVIEW — Pre-Execution
> **Phase**: 3 Entry Review + Step 1-10 Execution Roadmap
> **Predecessor**: Phase 2-D Product Shell Closure (f378ce6)
> **Scope**: Product Shell Validation — 确认 Shell Boundary 冻结状态下的完整性和可交付性
>
> **详细执行计划**: [phase3-execution-plan.md](./phase3-execution-plan.md)
> **交叉对比报告**: [cross-comparison-report.md](./cross-comparison-report.md) — `ui-template` vs `v6-agent` UI 体系全量对比

---

## 1. Phase Objective

Phase 3 Entry Review 的目标是确认 Phase 2-D 冻结的 Product Shell 可以安全进入 Step 1-10 验证执行。

**Phase 3 定位**：不是新增能力（MCP / Browser / Workflow / Skill 是 Capability Expansion 阶段），而是对已冻结的 Product Shell 执行完整性和可交付性验证。

**Step 1-10 是已验证的 Execution Roadmap，不重新设计。**

---

## 2. Step 1-10 Execution Roadmap

```
Phase 2-D Closure
        ↓
Phase 3 Entry Review  ← 当前阶段
        ↓
Step 1:  清理冗余副本 + 环境修复
        ↓
Step 2:  v6/ui 完整性验证
        ↓
Step 3:  数据链路贯通验证
        ↓
Step 4:  Provider 接入验证
        ↓
Step 5:  LLM 真实闭环验证
        ↓
Step 6:  Session 持久化验证
        ↓
Step 7:  Module 完整性检查
        ↓
Step 8:  回归测试
        ↓
Step 9:  PyInstaller 打包
        ↓
Step 10: Windows 快捷方式
```

---

## 3. Validation Gates

每个 Step 执行后自动验证以下 Gate。通过后进入下一 Step。

### Gate A — Frozen Zone Integrity

| 检查项 | 规则 |
|--------|------|
| v6/runtime/ 19 文件 | 零变更 |
| RuntimeRequest Protocol | 零变更 |
| InteractionEvent Protocol | 零变更 |
| Controller Public API | 零变更（可新增方法，不可修改签名） |
| Decision Layer | 零变更 |

### Gate B — Data Flow

| 检查项 | 规则 |
|--------|------|
| 数据链路 | CLI → Controller → InteractionLayer → Runtime → Capability → Provider |
| 无直接 Runtime 访问 | Shell 不访问 `runtime.*` 内部 |
| 无 Provider 直接调用 | Shell 不直接调用 Provider API |

### Gate C — Regression

| 检查项 | 基线 |
|--------|------|
| tests/v6/ | 零回归 (310 pass + 4 pre-existing + 7 skip) |
| tests/interaction/ | 零回归 (30 pass) |
| tests/v6_10/ | 零回归 (17 pass) |
| tests/test_controller_interaction.py | 零回归 (4 pass + 1 skip) |

### Gate D — Structural Integrity

| 检查项 | 规则 |
|--------|------|
| 模块隔离 | 不跨模块依赖 |
| 无循环依赖 | import 图无环 |
| 无泄漏 | 不引入对 Runtime Kernel 的反向依赖 |

### Gate E — Smoke Test

| 检查项 | 规则 |
|--------|------|
| 可加载 | 关键模块初始化不报错 |
| 可运行 | CLI 和 GUI 入口可启动 |
| 可通信 | 端到端调用链路完整 |

---

## 4. Step 1-10 详细映射

> **详细执行计划参见**: [phase3-execution-plan.md](./phase3-execution-plan.md) — 包含每个 Step 的完整子任务、涉及文件、Exit Criteria。
> **设计基线参见**: [cross-comparison-report.md](./cross-comparison-report.md) — 记录 `ui-template`（设计版）与 `v6-agent`（当前版）的全量差异，为 UI 修复提供依据。

### Step 1: 清理冗余副本 + 环境修复

**目标**: 清理 `agent_workbench/v6/ui/` 下的冗余文件，修复环境依赖问题。

**检查项**:
- [ ] 识别并移除 `agent_workbench/v6/ui/` 下的 3 个冗余副本文件
- [ ] 确认 openai 包安装或保持 skip 标记
- [ ] 确认 pytest 可用
- [ ] 确认所有 import 路径正确

**风险等级**: 低

**Frozen Zone 影响**: 无（v6/ui 冗余文件清理，不修改核心文件）

**Gate 触发**: A, C

---

### Step 2: v6/ui 完整性验证

**目标**: 验证 v6/ui 22 个文件的 Frozen Foundation 状态，评估 4 个 pre-existing host_contract 失败。

**检查项**:
- [ ] 确认 v6/ui 目录结构完整（22 files）
- [ ] 评估 4 个 host_contract 失败是否阻塞后续步骤
- [ ] 验证 v6/ui 不引用 `agent_workbench/` 包（架构禁止 2）
- [ ] 验证 Renderer 层 (`presentation/renderers/v6_ui/`) 与 v6/ui 接口对齐

**风险等级**: 中

**风险原因**: 4 个 pre-existing host_contract 失败可能暴露 UI 层的接口缺口。需评估是阻塞性问题还是已知债务。

**Frozen Zone 影响**: 无（不修改 v6/ui 文件，仅评估）

**Gate 触发**: A, D

---

### Step 3: 数据链路贯通验证

**目标**: 验证 CLI → Controller → InteractionLayer → Runtime → Provider 链路完整。

**检查项**:
- [ ] CLI (`app.py::run_cli()`) 通过 Controller 提交请求
- [ ] Controller 通过 InteractionLayer 执行请求
- [ ] RuntimeRequest 格式正确传递到 Runtime
- [ ] RuntimeEvent 正确映射为 InteractionEvent
- [ ] UIEventRenderer 正确渲染到 UI

**风险等级**: 高

**风险原因**: 数据链路是 Product Shell 的核心路径。链路断裂会导致 CLI/GUI 全部不可用。

**Frozen Zone 影响**: 无（验证链路，不修改链路代码）

**Gate 触发**: A, B, E

---

### Step 4: Provider 接入验证

**目标**: 验证已注册 Provider (agnes / minimax-m3 / deepseek-v4-pro) 的接入状态。

**检查项**:
- [ ] agnes (默认) Provider 可正确加载
- [ ] minimax-m3 Provider 参数完整
- [ ] deepseek-v4-pro Provider 参数完整
- [ ] Provider 切换链路：CLI `/provider <name>` 命令正确切换
- [ ] Preflight Check 对每个 Provider 返回正确的就绪状态

**风险等级**: 中

**风险原因**: openai 包未安装导致默认 Provider 链可能失败。但 agnes/minimax/deepseek 使用独立 SDK，不受 openai 包影响。

**Frozen Zone 影响**: 无

**Gate 触发**: A, B, E

---

### Step 5: LLM 真实闭环验证

**目标**: 验证真实 LLM Provider 的端到端对话闭环。

**检查项**:
- [ ] 使用 agnes Provider 完成一次完整对话
- [ ] 使用 minimax-m3 Provider 完成一次完整对话
- [ ] 使用 deepseek-v4-pro Provider 完成一次完整对话
- [ ] 验证非流式响应正确
- [ ] 验证错误处理（Provider 不可用时的友好降级）

**风险等级**: 高

**风险原因**: 真实 LLM 调用涉及网络 I/O、API Key、模型可用性。需确保 Provider 配置正确且 API 可访问。

**Frozen Zone 影响**: 无

**Gate 触发**: A, B, C, E

---

### Step 6: Session 持久化验证

**目标**: 验证 Session 数据的持久化和恢复。

**检查项**:
- [ ] Session 数据正确写入 `storage/sessions/`
- [ ] Session 关闭后重新打开，历史消息正确恢复
- [ ] 多 Session 切换不丢失数据
- [ ] Session 文件格式有效（JSON 可解析）

**风险等级**: 中

**风险原因**: Session 持久化影响用户体验。格式变更需向后兼容。

**Frozen Zone 影响**: 无

**Gate 触发**: A, C, D

---

### Step 7: Module 完整性检查

**目标**: 验证 10 个 BaseRuntimeModule 的加载和运行状态。

**检查项**:
- [ ] Runtime / Session / Config / Profile / Prompt / Model / Tool / Memory / Strategy / Trace 全部加载
- [ ] 每个 Module 的 `initialize` 不报错
- [ ] 每个 Module 的 `metadata()` 返回有效数据
- [ ] Module 间依赖关系正确

**风险等级**: 低

**Frozen Zone 影响**: 无

**Gate 触发**: A, C, D

---

### Step 8: 回归测试

**目标**: 全量回归测试，确保 Step 1-7 未引入回归。

**检查项**:
- [ ] `pytest tests/v6/` — 310/310 pass (baseline)
- [ ] `pytest tests/interaction/` — 30/30 pass
- [ ] `pytest tests/v6_10/` — 17/17 pass
- [ ] `pytest tests/test_controller_interaction.py` — 4/4 pass + 1 skip
- [ ] 新增测试（如有）全部通过

**风险等级**: 低

**风险原因**: 回归测试是防御性检查。Step 1-7 不应引入变更，回归应自动通过。

**Frozen Zone 影响**: 无

**Gate 触发**: A, B, C, D

---

### Step 9: PyInstaller 打包

**目标**: 产出可独立运行的 exe。

**检查项**:
- [ ] `pyinstaller agent_workbench.spec` 构建成功
- [ ] exe 启动不报错
- [ ] exe 中的 CLI 入口可用
- [ ] exe 中的 GUI 入口可用（如适用）
- [ ] 依赖正确打包（PySide6、Provider SDK 等）

**风险等级**: 高

**风险原因**: PyInstaller 对动态导入、二进制依赖、资源文件路径敏感。Qt 组件打包是常见失败点。

**Frozen Zone 影响**: 无

**Gate 触发**: E

---

### Step 10: Windows 快捷方式

**目标**: 创建桌面快捷方式，完成可交付产物。

**检查项**:
- [ ] 桌面快捷方式指向 exe 正确路径
- [ ] 快捷方式图标正确
- [ ] 双击快捷方式可启动 Workbench
- [ ] 卸载/清理不影响系统

**风险等级**: 低

**Frozen Zone 影响**: 无

**Gate 触发**: E

---

## 5. Risk Assessment Matrix

| Step | 名称 | 风险等级 | 风险原因 | 缓解措施 |
|------|------|----------|----------|----------|
| 1 | 清理冗余副本 + 环境修复 | 低 | 文件清理，操作面小 | 清理前备份，`git diff` 确认 |
| 2 | v6/ui 完整性验证 | 中 | host_contract 失败可能阻塞 | 评估影响，必要时标记为已知债 |
| 3 | 数据链路贯通验证 | **高** | 核心链路，断裂影响全局 | 使用已有测试链路验证 |
| 4 | Provider 接入验证 | 中 | openai 包缺失，但其他 Provider 可用 | 优先验证 agnes/minimax/deepseek |
| 5 | LLM 真实闭环验证 | **高** | 网络 I/O、API Key、模型可用性 | 逐个 Provider 验证，单个失败不阻塞 |
| 6 | Session 持久化验证 | 中 | 存储格式兼容性 | 向后兼容，不修改格式 |
| 7 | Module 完整性检查 | 低 | 10 个 Module 已稳定 | 自动化检查 |
| 8 | 回归测试 | 低 | 防御性检查 | 复用已有测试套件 |
| 9 | PyInstaller 打包 | **高** | Qt 组件打包 | 先验证依赖可打包，再完整构建 |
| 10 | Windows 快捷方式 | 低 | 文件系统操作 | 简单路径创建 |

---

## 6. Frozen Boundary Consistency Check

### 6.1 Do Not Touch — Confirmed

| 范围 | 文件数 | Step 1-10 影响 |
|------|--------|---------------|
| Runtime Kernel | 19 files | 零修改（全部只读验证） |
| Decision Layer | `decision_manager.py` | 零修改 |
| Interaction Protocol | `request.py`, `event.py`, `layer.py` | 零修改 |
| Controller Contract | `controller.py` 27 methods | 零修改（签名不变） |
| v6/ui | 22 files | 仅评估，不修改（Step 1 清理冗余副本，不修改核心文件） |

### 6.2 四项禁止事项 — 合规确认

| 禁止 | Step 1-10 合规 | 说明 |
|------|---------------|------|
| Skill 不得进入 Runtime Kernel | ✅ | 不涉及 Skill 变更 |
| Memory 不得进入 Capability | ✅ | 不涉及 Memory 变更 |
| AgentIdentityRegistry 不负责执行 | ✅ | 不涉及 Agent Identity 变更 |
| PackageRegistry 不保存运行状态 | ✅ | 不涉及 Package 变更 |

### 6.3 Step 1-10 与 Frozen Files 交集

**零交集**。Step 1-10 是验证性步骤，不修改任何 Frozen Zone 文件。所有操作限定在：
- 文件清理（冗余副本）
- 环境修复（pip install）
- 测试执行（pytest）
- 打包（PyInstaller）
- 快捷方式（Windows Shell）

---

## 7. Execution Ready Report

### 7.1 Pre-Flight Checklist

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | Phase 2-D Closure committed (f378ce6) | ✅ |
| 2 | Frozen Zone 19 文件零变更 | ✅ |
| 3 | Controller Public API 冻结 (ADR-011) | ✅ |
| 4 | Gate 2/3/4 PASS | ✅ |
| 5 | Interaction Layer 30/30 PASS | ✅ |
| 6 | v6-core 310/310 PASS | ✅ |
| 7 | openai 环境依赖已标记 | ✅ |
| 8 | ADR-010 (PackageAction bypass) 已知 | ✅ |
| 9 | ADR-011 (Controller API freeze) 已知 | ✅ |
| 10 | 3 个 Provider 已注册 (agnes/minimax/deepseek) | ✅ |

### 7.2 Blocking Issues

**无阻塞性问题**。4 个 pre-existing host_contract 失败在 Step 2 中评估。

### 7.3 Known Pre-Existing Issues

| # | 问题 | 等级 | 影响 Step |
|---|------|------|----------|
| 1 | openai 包未安装 | 低 | Step 4, 5 — 已标记 skip，不影响其他 Provider |
| 2 | host_contract 4 FAIL | 中 | Step 2 — 待评估是否阻塞 |
| 3 | `execute_agent_action` bypass | R1 | 不影响 Step 1-10（ADR-010 已记录） |
| 4 | Controller 职责膨胀 | R1 | 不影响 Step 1-10（ADR-011 已记录） |

### 7.4 Decision

```
Phase 3 Entry Review: PASS
Condition: 4 pre-existing host_contract failures assessed in Step 2
Step 1-10 Execution Plan: CONFIRMED
Ready for Step 1: YES
Blocking Issues: NONE
```

---

## 8. Appendix: Step 1-10 Quick Reference

| Step | 名称 | 风险 | Gate | 类型 |
|------|------|------|------|------|
| 1 | 清理冗余副本 + 环境修复 | 低 | A, C | 清理 |
| 2 | v6/ui 完整性验证 | 中 | A, D | 验证 |
| 3 | 数据链路贯通验证 | **高** | A, B, E | 验证 |
| 4 | Provider 接入验证 | 中 | A, B, E | 验证 |
| 5 | LLM 真实闭环验证 | **高** | A, B, C, E | 验证 |
| 6 | Session 持久化验证 | 中 | A, C, D | 验证 |
| 7 | Module 完整性检查 | 低 | A, C, D | 验证 |
| 8 | 回归测试 | 低 | A, B, C, D | 验证 |
| 9 | PyInstaller 打包 | **高** | E | 构建 |
| 10 | Windows 快捷方式 | 低 | E | 交付 |

### Execution Rules

1. 每个 Step 执行后立即验证
2. 验证通过后进入下一 Step
3. 发现问题时记录 Issue / Impact / Recommended Fix，不直接扩大修改范围
4. 禁止修改 Frozen Boundary、Runtime Kernel、Interaction Protocol、Controller Contract
5. Step 不通过时暂停，等待 Review

### Related Documents

| 文档 | 用途 |
|------|------|
| [phase3-execution-plan.md](./phase3-execution-plan.md) | Phase 3 详细执行计划（子任务、涉及文件、Exit Criteria） |
| [cross-comparison-report.md](./cross-comparison-report.md) | `ui-template` vs `v6-agent` UI 体系全量交叉对比 |
| [product-shell-phase-report.md](./product-shell-phase-report.md) | Phase 2-D Product Shell Closure Report |
| [architecture-boundaries.md](./architecture-boundaries.md) | Frozen Zone + 四项禁止事项 |