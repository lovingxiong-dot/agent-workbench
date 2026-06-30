# 多会话管理 v4 代码框架设计文档

> **版本**：v4.0.0 — Chat-as-Authority 架构  
> **核心原则**：消息是权威，UI 是投影，Worker 绑定环境，切换不操作 Worker  
> **设计目标**：成熟聊天软件的丝滑体验 + AI 任务状态机 + 多会话并发槽位控制

---

## 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                      MainWindow（薄编排层）                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 会话列表  │ │ ChatView │ │ 状态栏  │ │ 侧边栏  │           │
│  │ 纯数据驱动│ │ 消息权威  │ │ 状态徽章│ │ 模式切换│           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└──────────┬──────────────────────────────────┬────────────────────┘
           │                                  │
           ▼                                  ▼
    ┌──────────────┐                  ┌──────────────┐
    │  UIRenderer   │◄─── 消息事件 ────│ MessageBus  │
    │  只渲染当前    │                  │  事件路由    │
    │  丢弃不阻塞    │                  │  解耦核心    │
    └──────────────┘                  └──────┬───────┘
                                              │
           ┌──────────────┬──────────────────┬┴──────────────┐
           │              │                  │               │
           ▼              ▼                  ▼               ▼
    ┌──────────┐   ┌──────────┐      ┌──────────┐    ┌──────────┐
    │ Session  │   │ Session  │      │  Session │    │  Session │
    │Runtime A │   │Runtime B │  ... │Runtime C │    │Runtime D │
    │ (ACTIVE) │   │(BACKGROUND)│     │ (BACKGROUND)│   │ (BACKGROUND)│
    │         │    │         │      │           │    │          │
    │ ┌──────┐│    │ ┌──────┐│      │ ┌──────┐ │    │ ┌──────┐ │
    │ │Queue ││    │ │Queue ││      │ │Queue │ │    │ │Queue │ │
    │ │2-Slot││    │ │2-Slot││      │ │2-Slot│ │    │ │2-Slot│ │
    │ └──────┘│    │ └──────┘│      │ └──────┘ │    │ └──────┘ │
    │ ┌──────┐│    │ ┌──────┐│      │ ┌──────┐ │    │ ┌──────┐ │
    │ │Phase ││    │ │Phase ││      │ │Phase │ │    │ │Phase │ │
    │ │State ││    │ │State ││      │ │State │ │    │ │State │ │
    │ │机   ││    │ │机   ││      │ │机   │ │    │ │机   │ │
    │ └──────┘│    │ └──────┘│      │ └──────┘ │    │ └──────┘ │
    │ ┌──────┐│    │ ┌──────┐│      │ ┌──────┐ │    │ ┌──────┐ │
    │ │Worker││    │ │Worker││      │ │Worker│ │    │ │Worker│ │
    │ │环境  ││    │ │环境  ││      │ │环境  │ │    │ │环境  │ │
    │ └──────┘│    │ └──────┘│      │ └──────┘ │    │ └──────┘ │
    └──────────┘   └──────────┘      └──────────┘    └──────────┘
           │              │                  │               │
           └──────────────┴──────────┬──────┴───────────────┘
                                    │
                                    ▼
                           ┌──────────────┐
                           │ SessionOrchestrator│
                           │  协调中心      │
                           │  槽位控制      │
                           │  环境绑定      │
                           └──────────────┘
                                    │
                                    ▼
                           ┌──────────────┐
                           │ WorkerManager  │
                           │ 环境感知管理   │
                           │ 最大并发槽位   │
                           └──────────────┘
                                    │
                                    ▼
                           ┌──────────────┐
                           │ SessionRepository│
                           │  DB 持久化    │
                           │  消息权威     │
                           └──────────────┘
```

---

## 核心设计原则

### 1. 消息是权威（Chat-as-Authority）

- 所有消息的唯一来源：SQLite 数据库
- 内存缓存只用于性能优化，不用于权威查询
- 会话切换时：从 DB 加载，不从内存取
- 后台 Worker 完成的消息：直接写 DB，UI 切回时自然可见

### 2. 会话切换不操作 Worker

- 切换会话 = 只切 UI 指针，不操作 Worker 状态
- Worker 绑定到任务，不绑定到前台/后台状态
- 后台任务的 chunk 信号被 UIRenderer 丢弃，但不阻塞 Worker
- 环境（project_root）绑定到 SessionRuntime，切回时自动恢复

### 3. 状态机只控制 Phase 流程

- PhaseManager 只管 Analyze → Confirm → Execute → Verify → Archive
- 状态机不控制 Worker 生命周期
- 状态机不控制 UI 渲染
- 状态机只通过 MessageBus 发射事件，不直接调用 UI

### 4. 槽位控制只约束并发数

- 系统最多同时运行 N 个 Worker（默认 5）
- 槽位控制只约束 Worker 创建，不控制消息发送
- 超出槽位的新任务：排队等待，而非拒绝
- 每个会话的 QueueManager 独立控制本会话的双槽位（streaming + pending）

### 5. 环境感知（Work vs Chat）

- **Chat 模式**：纯对话，无环境，project_root = ""
- **Work 模式**：任务执行，有环境，project_root = 项目目录
- Worker 创建时绑定环境：project_root、tools、interpreter
- 环境切换时：旧环境 Worker 继续运行，新环境创建新 Worker
- 环境元数据持久化到 DB，恢复时自动重建

---

## 关键架构决策对比

| 决策 | v3（旧） | v4（新） | 原因 |
|------|---------|---------|------|
| 消息权威 | 内存 `_sessions` 字典 | SQLite DB | 避免切换丢失，后台结果可恢复 |
| 会话切换 | 停止 Worker，清空状态 | 只切 UI，Worker 继续 | 后台任务不中断 |
| Worker 状态 | PAUSED / RUNNING / STOPPED | 绑定到任务生命周期 | 简化状态，减少竞态 |
| 列表维护 | 手动 `add/move/remove` | 全量 `refresh` 数据驱动 | 减少手动同步错误 |
| 环境切换 | 无环境概念 | project_root + tools 绑定 | AI 知道"自己在哪" |
| 并发控制 | 全局单队列 | 每会话双槽位 + 系统并发槽位 | 更精细的并发管理 |
| 状态机 | 耦合 Worker/Queue/UI | 只控制 Phase 流程 | 单一职责，降低复杂度 |

---

## 目录结构

```
v4/
├── __init__.py
├── models.py              # 纯数据模型（Session, Message, Environment）
├── repository.py          # DB 持久化（SessionRepository）
├── runtime.py             # 会话运行时（SessionRuntime）
├── queue.py               # 队列管理（QueueManager）— 只控制槽位
├── worker_manager.py      # Worker 管理（环境感知 + 并发槽位）
├── orchestrator.py        # 会话协调器（SessionOrchestrator）
├── ui_renderer.py         # UI 渲染器（UIRenderer）
├── events.py              # 消息总线事件定义
├── event_bus.py           # 消息总线（MessageBus）
├── main_window.py         # 主窗口（薄编排层）
├── conversation_list.py    # 会话列表（纯数据驱动）
└── tests/
    ├── test_session.py
    ├── test_queue.py
    ├── test_worker_manager.py
    ├── test_orchestrator.py
    └── test_integration.py
```

---

## 设计说明

### 为什么删除 SessionRegistry / WorkerManager.pause/resume？

- v3 的 `SessionRegistry` 引入 PAUSED/STOPPED 状态，但从未真正实现 Worker 的 PAUSED 状态（实际上 Worker 被强制 stop）
- 真正的"后台运行"不需要暂停：Worker 在子线程运行，UI 只是不渲染它的输出
- 删除 PAUSED/STOPPED 状态机，Worker 只绑定到任务：任务开始 → Worker 创建 → 任务完成 → Worker 释放

### 为什么 UIRenderer 丢弃事件而非阻塞？

- 事件总线的一个设计原则是：生产者不阻塞，消费者按需处理
- 如果后台 Worker 的 chunk 信号被阻塞，Worker 的 asyncio 事件循环可能被卡住
- 丢弃事件：后台任务继续运行，消息已写 DB，切回时自然可见

### 为什么环境绑定到 SessionRuntime 而非 Worker？

- Worker 是任务执行者，环境是任务的上下文
- 同一会话的多轮任务可能共享环境（project_root、tools 等）
- 环境绑定到 SessionRuntime，Worker 创建时从 Runtime 获取环境
- 环境切换时，当前 Worker 继续（旧环境），新任务创建新 Worker（新环境）

### 为什么支持"可重名"？

- 会话标题不是唯一标识，session_id 才是
- 允许重名避免用户被"新对话 (2)"这样的命名困扰
- 列表排序不依赖标题，依赖时间戳 + 置顶标记

### 为什么自动按时间排序？

- 最活跃（最近有消息）的会话排在前面
- 排序只影响显示顺序，不影响 session_id 或数据关系
- 置顶会话固定在最上方，不受时间排序影响

---

## 测试策略

| 测试 | 目标 | 覆盖 |
|------|------|------|
| 会话创建/切换/删除 | 数据完整性，不丢失消息 | 100% |
| 消息发送/接收 | DB 权威，内存缓存一致 | 100% |
| 会话切换不中断 | 后台 Worker 继续，切回可见 | 100% |
| 队列槽位 | 双槽位满时拒绝，完成后自动出队 | 100% |
| 并发槽位 | 最多 N 个 Worker，超出排队 | 100% |
| 环境切换 | project_root 切换，工具上下文变化 | 100% |
| 状态机 | Phase 流程，空阶段跳过，错误处理 | 100% |
| UI 事件丢弃 | 后台事件不阻塞，切回正确加载 | 100% |
| 列表排序 | 按时间排序 + 置顶 | 100% |
| 重名 | 同标题多会话，列表正常显示 | 100% |

---

## 验证清单（手动）

1. 创建 3 个全局对话，发送不同消息，切换会话 → 消息正确显示
2. 切换到项目 A 的 Work 会话，发送"列出当前目录" → AI 显示项目 A 目录
3. 切换到项目 B 的 Work 会话，发送"列出当前目录" → AI 显示项目 B 目录
4. 在 A 会话发送任务，切换到 B 会话聊天，切回 A → 任务已完成，结果可见
5. 快速发送 10 条消息（系统并发槽位=5）→ 前 5 个 Worker 创建，后 5 个排队
6. 任务执行中点击停止 → 当前任务取消，队列自动出队下一个
7. 置顶 2 个会话，观察列表 → 置顶会话固定在最上方，其余按时间排序
8. 所有会话标题设为"新对话" → 列表正常显示，可区分
9. 重启程序 → 所有会话恢复，消息完整，环境正确

