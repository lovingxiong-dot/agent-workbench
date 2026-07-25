# Phase 3 Context — 架构上下文索引

> **创建日期**: 2026-07-24
> **更新日期**: 2026-07-24
> **状态**: Canonical source migrated to [architecture-context.md](./architecture-context.md)

---

## 本文档已升级

`phase3-context.md` 最初是 Phase 3 执行时的临时上下文文档，用于防止 Agent 上下文压缩后丢失架构语义。

2026-07-24 经过评估，这些内容不限于 Phase 3，而是长期架构知识。因此已升级为独立文档：

| 迁移内容 | 新位置 |
|----------|--------|
| Boundary Map、Change Permission Matrix、Frozen Zone、数据流全貌 | [architecture-context.md](./architecture-context.md) |
| API 所有权模型、验证顺序、审计规则 | [api-ownership-model.md](./api-ownership-model.md) |

---

## 执行前必读

Agent 执行任何 Phase 3 Step 前，必须按顺序读取：

```
1. architecture-context.md     ← 架构语义（长期）：Boundary Map、Frozen Zone、数据流
2. api-ownership-model.md      ← API 所有权：能力归属、验证顺序、审计规则
3. phase3-execution-plan.md    ← 执行清单：Step 1-10 子任务
4. 执行当前 Step
5. 输出 Step Report
```

---

## 文档引用链

```
architecture-context.md        ← 长期架构知识（Agent 执行前必读）
api-ownership-model.md         ← API 所有权模型
phase3-execution-plan.md       ← Phase 3 执行清单（Step 1-10 子任务）
phase3-validation-plan.md      ← Phase 3 验证框架（Gate 定义 + 风险评估）
phase3-step-2-report.md        ← Step 2 独立审计报告
cross-comparison-report.md     ← UI 设计基线 vs 当前实现
architecture-boundaries.md     ← Frozen Zone 定义
SPEC.md                        ← V6 接口与信号契约
product-contract.md            ← Workbench OS 产品契约
product-shell-phase-report.md  ← Phase 2-D Closure Report
```