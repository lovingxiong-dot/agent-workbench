# Workbench OS 1.0 Product Contract

> 产品契约，不是技术实现文档。
>
> 它定义 Workbench OS 1.0 中每个核心概念是什么、保存什么、职责边界在哪里、不属于什么。
>
> Qt / Web / CLI / Remote 任何 Frontend 与 Backend 都遵守同一套产品定义。
>
> **本契约在 v6.12.0-rc.1 之前冻结。**

---

## Workbench OS

Workbench OS 是一个桌面操作系统，用于安装、管理、运行 Agent。

它不是聊天软件。
它不是插件市场。
它不是模型客户端。

Workbench OS 的核心体验是：

> 用户选择一个 Agent，进入一个 Workspace，通过 Inspector 查看状态，通过 CommandBar 下达指令，Agent 在 Runtime 中执行，结果反馈到 Workspace。

---

## Project

Project 是 Workbench OS 的工作目录。

它保存：

- 会话（Conversations）
- 配置（Config）
- 安装的 Package
- 运行时状态（Runtime State）
- 日志与 Trace

一个 Project 对应一个数据目录。用户打开 Project，就是打开一个完整的工作环境。

Project 不保存代码。代码属于 Package 或外部仓库。

---

## Conversation

Conversation 是 Workbench OS 的基本工作单元。

它保存：

- id
- title
- summary
- icon
- created_at
- updated_at
- last_activity
- workspace_id
- pinned
- 用户消息
- Agent 回复
- Task
- Metadata

Conversation 不属于某个 UI。任何 Frontend 都读取同一 Conversation。

Conversation 的 Metadata 由 Conversation Domain 生成与维护，UI 只负责显示。

---

## Package

Package 是 Agent 的安装单元。

Package 描述：

- 身份（id / name / version / author）
- 能力（Capabilities）
- 视图（ViewSchema）
- Runtime 配置
- 资源（Resources）
- Prompt

Workbench OS 永远运行 Package，而不是直接运行 Python 脚本。

Package 不依赖 Qt。Package 只能声明组件类型，由宿主 Workbench 决定渲染方式。

Package 的入口是 `manifest.json`。没有 `manifest.json` 的目录被 Loader 忽略。

---

## Workspace

Workspace 是 Package 或功能模块被打开后的主区域。

一个 Workspace 展示：

- 该模块的核心内容
- Toolbar 操作
- 与该模块相关的视觉反馈

Workspace 由 ViewSchema 驱动。同一个 Package 在不同上下文中可以打开不同 Workspace。

Workspace 不保存持久状态。持久状态属于 Conversation 或 Project。

---

## Navigator

Navigator 是 Workbench OS 的导航面板。

它显示：

- 已安装的 Agent（Packages）
- 固定 Workspace
- 最近使用
- 设置分类

Navigator 只处理选择。它不知道被选中对象的具体实现。

选中变化通过事件通知 Workbench，由 Workbench 决定打开哪个 Workspace 与 Inspector。

---

## Inspector

Inspector 是 Workbench OS 的属性面板。

它显示当前选中对象的：

- Properties
- Statistics
- Actions
- 按 ViewSchema 定义组织的 Tab

Inspector 不持有业务对象。它只显示由 PresentationModel 提供的数据，并通过事件向上报告 Action 触发与属性变更。

---

## CommandBar

CommandBar 是 Workbench OS 的输入入口。

它接收用户输入，并将输入提交给当前激活的 Agent 或 Workspace。

CommandBar 不解析命令语义。解析由 Runtime 或当前 Agent 完成。

---

## StatusBar

StatusBar 是 Workbench OS 的状态条。

它显示：

- Runtime 状态
- 当前选中的模块
- 后台任务进度
- 简短提示（如 Loading Package...）

StatusBar 永远只读。用户不能直接在 StatusBar 上编辑状态。

---

## Agent

Agent 是 Workbench OS 中的可执行角色。

Agent 由一个 Package 定义。一个 Package 可以描述一个或多个 Agent。

Agent 拥有：

- 身份
- 能力
- Prompt
- Memory
- Tool 集合
- 运行时策略

Agent 在 Runtime 中执行，输出结果到 Workspace 或 Conversation。

---

## Capability

Capability 是 Agent 能做的事。

例如：

- 发送消息
- 调用工具
- 读写 Memory
- 执行 Workflow

Capability 通过 Metadata 声明，由 Runtime 解析并执行。

---

## Runtime

Runtime 是 Workbench OS 的执行引擎。

它负责：

- 接收 Task
- 选择 Engine
- 调用 Capability
- 管理状态
- 发布 Trace 事件

Runtime 不直接渲染 UI。Runtime 通过 EventBus 与 Binding 向 UI 反馈状态。

---

## Metadata

Metadata 是 Workbench OS 中对象的描述数据。

它描述：

- 对象是谁
- 对象有什么属性
- 对象能做什么
- 对象的状态统计

Metadata 不绑定任何 UI。UI 通过 MetadataAdapter 将 Metadata 转换为 PresentationModel。

---

## Presentation

Presentation 是 Metadata 在 UI 层的表达形式。

它包含：

- 显示名称
- 图标
- 属性列表
- 统计列表
- 操作列表
- 分类
- ViewSchema 引用

Presentation 不知道 Runtime 或 Package 的实现细节。它只供 ViewSchemaRenderer 消费。

---

## ViewSchema

ViewSchema 是 Workspace / Inspector / Toolbar / StatusBar 的布局协议。

它定义：

- 哪些属性显示在 Inspector 的哪个 Tab
- Toolbar 上有什么按钮
- StatusBar 上显示哪些统计
- Workspace 使用哪个内置组件

ViewSchema 只引用 PresentationModel 的字段名，不绑定具体值。

---

## Workbench

Workbench 是 Workbench OS 的宿主框架。

它负责：

- 加载 Package
- 管理 Workspace
- 渲染 Navigator / Inspector / CommandBar / StatusBar
- 协调 UI 事件与 Runtime

Workbench 不拥有 Runtime 或业务对象。Workbench 由 Runtime 状态驱动，只处理选择并通过事件通信。

---

## About

About 是 Workbench OS 的关于窗口。

它显示：

- Workbench OS 1.0
- 当前版本号
- Git Commit
- Python 版本
- Qt 版本
- 已安装 Package 数量
- Runtime 状态
- License

---

## Settings

Settings 是 Workbench OS 的轻量设置入口。

第一版只包括：

- Theme
- Language
- Package Directory
- Workspace Directory
- Log Level

Settings 不保存业务配置。业务配置属于 Project。

---

## 冻结声明

本 Product Contract 自 **v6.12.0-rc.1** 起冻结。

冻结后：

- 上述概念名称不再更改。
- 核心字段不再删除，只能扩展。
- 新增概念必须经过架构评审。

所有实现、文档、测试、API 都围绕本契约展开。
