# Changelog

## v6.12.0-beta.6 (2026-07-10) — Package Registry Lifecycle + Workbench OS Branding

> **里程碑语义**：Commit 12.2 冻结 Package 生命周期接口：`discover()` / `load()` / `unload()` / `reload()` / `list()`。`reload()` 先抛出 `NotImplementedError`，但接口已经锁定。同时确立产品品牌：完成 UI 最终打包后的第一个产品命名定为 **Workbench OS 1.0**，并生成对应应用图标（PNG/ICO）。

### Added
- `agent_workbench/package/package_info.py`：`PackageInfo` 运行时包信息。
- `agent_workbench/package/registry.py`：`PackageRegistry` 生命周期注册表。
  - `discover(packages_dir)`：扫描并返回合法 manifest 列表。
  - `load(manifest)`：加载 manifest 指向的 metadata / capabilities / view_schema / runtime 文件。
  - `unload(package_id)`：卸载指定包。
  - `reload(package_id)`：接口已冻结，当前 `NotImplementedError`。
  - `list()` / `get(package_id)`：查询已加载包。
- `agent_workbench/package/__init__.py`：导出 `PackageInfo` / `PackageRegistry`。
- `tests/package/test_package_registry.py`：8 个非 GUI 单元测试，覆盖 Registry 全生命周期。
- `agent_workbench/resources/`：
  - `app_icon.png` / `app_icon.ico`：Workbench OS 应用图标（黑色背景 + 三层白色嵌套圆角矩形）。
  - `__init__.py`：导出 `APP_ICON_PNG` / `APP_ICON_ICO`。
- `agent_workbench/__init__.py`：
  - 更新 `__version__` 为 `v6.12.0-beta.5`。
  - 新增 `PRODUCT_NAME = "Workbench OS"`，`PRODUCT_VERSION = "1.0"`，`DISPLAY_NAME = "Workbench OS 1.0"`。

### Design Constraints
- Package Registry 不依赖 Qt。
- Package 无权注册 Renderer。
- `reload()` 接口先冻结，允许后续无缝实现。

### Tests
- `pytest tests/`：**769/769 passed**（新增 8 个 Registry 测试；收尾 Qt 退出码 `3221226505` 与 `QThread: Destroyed while thread is still running` 为 Windows 已知现象，不影响断言结果）。

### Next Phase
- **Commit 12.3**：Workbench Integration（Package → Metadata → Navigator / Workspace）。

---

## v6.12.0-beta.5 (2026-07-10) — Package Contract Freeze（Commit 12.1）

> **里程碑语义**：Commit 12 拆分为 12.1-12.4 四个子提交，12.1 只冻结 Package 契约，不加载任何 Agent。Package 以 `manifest.json` 为唯一入口，`PackageLoader.scan()` 仅读取含 `manifest.json` 的子目录，无 manifest 的目录直接忽略。非法 manifest 被校验并跳过，不影响其他包。Package 层明确禁止依赖 Qt 和注册 Renderer。

### Added
- `agent_workbench/package/`：
  - `__init__.py`：导出 `PackageLoader`、`PackageManifest`、`PackageValidationError`。
  - `exceptions.py`：`PackageError` / `PackageValidationError`。
  - `manifest.py`：`PackageManifest` 定义与解析，支持 `id` / `version` / `schema_version` / `metadata` / `capabilities` / `view_schema` / `runtime` 字段。
  - `loader.py`：`PackageLoader.scan()` 扫描 `packages/` 目录并返回合法 manifest 列表。
- `packages/starter_agent/manifest.json`：第一个示例 Package 的最小 manifest。
- `tests/package/test_package_contract.py`：14 个非 GUI 单元测试，覆盖 manifest 解析、校验、Loader 扫描行为。

### Design Constraints
- Package 不允许直接依赖 Qt（禁止 `from PySide6 ...`）。
- Package 不允许注册 Renderer；Renderer 永远属于 Workbench。
- Loader 不扫描所有 `.json`，只读取 `manifest.json`。

### Tests
- `pytest tests/`：**761/761 passed**（新增 14 个 Package Contract 测试；收尾 Qt 退出码 `3221226505` 为 Windows 已知现象，不影响断言结果）。

### Next Phase
- **Commit 12.2**：Package Registry（discover / load / unload / reload 生命周期）。

---

## v6.12.0-beta.4 (2026-07-10) — ViewComponentRegistry 契约层

> **里程碑语义**：Commit 10 建立 View 层组件注册与查找的最小契约。`ViewComponentRegistry` 只负责「找得到」`ViewComponentDefinition`，不负责创建任何 Qt 控件；`ViewSchemaRenderer` 改为以 `render(component_id)` 为入口，按 `toolbar` / `status_bar` / `inspector` / `workspace` 分发渲染。Terminal / Editor / Monaco / Chart / Graph / Dock / Tree / Split 等明确禁止进入 Registry，它们属于 Builtin Component。这一层是 Commit 12 Agent Package 的基础设施铺垫。

### Added
- `agent_workbench/ui/workbench/view_component.py`：定义 `ViewComponentDefinition`，仅含 `id`、`renderer`、`supported_schema`、`supported_binding`、`default_size` 五个字段。
- `agent_workbench/ui/workbench/view_component_registry.py`：实现 `ViewComponentRegistry`，仅暴露 `register` / `unregister` / `resolve` / `list` 四个接口。
- `agent_workbench/ui/workbench/view_schema_renderer.py`：
  - 构造函数新增 `component_registry` 参数。
  - 新增 `render_component(component_id, schema, presentation)` 入口，按组件 ID 分发到现有四个区域渲染方法。
  - `render(schema, presentation)` 内部改为遍历内置组件 ID 逐个分发。
- `tests/ui/test_view_component_registry.py`：6 个非 GUI 单元测试，覆盖 Registry 四个接口与 Renderer 组件分发。

### Tests
- `pytest tests/`：**747/747 passed**（新增 6 个 ViewComponent 测试；收尾 Qt 退出码 `3221226505` 为 Windows 已知现象，不影响断言结果）。

### Architecture
```text
ViewComponentRegistry
         │
         ▼
ViewComponentDefinition  (id + renderer + schema/binding/size)
         │
         ▼
ViewSchemaRenderer.render_component(component_id)
         │
         ▼
_builtin toolbar / status_bar / inspector / workspace
```

### Next Phase
- **Commit 12**：Agent Package + Echo Agent（分水岭：Agent 成为可放置对象）。

---

## v6.12.0-beta.3 (2026-07-10) — Dynamic UI Binding Layer

> **里程碑语义**：Commit 9 在 ViewSchema 与 Qt Renderer 之间增加 Dynamic UI Binding Layer，实现 Metadata → PresentationModel → ViewSchema → BindingContext → Qt Renderer 的完整数据流。Runtime 状态（status / provider / model / session 等）通过 `BindingProvider` 按 namespace 注册到 `BindingContext`，ViewSchema 以声明式 `BindingSource` 路径引用，Renderer 在渲染时动态解析。UI 不再直接访问 Runtime，新增状态项只需在 Schema 中声明绑定路径，无需修改 Renderer。

### Added
- `agent_workbench/ui/workbench/binding_context.py`：新增 Binding Layer。
  - `BindingProvider`：按 namespace 提供动态数据 getter。
  - `BindingRegistry`：Provider 注册表。
  - `BindingContext`：按 `namespace.key1.key2` 路径解析 `BindingSource`，支持静态值、Provider 动态值、format 格式化与异常回退。
- `agent_workbench/ui/workbench/view_schema.py`：
  - 新增 `BindingSource` 与 `PropertyBinding`，支持 `path` + `format` 声明动态数据来源。
  - `StatusItemSchema` 增加 `source="binding"` 与 `binding` 字段。
- `agent_workbench/ui/workbench/view_schema_renderer.py`：
  - 构造函数接收 `BindingContext`。
  - `_resolve_status_item()` 支持 `statistics` / `binding` / `runtime`（兼容旧 schema）三种来源。
  - `_apply_property_bindings()` 为 `editable=False` 且带 `binding` 的 PropertyPresentation 注入 Runtime 当前值。
  - 新增 `refresh()` 方法，仅刷新 StatusBar 与 Inspector 中受 Binding 影响的区域。
- `agent_workbench/ui/workbench/presentation.py`：`PropertyPresentation` 增加 `binding` 字段。
- `agent_workbench/ui/workbench/view_schema_registry.py`：所有默认 Workspace Schema 的 StatusBar 项改为 `source="binding"`，通过 `BindingSource` 引用 `runtime.status` / `runtime.provider` / `runtime.model` / `runtime.session` / `runtime.latency`。
- `agent_workbench/ui/workbench_ui_controller.py`：
  - 初始化 `BindingContext` 并注册 `runtime` Provider，将 `_runtime_status()` 核心状态暴露给 Binding Layer。
  - `_on_selection_changed()` 与 `_refresh_status_bar()` 改为调用 `ViewSchemaRenderer.render(schema, pres)`（移除旧的 `runtime_status=` 参数）。
- `tests/ui/test_binding_context.py`：15 个非 GUI 单元测试，覆盖 BindingRegistry、BindingContext 路径解析、format、静态值、Provider 异常回退、优先级等。

### Changed
- `agent_workbench/ui/workbench/status_bar_host.py`：恢复 `set_statistics()` 接口并委托给 `StatusBar.set_statistics()`，修复 Renderer 调用缺失。
- `tests/ui/test_view_schema.py`：更新 `test_renderer_status_bar_selects_by_schema` 为 BindingContext 驱动。

### Tests
- `pytest tests/`：**741/741 passed**（新增 15 个 Binding 测试；收尾 Qt 退出码 `3221226505` 为 Windows 已知现象，不影响断言结果）。

### Architecture
```text
Runtime / Task / Provider
         │
         ▼
BindingProvider (namespace)
         │
         ▼
BindingContext
         │
         ▼
ViewSchemaRenderer
         │
         ▼
Qt Widgets
```

### Next Phase
- **Commit 10**：UI Extension Registry（只建立扩展契约，不实现 Layout Persistence）。

---

## v6.12.0-beta.2 (2026-07-10) — ViewSchema 布局协议层

> **里程碑语义**：Commit 8.5 在 PresentationModel 与 Qt Renderer 之间增加 ViewSchema 布局协议层。ViewSchema 不依赖 Qt，只描述「Module 的 PresentationModel 应该如何摆放在 Workbench 的 Toolbar / Inspector / StatusBar / Workspace / Dock 中」。至此，Workbench 形成完整数据驱动链：`Metadata → PresentationModel → ViewSchema → Qt Renderer`。新增一个 Agent（如律师 AI、Trading Agent）只需注册 Metadata、配置 view_schema_id，Qt 自动渲染导航、工具栏、工作区、属性面板，无需再写 `if module.id == ...`。

### Added
- `agent_workbench/ui/workbench/view_schema.py`：定义 ViewSchema 协议层，包括 `ToolbarSchema`（支持扁平/分组）、`InspectorSchema`（Tab 布局 + category 过滤）、`StatusSchema`、`DockSchema`、`WorkspaceSchema`、`ViewSchema`。
- `agent_workbench/ui/workbench/view_schema_registry.py`：注册 7 个默认布局协议：`chat_workspace`、`settings_workspace`、`trace_workspace`、`config_workspace`、`skill_workspace`、`tool_workspace`、`generic_workspace`；支持按 `view_schema_id` 或 `type` 解析。
- `agent_workbench/ui/workbench/view_schema_renderer.py`：Qt 渲染器，将 `ViewSchema + ModulePresentation` 应用到 `ToolBar / StatusBar / Inspector / Workspace`。
- `agent_workbench/ui/workbench/generic_workspace.py`：新增 GenericWorkspaceItem，作为无专属 Workspace 的默认视图。
- `ModulePresentation.view_schema_id`：MetadataAdapter 自动推断默认值，Metadata 可显式覆盖。
- `tests/ui/test_view_schema.py`：13 个非 GUI 单元测试，覆盖 Registry 解析、Renderer Toolbar/StatusBar/Inspector/Workspace 驱动、MetadataAdapter view_schema_id 推断。

### Changed
- `agent_workbench/ui/workbench/inspector.py`：支持 Schema 驱动的 Tab 模式；无 Schema 时保持原有平铺模式，向后兼容。
- `agent_workbench/ui/workbench/status_bar.py`：改为纯 `set_statistics(statistics)` 接口，彻底移除 Runtime 字段硬编码。
- `agent_workbench/ui/workbench/tool_bar.py` + `tool_bar_host.py`：新增 ToolBar，按 ActionPresentation 动态生成按钮，支持分组与 danger 样式。
- `agent_workbench/ui/workbench/workbench.py`：将 ToolBarHost 纳入 Workbench 骨架。
- `agent_workbench/ui/workbench_ui_controller.py`：
  - `_on_selection_changed()` 改为通过 `ViewSchemaRenderer` 统一驱动所有 UI Host。
  - 新增 `_runtime_status()` 提供 Runtime 核心状态给 Renderer。
  - `_refresh_status_bar()` 使用 `generic_workspace` Schema 渲染全局状态。
- `docs/v6/v6.12-task-list.md`：新增 Commit 8.5（ViewSchema 布局协议层）并勾选所有任务。

### Tests
- `pytest tests/`：**726/726 passed**（新增 13 个 ViewSchema 测试；收尾 Qt 退出码 `3221226505` 为 Windows 已知现象，不影响断言结果）。

### Architecture
```text
Metadata
    ↓
PresentationModel
    ↓
ViewSchema（怎么摆）
    ↓
Qt Renderer（具体实现）
```

### Next Phase
- **Commit 9**：Task 闭环（User → Manager → Planning → Capability → Provider → Streaming → Task → Trace → History）。

---

## v6.12.0-beta.1 (2026-07-10) — StatusBar + ToolBar + Workspace 聚合 PresentationModel

> **里程碑语义**：Commit 8 完成 Metadata → PresentationModel → Workbench UI 数据流的最后一段。StatusBar 不再直接读取 Runtime，改为聚合所有 ModulePresentation.statistics；ToolBar 根据当前选中 ModulePresentation.actions 动态生成快捷按钮；Workspace 根据 Presentation 类型自动切换（chat / trace / generic），移除硬编码模块 ID 分支。至此，Workbench 所有主 Host（Navigator / Inspector / StatusBar / ToolBar / Workspace）都只消费 PresentationModel，UI 与 Runtime 的解耦达到稳定状态。

### Added
- `agent_workbench/ui/workbench/tool_bar.py` + `tool_bar_host.py`：新增 ToolBar，根据 `ActionPresentation` 列表动态生成按钮，支持 `enabled` / `danger` / `order`，并通过 `action_triggered` 信号复用 Inspector Action 处理通道。
- `agent_workbench/ui/workbench/generic_workspace.py`：新增 GenericWorkspaceItem，作为无专属 Workspace 的选中项的默认视图。
- `agent_workbench/ui/workbench/status_bar.py`：新增 `set_statistics(statistics)`，从 `StatisticPresentation` 列表动态重建状态项，支持 `bytes` / `percent` / `duration` 格式化。
- `tests/ui/test_status_bar_presentation.py`：13 个非 GUI 单元测试，覆盖 StatusBar 统计聚合、ToolBar 按钮渲染与信号、Workspace ID 解析、GenericWorkspace 内容更新。

### Changed
- `agent_workbench/ui/workbench/status_bar_host.py`：精简为 `set_statistics()` 单一入口，移除对 Runtime 具体字段的依赖。
- `agent_workbench/ui/workbench/workbench.py`：新增 ToolBarHost 到 Workbench 骨架，并转发 `tool_bar_action_triggered` 信号。
- `agent_workbench/ui/workbench_ui_controller.py`：
  - `_refresh_status_bar()` 改为聚合 `_build_navigator_presentations()` 中所有 ModulePresentation 的 statistics。
  - `_on_selection_changed()` 同步更新 Inspector、ToolBar 与 Workspace。
  - 新增 `_resolve_workspace_id()` 与 `_switch_workspace()`，根据 Presentation.type 自动映射 Workspace，移除硬编码分支。
- `docs/v6/v6.12-task-list.md`：Commit 8 阶段标记为 `v6.12.0-beta.1` 并勾选所有任务。

### Tests
- `pytest tests/`：**713/713 passed**（新增 13 个 StatusBar / ToolBar / Workspace Presentation 测试；收尾 Qt 退出码 `3221226505` 为 Windows 已知现象，不影响断言结果）。

### Next Phase
- **Commit 9**：Task 闭环（User → Manager → Planning → Capability → Provider → Streaming → Task → Trace → History）。

---

## v6.12.0-alpha.3 (2026-07-09) — Navigator + Inspector 读取 PresentationModel

> **里程碑语义**：Commit 6 完成了 `MetadataDefinition → PresentationModel` 的映射；Commit 7 让 Navigator 与 Inspector 真正消费 PresentationModel，移除 Workbench 左侧导航与右侧属性检查器的硬编码。现在，新增一个 Runtime Module 或 Settings 分类后，Workbench 启动即可在 Navigator 看到，Inspector 会自动按 category 分组、识别敏感字段与只读字段、禁用不可用的 Action。UI 与 Runtime 的解耦进入可运行阶段。

### Added
- `agent_workbench/ui/workbench/navigator.py`：
  - 新增 `load_presentations(presentations)`，从 `list[ModulePresentation]` 重建导航。
  - 新增 `_is_settings_presentation()`，按 `category == "settings"` 或 `type == "settings"` 将 PresentationModel 分到 Settings 区（带 "+" 按钮），其余分到顶部功能 Tab 区。
- `agent_workbench/ui/workbench/navigator_host.py`：新增 `load_presentations()` 代理方法。
- `agent_workbench/ui/workbench/inspector.py`：
  - Properties 按 `category` 分组渲染，空 category 归入 `General`。
  - `sensitive=True` 的 Property 统一使用密码输入框（`QLineEdit.EchoMode.Password`）。
  - `editable=False` 的 Property 统一禁用编辑并应用只读样式（string / textarea / select / boolean 均生效）。
  - Actions 根据 `enabled` 禁用/启用按钮。
- `tests/ui/test_navigator_inspector_presentation.py`：14 个非 GUI 单元测试，覆盖 Navigator 分组、选择、"+" 按钮，以及 Inspector 分类分组、password、readonly、boolean/select/textarea/action enabled 等。

### Changed
- `agent_workbench/ui/workbench_ui_controller.py`：
  - `_refresh_navigator()` 改为调用 `_build_navigator_presentations()` 构造 `list[ModulePresentation]`，再调用 `Navigator.load_presentations()`，移除 Navigator 中的硬编码 tab 注册。
  - 功能 Workspace（Chat / Skills / Tools）与 Settings 分类统一以 ModulePresentation 表达。
- `docs/v6/v6.12-task-list.md`：Commit 7 阶段标记为 `v6.12.0-alpha.3` 并勾选所有任务。

### Tests
- `pytest tests/`：**700/700 passed**（新增 14 个 Navigator / Inspector PresentationModel 测试；收尾 Qt 退出码 `3221226505` 为 Windows 已知现象，不影响断言结果）。

### Next Phase
- **Commit 8**：StatusBar + ToolBar + Workspace 通过 `PresentationModel` 聚合（v6.12.0-beta.1）。
- **Commit 9**：Task 闭环（User → Manager → Planning → Capability → Provider → Streaming → Task → Trace → History）。

---

## v6.12.0-alpha.2 (2026-07-09) — Conversation 自动标题

> **里程碑语义**：会话标题被正式纳入 Conversation Domain，UI 只读取 `conversation.title`。新会话默认显示 `New Conversation`，第一轮 Assistant 回复完成后自动根据首条用户消息生成标题；手动重命名后自动标题不再覆盖。该功能作为 Commit 6 的附属小功能，验证了「Domain 持有唯一真相」的架构原则，并为后续 summary / 标签 / 搜索索引 / 长期记忆扩展打下基础。

### Added
- `agent_workbench/conversation/` Domain 层：
  - `title_generator.py`：定义 `TitleGenerator` Protocol 与 `AbstractTitleGenerator`，提供 `RuleTitleGenerator`（基于首条用户消息截断生成标题）。
  - `title_service.py`：`ConversationTitleService` 负责生成标题并在标题为空时自动更新会话。
  - `conversation_service.py`：`ConversationService` 统一封装 Session / Chat / Title 生命周期，提供 `create_conversation`、`store_user_message`、`store_assistant_message`、`rename_conversation`、`load_messages` 等语义化 API。
- `agent_workbench/ui/workbench_ui_controller.py`：
  - 集成 `ConversationService`。
  - 新建会话时创建空标题会话，标题栏与左侧列表显示 `New Conversation`。
  - Assistant 第一轮回复完成后自动触发标题生成，并刷新会话列表与标题栏。
  - 覆盖 `_load_session_view()`，空标题时显示默认占位。
- `v6/ui/session_item.py`：空标题会话在左侧列表显示 `New Conversation`。
- `tests/conversation/test_title_generator.py`：7 个规则标题生成测试。
- `tests/conversation/test_conversation_service.py`：10 个 ConversationService 生命周期与自动标题测试。

### Changed
- `docs/v6/v6.12-task-list.md`：Conversation 自动标题阶段标记为 `v6.12.0-alpha.2`。

### Tests
- `pytest tests/`：**686/686 passed**（新增 17 个 Conversation 测试；收尾 Qt 退出码 `3221226505` 为 Windows 已知现象，不影响断言结果）。

---

## v6.12.0-alpha.1 (2026-07-09) — Metadata → PresentationModel 完整映射

> **里程碑语义**：v6.11 完成了 Metadata Contract 与 Provider Registry；v6.12 开始让 UI 真正独立于 Runtime。本次提交完整打通 `MetadataDefinition → PresentationModel → Qt` 的第一段：Adapter 现在能无损失地转换 Capability Metadata、Resource Metadata 以及旧版 Legacy Metadata，并为 PresentationModel 补齐所有常用字段。同时，`PROJECT_BLUEPRINT.md` 正式宣布 Metadata Contract 长期冻结（Additive Only），为 v6.12 及以后的 UI / CLI / Remote / Plugin 扩展提供稳定契约基础。

### Added
- `agent_workbench/ui/workbench/presentation.py`：
  - `PropertyPresentation` 扩展 `default_value`、`category`、`sensitive`、`placeholder`、`required`。
  - `StatisticPresentation` 扩展 `unit`、`timestamp`。
  - `ActionPresentation` 扩展 `enabled`、`order`、`danger`。
  - `ModulePresentation` 扩展 `tags`、`enabled`、`order`、`category`、`children`、`connection`，可同时表达 Capability Module 与 Resource。
- `agent_workbench/ui/workbench/metadata_adapter.py`：
  - 新增 `PresentationMetadataAdapter` 类，显式实现 `agent_workbench.metadata.adapter.MetadataAdapter` Protocol。
  - 新增 `adapt_resource()`，将 `ResourceDefinition` 转换为 `ModulePresentation`。
  - 完整保留 `MetadataDefinition`、`ResourceDefinition` 以及 Legacy `ModuleMetadata` / `PropertyMetadata` / `StatisticMetadata` / `ActionMetadata` 的映射。
- `docs/v6/v6.12-task-list.md`：拆分 Commit 6/7/8，明确 v6.12 主线为 PresentationModel 打通 → Task 闭环 → 真实使用验证 → 后续扩展。
- `tests/ui/test_metadata_presentation.py`：覆盖 Capability、Resource、Legacy 映射与 Protocol 合规性。

### Changed
- `agent_workbench/ui/workbench/__init__.py`：导出 `PresentationMetadataAdapter`，并保留 `MetadataAdapter` 向后兼容别名。
- `agent_workbench/ui/workbench_ui_controller.py`：使用 `PresentationMetadataAdapter` 替换旧的 `MetadataAdapter`。
- `PROJECT_BLUEPRINT.md`：新增「Metadata Contract 长期冻结（v6.11.0-beta.4 起）」小节，规定只允许 Additive Change，禁止 Breaking Change。
- `docs/v6/v6.11-task-list.md`：原 Commit 6 拆分为 6/7/8，并链接到新的 v6.12 任务清单。

### Tests
- `pytest tests/`：**669/669 passed**（新增 7 个 PresentationModel 映射测试；收尾 QApplication 销毁阶段出现 Windows 已知退出码 `3221226505`，不影响断言结果）。

### Next Phase
- **Commit 7**：Navigator + Inspector 全面读取 `PresentationModel`。
- **Commit 8**：StatusBar + ToolBar + Workspace 通过 `PresentationModel` 聚合。
- **Commit 9**：Task 闭环（User → Manager → Planning → Capability → Provider → Streaming → Task → Trace → History）。

---

## v6.11.0-beta.4 (2026-07-09) — Provider Registry + 多模型接入

> **里程碑语义**：在 OpenAI 跑通后，引入 `ProviderRegistry` 统一注册与发现模型 Provider；新增 Claude / Gemini / Kimi / Qwen / DeepSeek 五个 OpenAI 兼容 Provider，均通过统一 `ModelProvider` 协议接入 `ModelModule`。`AddProviderDialog` 从 `ModelModule` 动态读取可用 Provider 类型，Workbench 用户可在 UI 中按需配置并切换不同云模型，无需修改源码。

### Added
- 新增 `agent_workbench/runtime/provider_registry.py`：
  - `ProviderRegistry.register(provider_class)` / `get(name)` / `has(name)` / `list_names()` / `list_providers()`。
  - `create_default_provider_registry()` 注册所有内置 Provider（echo / openai / claude / gemini / kimi / qwen / deepseek）。
  - 每个已注册 Provider 返回平台无关的 `MetadataDefinition`，供 UI 与外部系统消费。
- 新增 OpenAI 兼容 Provider 实现：
  - `agent_workbench/services/claude_provider.py` — 默认 `https://api.anthropic.com/v1`。
  - `agent_workbench/services/gemini_provider.py` — 默认 `https://generativelanguage.googleapis.com/v1beta/openai`。
  - `agent_workbench/services/kimi_provider.py` — 默认 `https://api.moonshot.cn/v1`。
  - `agent_workbench/services/qwen_provider.py` — 默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`。
  - `agent_workbench/services/deepseek_provider.py` — 默认 `https://api.deepseek.com/v1`。
- 新增 `tests/runtime/test_provider_registry.py`：覆盖默认注册表包含全部 7 个 Provider、`get` 实例化、`has` 查询、`list_providers` 返回 Metadata、`ModelModule.provider_types()` 暴露注册表类型。

### Changed
- `agent_workbench/runtime/modules/model_module.py`：
  - 使用 `create_default_provider_registry()` 替代硬编码的 `EchoProvider / OpenAIProvider` 分支。
  - 新增 `provider_types()`，暴露注册表中所有支持的 Provider 类型名称。
- `agent_workbench/ui/dialogs/add_provider_dialog.py`：构造函数新增 `provider_types` 参数，下拉框动态填充可用类型。
- `agent_workbench/ui/workbench_ui_controller.py`：
  - 新增 `_provider_types()`，从 `ModelModule` 注册表读取可用 Provider 类型。
  - `AddProviderDialog` 工厂改为传入 `provider_types=self._provider_types()`，并将父窗口修正为 `WorkbenchHost`。

### Tests
- `pytest tests/`：**662/662 passed**（新增 14 个 Provider Registry / UI 集成测试；收尾 QApplication 销毁阶段出现 Windows 已知退出码 `3221226505`，不影响断言结果）。

### Next Phase
- **Commit 6**：Workbench UI 去硬编码（MetadataAdapter 完整映射、Navigator / Inspector / StatusBar 通过 PresentationModel 渲染）。

---

## v6.11.0-beta.3 (2026-07-09) — Resource Metadata

> **里程碑语义**：A 线冻结式推进。将 Model / MCP / Skill / Prompt / Memory / Workflow 六个 Runtime Module 的 `metadata()` 统一迁移到 `MetadataDefinition`，使用 `ValueType` 描述属性类型，消除旧 `ModuleMetadata` 在核心资源模块中的使用。新增 `agent_workbench/metadata/resource.py`，定义 `ResourceType`、`ResourceConnection`、`ResourceDefinition`，建立 Resource（System / Python Env / IDE / CLI / Agent CLI）的跨层描述契约，明确 Capability（What I can do）与 Resource（What I can use）的语义边界。

### Added
- 新增 `agent_workbench/metadata/resource.py`：
  - `ResourceType` 枚举：SYSTEM / PYTHON_ENV / IDE / CLI / AGENT_CLI。
  - `ResourceConnection`：描述 Resource 的连接或定位信息（target / command / args / env / working_dir）。
  - `ResourceDefinition`：Resource 的静态描述，复用 `MetadataProperty` / `MetadataStatistics` / `MetadataAction` 原语。
- 新增 `tests/runtime/modules/test_module_metadata.py`：覆盖 Model / MCP / Skill / Prompt / Memory / Workflow 六个模块的 `MetadataDefinition` 返回类型、属性类型、统计字段、操作字段，以及 Resource Metadata 基础创建。

### Changed
- `agent_workbench/runtime/modules/model_module.py`：`metadata()` 返回 `MetadataDefinition`；属性使用 `ValueType.ENUM / FLOAT / INT`。
- `agent_workbench/runtime/modules/mcp_module.py`：`metadata()` 返回 `MetadataDefinition`；`servers` 属性使用 `ValueType.LIST`。
- `agent_workbench/runtime/modules/skill_module.py`：`metadata()` 返回 `MetadataDefinition`；`registry` 属性使用 `ValueType.LIST`。
- `agent_workbench/runtime/modules/prompt_module.py`：`metadata()` 返回 `MetadataDefinition`；`renderer` 属性使用 `ValueType.ENUM`。
- `agent_workbench/runtime/modules/memory_module.py`：`metadata()` 返回 `MetadataDefinition`；属性使用 `ValueType.BOOL / ENUM / PATH / INT`。
- `agent_workbench/runtime/modules/workflow_module.py`：`metadata()` 返回 `MetadataDefinition`；`templates` 属性使用 `ValueType.LIST`。
- `agent_workbench/metadata/__init__.py`：导出 `ResourceDefinition`、`ResourceConnection`、`ResourceType`。

### Tests
- `pytest tests/`：**648/648 passed**（新增 8 个模块 Metadata 测试；收尾 QApplication 销毁阶段出现 Windows 已知退出码 `3221226505`，不影响断言结果）。

### Next Phase
- **Commit 5**：Provider Registry + 多模型接入（OpenAI / Claude / Gemini / Kimi / Qwen / DeepSeek）。

---

## v6.11.0-beta.2 (2026-07-09) — Streaming UI 对话闭环

> **里程碑语义**：第一条真实 LLM 链路升级为流式输出，Workbench Chat Workspace 可实时显示 Token；修复流式输出结束后重复生成完整 AI 消息的问题，建立 `AI_CHUNK → sign_stream_chunk`、`AI_END / ENGINE_FAILED → sign_stream_end` 的确定性事件映射。新增 `tests/ui/test_streaming_chat_loop.py` 覆盖流式事件映射、非流式路径回退、错误状态唯一传播。

### Added
- 新增 `tests/ui/test_streaming_chat_loop.py`：
  - `test_streaming_path_does_not_duplicate_ai_message`：验证流式路径下 `AI_CHUNK` 实时显示、结束时不会重复追加完整 AI 消息。
  - `test_streaming_error_finally_emits_once`：验证 `ENGINE_FAILED` 错误只传播一次，不会同时触发 `sign_chat_ai` 与 `sign_stream_end` 重复错误。
  - `test_non_streaming_path_emits_ai_message`：验证非流式路径仍正常显示完整 AI 回复。

### Changed
- `agent_workbench/ui/workbench_ui_controller.py`：
  - 新增 `_finalize_stream(error)` 方法，使用锁与 `_stream_finalized` 标志原子化结束流式输出，确保 `sign_stream_end` 与 `sign_set_streaming(False)` 只发射一次。
  - `_on_ai_end()` 与 `_on_engine_failed()` 统一调用 `_finalize_stream()`。
  - `on_send_msg()` 中设置 `_stream_finalized = False`，`_run()` 线程统一通过 `finally` 调用 `_finalize_stream(error_message)`。
  - 非流式路径在流式未结束时才发射完整 `sign_chat_ai`，避免与流式片段重复。

### Tests
- `pytest tests/`：**640/640 passed**（新增 3 个 Streaming UI 测试；收尾 QApplication 销毁阶段出现 Windows 已知退出码 `3221226505`，不影响断言结果）。

### Next Phase
- **Commit 4**：Resource Metadata（Prompt / Skill / MCP Metadata）。

---

## v6.11.0-beta.1 (2026-07-09) — First Real LLM Link

> **里程碑语义**：打通第一条真实 LLM 链路，Workbench 从架构进入产品阶段。ManagerAI 将普通聊天请求（`GENERAL_QUERY`）从 `CHAT` 改为 `ACTION`，经 Decision Layer 路由到 `chat` Capability；`CapabilityResolver` 支持 `GENERAL_QUERY → chat` 并生成 `engine_capability=text_generation` 的能力链；`OpenAIProvider` 通过 `ModelModule` 接入 Runtime，非流式调用 `chat.completions.create`。新增 `tests/integration/test_openai_chat_loop.py` 非 GUI 集成测试：使用 mock HTTP 验证完整请求/响应格式、api_key 不随响应或 Trace 泄露、Provider 错误可传播为任务 FAILED。

### Added
- 新增 `tests/integration/test_openai_chat_loop.py`：
  - `test_openai_chat_loop_returns_mocked_response`：验证 `User → Controller → Manager AI → Capability → OpenAI Provider → LLM → Response → UI` 完整闭环。
  - `test_openai_chat_loop_does_not_leak_api_key`：验证响应与 Trace 中均不包含 `api_key`。
  - `test_openai_provider_error_propagates_as_failed`：验证 Provider 异常使任务进入 `FAILED` 且不泄露 api_key。

### Changed
- `agent_workbench/runtime/decision/manager_ai.py`：默认请求路由从 `CHAT` 改为 `ACTION` + `general_query`，使普通聊天进入 Runtime 并调用真实 Provider。
- `agent_workbench/runtime/decision/resolver.py`：`CapabilityResolver._map_intent_to_capability()` 新增 `IntentType.GENERAL_QUERY → chat` 映射。
- `tests/v6/runtime/test_decision_layer.py`：原 `test_chat_does_not_enter_runtime` 更新为 `test_general_query_enters_runtime_via_chat_capability`，匹配新路由行为。
- `tests/test_controller_interaction.py`：`test_controller_chat_still_works_for_chat_mode` 更新为 `test_controller_chat_routes_general_query_to_chat_capability`，断言 `action/general_query/chat capability_chain`。

### Tests
- `pytest tests/`：**632/632 passed**（新增 3 个 OpenAI 集成测试；收尾 QApplication 销毁阶段出现 Windows 已知退出码 `3221226505`，不影响断言结果）。

### Next Phase
- **B 线 Commit 2**：`OpenAIProvider` Streaming 输出 + Workbench Chat Workspace 实时显示 Token + Trace 记录完整请求/响应统计。

---

## v6.11.0-alpha.3 (2026-07-09) — B-line Pivot: OpenAI Provider First

> **里程碑语义**：响应用户方向确认，v6.11 正式拆分 A/B 两条线并明确时序原则：B 线（产品线）优先推进单一真实 LLM 对话闭环，A 线（架构线）在 Metadata Contract 已冻结基础上冻结式推进。`docs/v6/ROADMAP.md` 与 `docs/v6/v6.11-task-list.md` 重新排序，将 OpenAI Provider 非流式对话闭环列为 v6.11.0-beta.1 唯一目标；明确延后 MCP、Workflow、Memory、Tool Calling、多模型等扩展，直到第一条真实链路跑通。

### Changed
- 更新 [docs/v6/ROADMAP.md](docs/v6/ROADMAP.md)：新增「真实 LLM 对话闭环」阶段，拆分 B 线（产品线）与 A 线（架构线）并标明优先级；OpenAI Provider 成为 v6.11.0-beta.1 单一目标。
- 更新 [docs/v6/v6.11-task-list.md](docs/v6/v6.11-task-list.md)：Commit 2 改为 OpenAI Provider — First Real LLM Link，Commit 3 改为 Streaming UI 对话闭环，A 线任务标记为冻结式推进。

### Next Phase
- **B 线 Commit 1**：实现 `OpenAIProvider` 单 Provider 非流式调用，打通 `User → Workbench UI → Manager AI → Capability → OpenAI Provider → LLM → Response → UI`。

---

## v6.11.0-alpha.2 (2026-07-09) — Metadata Contract Frozen

> **里程碑语义**：Metadata Cross-layer Contract 首次落地实现。`agent_workbench/metadata/` 目录结构一次性冻结：`types.py`、`errors.py`、`model.py`、`registry.py`、`adapter.py`。定义 `MetadataDefinition`、`MetadataProperty`、`MetadataAction`、`MetadataStatistics` 四个核心对象；`MetadataRegistry` 提供 `register()` / `get()` / `all()`；`MetadataAdapter` 协议就位。`BaseRuntimeModule.metadata()` 返回类型迁移为 `MetadataDefinition`。旧 `agent_workbench/runtime/metadata.py` 保留为兼容层，现有 Runtime 模块可逐步迁移。ROADMAP 正式拆分 A 线（架构）与 B 线（产品）：Commit 1 完成后立即启动单一真实 LLM 接入与对话体验验证。

### Added
- 新增 `agent_workbench/metadata/` 跨层契约包：
  - `types.py`：`ValueType`、`MetadataType` 枚举与兼容别名。
  - `errors.py`：`MetadataError`、`MetadataValidationError`、`MetadataNotFoundError`、`MetadataAdapterError`。
  - `model.py`：`MetadataDefinition`、`MetadataProperty`、`MetadataAction`、`MetadataStatistics`。
  - `registry.py`：`MetadataRegistry`（`register` / `get` / `require` / `all` / `unregister` / `clear`）。
  - `adapter.py`：`MetadataAdapter` Protocol 与 `IdentityMetadataAdapter`。
- 新增 `tests/metadata/` 非 GUI 测试：model、registry、adapter 全覆盖。

### Changed
- `BaseRuntimeModule.metadata()` 返回类型从 `ModuleMetadata` 更新为 `MetadataDefinition`。
- `agent_workbench/runtime/metadata.py` 改为兼容层：保留旧类，并重新导出新的 `MetadataDefinition` 等类。
- `agent_workbench/ui/workbench/metadata_adapter.py` 同时兼容新旧 Metadata，支持逐步迁移。
- `WorkbenchController.get_module_metadata()` 与 `AgentRuntime.get_module_metadata()` 返回类型更新为 `MetadataDefinition | None`。
- 更新 [PROJECT_BLUEPRINT.md](PROJECT_BLUEPRINT.md)：
  - 增加 **Description-Driven Development** 小节：新增能力标准顺序 `Identity → Metadata → Schema → Runtime → Execution`。
  - 增加 **Capability vs Resource** 对照表：明确 Capability 是 "What I can do"，Resource 是 "What I can use"。
  - 强化 Metadata 铁律：依赖方向只能是 `Runtime → Metadata`，绝不能反向。
- 更新 [docs/v6/v6.11-task-list.md](docs/v6/v6.11-task-list.md)：Commit 1 明确冻结 `agent_workbench/metadata/` 目录与四个核心对象，Registry 与 Adapter 现在就位。
- 更新 [docs/v6/ROADMAP.md](docs/v6/ROADMAP.md)：拆分 A 线（Metadata / Schema / Resource / Plugin）与 B 线（单一真实 LLM / Streaming / 对话体验 / Provider 扩展）。

### Tests
- `pytest tests/`：**629/629 passed**（新增 15 个 Metadata 包测试；收尾 QApplication 销毁阶段出现 Windows 已知退出码 `3221226505`，不影响断言结果）。

### Next Phase
- **A 线 Commit 2**：实现 `MetadataAdapter` 到 `ModulePresentation` 的完整映射，补齐 Runtime 模块 Metadata。
- **B 线 Commit 1**：接入单一真实 LLM（OpenAIProvider），打通 `User → Workbench → Manager → Capability → Provider → LLM → UI` 非流式对话闭环。

---

## v6.11.0-alpha.1 (2026-07-09) — Workbench-First Doctrine & Resource Layer Design

> **里程碑语义**：v6.11 战略转向落地。Runtime 被正式定位为稳定基础设施，Workbench Layer 成为后续主要演进目标；Metadata 被定义为跨层契约（Cross-layer Contract），不隶属于 Runtime 或 UI；Resource Layer 设计完成，将 System / Python Env / IDE / CLI / Agent CLI 与 Capability 分离，形成 `Digital Identity → Capability → Resource → Provider → Target` 的完整执行链。

### Added
- 新增 `docs/v6/resource-layer-spec.md`：Resource Layer 规范，定义 System / Python Env / IDE / CLI / Agent CLI 五层资源及其与 Capability / Provider / Target 的关系。
- 在 [PROJECT_BLUEPRINT.md](PROJECT_BLUEPRINT.md) 顶部增加 **Workbench-First Doctrine**：自 v6.11 起 Runtime 视为稳定基础设施，Workbench Layer 成为产品长期演进方向。
- 在 [PROJECT_BLUEPRINT.md](PROJECT_BLUEPRINT.md) 增加 **Cross-Layer Contract — Metadata First** 章节：明确 Metadata 不属于任何单一 Layer，Runtime 与 Workbench 仅共同遵守契约。

### Changed
- 更新 [docs/v6/v6.11-task-list.md](docs/v6/v6.11-task-list.md)：Metadata 目录从 `agent_workbench/runtime/metadata/` 调整为 `agent_workbench/metadata/`，adapter 由 Metadata 契约拥有。
- 更新 [docs/v6/data-layer-inventory.md](docs/v6/data-layer-inventory.md)：反映 Metadata / Presentation / Schema / Registry 的新路径与职责。
- 更新 [docs/v6/repository-map.md](docs/v6/repository-map.md)：增加 `agent_workbench/metadata/` 与 `resource-layer-spec.md`。
- 更新 [docs/v6/runtime-kernel-spec.md](docs/v6/runtime-kernel-spec.md)：明确 Metadata 为 Cross-layer Contract，增加 Runtime Kernel ↔ Metadata Contract ↔ Workbench Layer 关系图。
- 更新 [docs/v6/runtime-glossary.md](docs/v6/runtime-glossary.md)：增加 **Resource**、**Target**、调整 **Metadata** / **Schema** / **PresentationModel** / **Plugin** 定义。
- 更新 [docs/v6/ROADMAP.md](docs/v6/ROADMAP.md)：增加 Resource Layer 梯队与预告，调整未来阶段优先级。

### Tests
- `pytest tests/`：**614/614 passed**（收尾 QApplication 销毁阶段出现 Windows 已知退出码 `3221226505`，不影响断言结果）。

### Next Phase
- 继续执行 [docs/v6/v6.11-task-list.md](docs/v6/v6.11-task-list.md)：在 `agent_workbench/metadata/model.py` 中实现 `ModuleMetadata` / `PropertyMetadata` / `StatisticMetadata` / `ActionMetadata` 跨层契约。

---

## v6.10.0-alpha (2026-07-09) — Configuration-Driven Workbench Loop

> **里程碑语义**：v6.10 以「打通完整配置闭环」为第一站。以 Provider 为样板，将 No-Code Registration Principle 扩展到 MCP、Skill、Workflow、Prompt、Memory：用户通过 Workbench UI 点击「+」即可注册扩展对象，ConfigStore 持久化后对应 Registry 自动 Reload，Navigator 与 StatusBar 实时刷新，Agent 立即可见新配置。这一闭环标志着 Agent Workbench 开始具备真正的平台特征：统一的配置注册、持久化、通知与刷新链路，不再依赖为每个对象单独编写的 UI 和配置流程。

### Added
- 新增 `agent_workbench/ui/dialogs/base.py`：`AddConfigItemDialog` 基类，统一新增配置项对话框的布局、主题样式与 `result()` 契约。
- 新增 `agent_workbench/ui/dialogs/add_mcp_dialog.py`：`AddMcpDialog` 用于新增 MCP Server（name / command / args / env / enabled）。
- 新增 `agent_workbench/ui/dialogs/add_skill_dialog.py`：`AddSkillDialog` 用于新增 Skill（name / type / source / description / enabled）。
- 新增 `agent_workbench/ui/dialogs/add_workflow_dialog.py`：`AddWorkflowDialog` 用于新增 Workflow 模板（name / description / steps / enabled）。
- 新增 `agent_workbench/ui/dialogs/add_prompt_dialog.py`：`AddPromptDialog` 用于新增 Prompt 模板（name / description / template / enabled）。
- 新增 `agent_workbench/ui/dialogs/add_memory_dialog.py`：`AddMemoryDialog` 用于新增 Memory Store（name / provider / path / enabled）。
- 新增 `agent_workbench/runtime/modules/mcp_module.py`：`McpModule` 读取 `mcp.servers` 配置并暴露 Metadata。
- 新增 `agent_workbench/runtime/modules/skill_module.py`：`SkillModule` 读取 `skill.registry` 配置并维护 Skill 索引。
- 新增 `agent_workbench/runtime/modules/workflow_module.py`：`WorkflowModule` 读取 `workflow.templates` 配置并维护模板索引。
- 扩展 `tests/ui/test_provider_config_loop.py`：新增 MCP / Skill / Workflow / Prompt / Memory 对话框与 `_on_add_requested` 追加测试。

### Changed
- 重构 `agent_workbench/ui/dialogs/add_provider_dialog.py`：继承 `AddConfigItemDialog`，保持原有表单字段与返回契约不变。
- 更新 `agent_workbench/runtime/agent_runtime.py`：在 ModuleRegistry 中注册 `McpModule` / `SkillModule` / `WorkflowModule`。
- 更新 `agent_workbench/runtime/modules/memory_module.py`：`apply_config` 优先读取 `memory.configs` 列表，无列表时回退到传统 `memory` 字典，兼容旧配置。
- 更新 `agent_workbench/ui/workbench_ui_controller.py`：`_register_configuration_categories` 为 MCP / Skill / Workflow / Prompt / Memory 绑定对应新增对话框，修正 `memory` 分类的 `config_path` 为 `memory.configs`。
- 更新 `agent_workbench/runtime/config_store.py`：`_notify` 发出通用 `changed(path, value)` 信号，使 UI 能在任意配置变更时刷新 Navigator / StatusBar。

### Tests
- `pytest tests/ui/test_provider_config_loop.py`：**22/22 passed**。
- `pytest tests/ui/`：**39/39 passed**。
- `pytest tests/`：**614/614 passed**（收尾 QApplication 销毁阶段出现 Windows 已知退出码 `3221226505`，不影响断言结果）。

### Next Phase
- v6.11.x 进入 **Metadata-driven Workbench**：统一 Provider / MCP / Skill / Workflow / Prompt / Memory 的 `metadata()` 契约，为 v6.12.x 的 Schema-driven UI 自动生成奠定基础。项目重心从 Runtime 演进正式转向 Workbench 演进。

---

## v6.9.6-foundation (2026-07-09) — V6 Runtime Foundation Baseline Frozen

> **里程碑语义**：v6.9.x Runtime Kernel Freeze Series 正式收官。Repository Hygiene、Runtime Glossary、Repository Map、Audit / Verify 自动化、环境目录布局全部落地，形成可长期演进的工程基线。从此所有 Provider、MCP、Gateway、Workflow 集成均从该基线出发，不再扩展 Runtime Kernel。

### Frozen
- **Runtime Kernel**：Request → Planning → Task → Capability → Engine → Provider 六层架构与依赖规则冻结。
- **Capability Runtime Contract**：`CapabilityDefinition`、`CapabilityContext`、`CapabilityState`、`CapabilityRegistry` 契约冻结。
- **Interaction Boundary**：`RuntimeRequest` / `InteractionEvent` 协议冻结。
- **Decision Layer Control Plane**：`RuntimeDecision` ABI 冻结。
- **Repository Governance**：Git as Archive、Workspace Contains Only Current Truth、One Asset One Authority、Generated Files Disposable、Repository Self-Explanatory、Environment Directories Are Not Source 六大原则冻结。

### Established
- `docs/v6/runtime-kernel-spec.md` — Runtime Kernel 规范。
- `docs/v6/runtime-glossary.md` — 平台术语表。
- `docs/v6/repository-governance.md` — 仓库治理宪章 + Agent 协作公约 + 环境目录使用约定。
- `docs/v6/repository-map.md` — 仓库地图。
- `scripts/audit_repository.py` — 仓库健康审计。
- `scripts/verify_repository.py` — 提交前验证。
- `scripts/generate_repository_map.py` — 自动地图生成。
- `F:\Agent/` 环境目录布局：`.dist/`、`.resource/`、`.sandbox/`、`.monitor/`、`.workbuddy/`。

### Baseline Tags
- `v6.9.6-hygiene` — Repository Hygiene 完成，V6 Runtime Foundation Baseline 起点。
- `v6.9.6-foundation` — V6 Runtime Foundation Baseline 最终冻结点。

---

## v6.9.4-alpha (2026-07-08) — Runtime Decision Layer

> **里程碑语义**：Runtime 从"有能力"进化为"有控制权"。引入 Runtime Decision Layer 作为 Runtime Kernel Control Plane，将 LLM 降级为 Intent Interpreter；Runtime 通过 Intent → Decision → Route → Capability Chain 控制执行路径，禁止 LLM 直接选择 Tool。Decision Layer 属于 Runtime Kernel 扩展，不是第 11 个 Capability Module，不违反 Feature Freeze。

### Added
- 新增 `agent_workbench/runtime/decision/schema.py`：纯协议层，定义 `RuntimeMode` / `IntentType` / `Intent` / `RuntimeDecision` / `IntentError`，不依赖 capability / planner / service。
- 新增 `agent_workbench/runtime/decision/interpreter.py`：`Interpreter` 负责 LLM Output → Intent，拒绝 tool / function / tool_calls / function_call 等传统 calling 格式。
- 新增 `agent_workbench/runtime/decision/resolver.py`：`CapabilityResolver` 负责 Intent → Capability Chain，确定性查询 `CapabilityRegistry` 并复用 Commit 4 的 leaves() 链生成逻辑。
- 新增 `agent_workbench/runtime/decision/policy.py`：`Policy` / `PolicyResult` 执行前策略接口，第一版默认放行。
- 新增 `agent_workbench/runtime/decision/manager_ai.py`：`ManagerAI` 负责 UserRequest → Intent；当前阶段使用规则映射，未来可替换为 LLM。
- 新增 `agent_workbench/runtime/manager/decision_manager.py`：`DecisionManager` 实现 `Manager` 协议，内部整合 `ManagerAI → Interpreter → Resolver → Policy → RuntimeDecision → Task`。
- 新增 `tests/v6/runtime/test_decision_layer.py`：覆盖 CHAT 不进入 Runtime、ACTION 图片能力、Python 分析链、旧任务兼容、拒绝 Tool Calling 污染等 5 个核心场景。

### Changed
- 升级 `v6/runtime/orchestrator.py`：保留 `execute(task)` 兼容入口，新增 `dispatch(decision)`；CHAT 模式不创建 Task，ACTION 模式生成 Task 并携带 `capability_chain`。
- 升级 `agent_workbench/controller.py`：默认 Manager 切换为 `DecisionManager`；`chat()` 优先通过 Decision Layer 判断模式，CHAT 直接返回完成上下文而不进入 Runtime。
- 升级 `agent_workbench/runtime/capability/graph.py`：默认能力树新增 `image_generation` 叶子能力，engine_capability 为 `image_generation`。
- 升级 `agent_workbench/engines/workbench_llm_engine.py`：`capabilities` 增加 `image_generation`，支持 Decision Layer 路由闭环。
- 升级 `agent_workbench/runtime/capability/__init__.py`：导出 `CapabilityRegistry`。
- 升级 `tests/v6/runtime/test_capability_registry.py`：`assistant` 子节点断言包含 `image_generation`。
- 升级 `tests/v6/runtime/test_orchestrator_chain.py`：显式使用 `ManagerRuntime`，保证 Commit 4 chain 执行测试不受默认 manager 变更影响。

### Constraints
- Decision Layer 属于 Runtime Kernel Control Plane，不是 Capability Module，不违反 10 模块 Feature Freeze。
- `schema.py` 只定义协议对象，禁止反向依赖 capability / planner / service / orchestrator。
- 不修改 PlannerLoop、不接 UI、不增加动态规划、retry、parallel、memory 调度。
- LLM 不能直接选择 Tool；任何 tool/function calling 格式都会被 Interpreter 拒绝。

### Contract Freeze (Post-Commit 5)
- `schema.py` 增加架构注释：明确 `RuntimeDecision` 是 Runtime Control Plane 稳定 ABI，不是 UI Model / API Request Model / Capability Model / Task Model。
- `PROJECT_BLUEPRINT.md` 新增 `Runtime Decision Layer Contract Boundary` 章节，记录冻结对象、依赖方向、禁止模式。
- 新增 `tests/v6/runtime/test_runtime_decision_contract.py`：验证 `RuntimeDecision` 可被 UI / MCP / Local Agent 三类入口共同构造，只携带基础类型，序列化稳定，且能被 `Orchestrator.dispatch` 接受。

### Tests
- `pytest tests/v6/runtime`：**63/63 passed**（含 Contract Freeze 新增 6 个测试）。
- `pytest`：**520/520 passed**。

## v6.9.6-alpha (2026-07-09) — Capability Runtime Contract Freeze

> **里程碑语义**：不是新增业务功能，而是冻结 Runtime 对 Capability 的契约。任何未来新增能力（图片、视频、浏览器、MCP、本地 Agent、远程 Agent）都必须通过注册 `CapabilityDefinition` 和实现 `CapabilityContext` 接入，不允许为单个能力增加专用 Runtime 流程。

### Added
- 升级 `agent_workbench/runtime/capability/model.py`：`CapabilityDefinition` 补全静态契约字段 `category` / `summary` / `version` / `provider_type` / `supported_modes` / `priority`，成为 Runtime 对能力的唯一静态描述；新增 `CapabilityCategory` / `CapabilityMode` 枚举。
- 新增 `agent_workbench/runtime/capability/context.py`：定义 `CapabilityContext` 及类型化子上下文 `WorkspaceContext` / `AttachmentContext` / `SelectionContext` / `ExecutionContext`；新增 `CapabilityContextBuilder` Protocol 与 `DefaultCapabilityContextBuilder`，`RuntimeRequest.source` 仅映射为 `CapabilityContext.origin`，不参与 Capability 路由。
- 新增 `agent_workbench/runtime/capability/state.py`：定义 `CapabilityState`（含 `PENDING` / `RESOLVED` / `SCHEDULED` / `RUNNING` / `COMPLETED` / `FAILED` / `CANCELLED` / `TIMEOUT` / `SKIPPED`）与 `CapabilityExecutionState`。
- 升级 `agent_workbench/runtime/capability/graph.py`：在现有 `CapabilityRegistry` 上扩展运行时索引 `state_ref` / `context_ref` / `provider_binding_ref`，提供 `set_state` / `get_state` / `set_context` / `get_context` / `bind_provider` / `get_provider_binding` / `clear_runtime` / `build_context`；Registry 只做索引，不保存执行历史/统计/Trace 等重数据。
- 升级 `agent_workbench/runtime/capability/__init__.py`：导出 Capability Runtime Contract 全部新类型。
- 升级 `agent_workbench/runtime/capability/graph.py` 默认能力树：为 `assistant` / `chat` / `analyze` / `tool` / `coding` / `image_generation` 等节点填充 `category` / `provider_type` / `supported_modes`。
- 新增 `tests/v6/runtime/test_capability_context.py`：8 个测试覆盖子上下文默认、类型化组合、DefaultCapabilityContextBuilder 从 RuntimeRequest / metadata 提取 origin。
- 新增 `tests/v6/runtime/test_capability_state.py`：3 个测试覆盖生命周期枚举与 `CapabilityExecutionState`。
- 新增 `tests/v6/runtime/test_capability_registry_runtime.py`：7 个测试覆盖 Registry 运行时索引与 `build_context`。
- 升级 `tests/v6/runtime/test_capability_model.py` / `test_capability_registry.py`：验证新静态契约字段与默认能力树契约字段。

### Changed
- 更新 `PROJECT_BLUEPRINT.md`：当前任务改为 v6.9.6-alpha Capability Runtime Contract Freeze，新增 V6 Runtime Kernel Freeze Roadmap，真实 LLM 集成整体后移到 v6.10.0-alpha。

### Constraints
- 不新增 `CapabilityDescriptor`，不新增 `CapabilityRuntimeRegistry`；只扩展现有 `CapabilityDefinition` 和 `CapabilityRegistry`。
- `CapabilityDefinition` 保持纯数据，不携带 Runtime 状态。
- Capability Context 必须是类型化子上下文，禁止做成万能 Dict。
- Registry 只保存 State / Context / Provider Binding 的引用/索引。
- `RuntimeRequest.source` 只表示 Origin，不进入 Decision / Capability 路由。
- Runtime 内部禁止出现任何 UI 概念（`QtSelection`、`QtWorkspace` 等）。
- 不接真实 LLM、不改 Orchestrator 执行模型、不做 UI。

### Tests
- `pytest tests/v6/runtime`：**76/76 passed**。
- `pytest`：**575/575 passed**。

### History Note
> **v6.9.x collectively forms the Runtime Kernel Freeze Series.**
>
> The primary objective of this series is to stabilize execution contracts, architectural boundaries, and runtime responsibilities before integrating production Providers, LLMs, MCP, and Workflow Runtime in v6.10 and beyond. Each v6.9.x release freezes one layer of the Runtime Kernel: Task (v6.9.2), Manager / Capability Tree (v6.9.3), Decision Layer (v6.9.4), Interaction Boundary (v6.9.5), and Capability Runtime Contract (v6.9.6).

## v6.9.5-alpha (2026-07-08) — Workbench Interaction Boundary Layer

> **里程碑语义**：Workbench 从 Runtime Owner 进化为 Runtime Client。新增 Interaction Boundary Layer，统一外部入口协议 `RuntimeRequest` 和 UI 事件协议 `InteractionEvent`；任何 UI / MCP / Local Agent / Remote Agent 都可通过同一边界接入 Runtime，而 Runtime 内部无需修改。

### Added
- 新增 `agent_workbench/runtime/interaction/request.py`：外部输入协议 `RuntimeRequest` / `RuntimeRequestSource`，区分 Global Chat 与 Workspace Session，禁止 capability 路由意图。
- 新增 `agent_workbench/runtime/interaction/event.py`：UI 事件协议 `InteractionEvent` / `InteractionEventType`，含 `source` 字段以追踪多入口来源。
- 新增 `agent_workbench/runtime/interaction/mapper.py`：`RuntimeEventMapper` 将 `RuntimeEvent` 翻译为 `InteractionEvent`，不依赖 Renderer。
- 新增 `agent_workbench/runtime/interaction/renderer.py`：`UIEventRenderer` Protocol，消费 `InteractionEvent`。
- 新增 `agent_workbench/runtime/interaction/layer.py`：`WorkbenchInteractionLayer` 作为 UI 与 Runtime 的边界，不持有 `DecisionManager`，只调用 `AgentWorkbenchRuntime.submit_request()`。
- 新增 `tests/interaction/`：16 个测试覆盖 `RuntimeRequest`、`InteractionEvent`、`RuntimeEventMapper`、`WorkbenchInteractionLayer`。
- 新增 `tests/test_controller_interaction.py`：5 个测试覆盖 `WorkbenchController.interaction_layer`、`submit_request`、chat 兼容、显式 tool 请求。

### Changed
- 升级 `agent_workbench/runtime/agent_runtime.py`：内部持有 `DecisionManager`；新增 `submit_request(request: RuntimeRequest) -> str` 作为纯外部入口；新增 `build_chat_context()`；CHAT 模式不创建 Task，只发布 `user_message` 事件。
- 升级 `agent_workbench/runtime/manager/decision_manager.py`：新增 `resolve_from_decision()` 避免重复调用 ManagerAI；识别 UI / CommandBar 显式 tool 请求（非 LLM 选 Tool）；合并 `decision.payload` 到 `Task.payload`。
- 升级 `agent_workbench/controller.py`：拥有 `WorkbenchInteractionLayer`；新增 `submit_request()`；`chat()` / `chat_with_tool()` 包装为 `RuntimeRequest`；保留 `_build_chat_context()` 不提前迁移。
- 升级 `agent_workbench/ui/workbench_ui_controller.py`：暴露 `interaction_layer` 属性，`on_send_msg()` 保持不变。

### Constraints
- `RuntimeRequest` 不允许表达 Capability 路由意图；`action_id` 是用户动作，不是 capability_id。
- `WorkbenchInteractionLayer` 不持有 `DecisionManager`，`DecisionManager` 保持在 Runtime 内部。
- `AgentWorkbenchRuntime.submit_request()` 只作为入口，不增加 session / identity / memory / queue / remote agent 等业务判断。
- CHAT 路径不伪造 `TASK_STARTED` / `TASK_FINISHED`；使用 `MESSAGE_USER` / `MESSAGE_DELTA` / `MESSAGE_COMPLETE` 事件流。
- 不改 Orchestrator、不改 Capability、不改 PlannerLoop、不接 Qt Renderer、不删除旧 `chat()`。

### Reliability Hardening (v6.9.5.1)
- 升级 `agent_workbench/runtime/interaction/layer.py`：新增 `WorkbenchInteractionLayer.close()` 生命周期方法，取消 EventBus 订阅、释放 renderer、清理 task→request 映射。
- 升级 `WorkbenchInteractionLayer.submit_request()`：捕获 Runtime 异常并转换为 `InteractionEventType.ERROR`，避免异常穿透边界影响 UI。
- 升级 `agent_workbench/runtime/interaction/mapper.py`：`payload=None` 时按空 dict 处理；`source` 缺失时回退为 `"unknown"`；未知事件返回 `None`。
- 新增 `tests/interaction/test_request_mapping.py`：完整验证 `request_id` / `source` / `session_id` / `text` / `attachments` / `action_id` / `metadata` / `task_id` 的 RuntimeRequest → UserRequest 映射。

### Tests
- `pytest tests/interaction`：**31/31 passed**。
- `pytest tests/v6/runtime`：**63/63 passed**。
- `pytest`：**556/556 passed**。

## v6.9.3-alpha (2026-07-08) — Multi-Capability Runtime & Manager Routing (Planning Approved)

> **里程碑语义**：Capability 从 metadata 提升为 Runtime 一级公民。单一 Agent 实例进化为能力操作系统：以 `assistant` 为根的能力树（Tree）、`ManagerRuntime` 作为能力路由层、静态 Capability Chain 顺序执行、只读 Runtime UI Bridge。Task 五字段保持不变，所有扩展写入 metadata/payload。不进入 Multi-Agent / Agent Memory / MCP 大规模接入。

### Planned
- 新增 `agent_workbench/runtime/capability/model.py`：`CapabilityDefinition` / `CapabilityPersona` / `CapabilityIntent` / `CapabilityMatch` 运行时模型。
- 新增 `agent_workbench/runtime/capability/graph.py`：`CapabilityRegistry` 能力树，支持 `register / get / lineage / children / roots / find / resolve`。
- 新增 `agent_workbench/runtime/capability/chain.py`：`CapabilityStep` / `CapabilityChain`，静态链序列化工具。
- 新增 `agent_workbench/runtime/manager/runtime.py`：`ManagerRuntime` 默认 Manager，完成 `UserRequest → CapabilityMatch → Task`。
- 新增 `agent_workbench/ui/workbench_runtime_bridge.py`：只读 Runtime → UI 事件桥（后半段，可开关）。
- 新增 Manager 级事件类型：`manager.intent.classified` / `manager.capability.selected` / `manager.chain.step.started` / `capability.chain.step.started`。
- 升级 `agent_workbench/runtime/capability_router.py`：按 `Task.metadata["capability_id"]` 解析 engine_capability。
- 升级 `agent_workbench/runtime/agent_runtime.py`：单例持有 `CapabilityRegistry` 并注入 Manager 与 Router。
- 升级 `agent_workbench/controller.py`：默认注入 `ManagerRuntime`；`AgentManager` 保留为 Legacy Adapter。
- 升级 `v6/runtime/orchestrator.py`：支持 `metadata["capability_chain"]` 静态链顺序执行。

### Constraints
- `CapabilityDefinition` 纯数据，不携带 Runtime 状态。
- `CapabilityRegistry` 由 `AgentWorkbenchRuntime` 单例持有。
- Capability Chain 仅静态链，不根据中间结果动态扩展。
- `ManagerRuntime` 不调用 Engine。
- UI Bridge 第一版只读。
- 能力树根节点为 `assistant`。

### Tests
- 新增 `tests/v6/runtime/test_capability_model.py` / `test_capability_registry.py` / `test_manager.py` / `test_router.py` / `test_capability_chain.py`。
- 目标：全量 260~280 passed。

## v6.9.2-alpha (2026-07-08) — Single Agent Runtime Foundation

> **里程碑语义**：Runtime 从 Chat API 转向 Task API，Workbench UI 从配置工具转向 IDE Host 骨架。Task / UserRequest / Manager / CapabilityRouter / Engine 主链固定；WorkbenchHost → Workbench → NavigatorHost / WorkspaceHost / InspectorHost / StatusBarHost / CommandBarHost 骨架固定。后续新增 Capability 只需扩展 Manager 规则与注册 Engine，无需修改 Runtime 或 Workbench 结构。

### Added
- 新增 `v6/runtime/user_request.py`：`UserRequest` 协议对象，封装 `text / attachments / metadata / session_id / task_id`，作为 Manager 的统一输入。
- 新增 `v6/runtime/manager.py`：`Manager` Protocol，定义 `resolve(UserRequest) -> Task` 接口，支持未来替换为 LLMManager / PolicyManager / HumanApprovalManager。
- 新增 `agent_workbench/services/manager.py`：`AgentManager` 默认实现，当前规则：普通文本 → `chat`，`metadata["task_type"] == "tool"` → `tool`。
- 新增 `agent_workbench/ui/workbench/host_base.py`：`WorkbenchAreaHost` 基类，提供 `mount / replace / dispose` 生命周期。
- 新增 `agent_workbench/ui/workbench/navigator_host.py`：`NavigatorHost`，提供 `register_module / clear_modules / set_selection / modules` 稳定接口。
- 新增 `agent_workbench/ui/workbench/inspector_host.py`：`InspectorHost`，提供 `set_object / clear` 及 `object_id / title` 属性。
- 新增 `agent_workbench/ui/workbench/status_bar_host.py`：`StatusBarHost`，提供 `set_runtime / set_provider / set_model / ... / values()` 稳定接口。
- 新增 `agent_workbench/ui/workbench/command_bar_host.py`：`CommandBarHost`，转发 `command_submitted` 信号并提供 `set_enabled / clear / set_placeholder`。
- 新增 `tests/v6/test_v6_user_request.py`：验证 `UserRequest` 字段与可变默认值隔离。
- 新增 `agent_workbench/tests/test_manager.py`：验证 `AgentManager` 解析 chat/tool 请求、Controller 通过 Manager 提交任务、完整 `UserRequest → Manager → Task → Engine` 主链。

### Changed
- `v6/runtime/task.py`：`Task` 固定为 `id / capability / payload / metadata / created_at` 五个核心字段；保留 `task_id` / `type` 旧别名兼容；`ChatTask` / `AnalyzeTask` 自动推导 capability。
- `v6/runtime/orchestrator.py`：`Orchestrator._ensure_context()` 合并 `Task.metadata` 到 `RuntimeContext.metadata`，保证 Manager 写入的扩展信息流入 Runtime。
- `agent_workbench/controller.py`：`WorkbenchController` 持有 `Manager`；`chat()` / `chat_with_tool()` 改为 `UserRequest → Manager.resolve() → submit_task()`。
- `agent_workbench/runtime/agent_runtime.py`：移除 `chat()`，仅保留 `submit_task()`；Runtime 不再感知 Chat/Prompt 输入形式。
- `agent_workbench/ui/workbench/workbench.py`：五大区域改为 `NavigatorHost / WorkspaceHost / InspectorHost / StatusBarHost / CommandBarHost`。
- `agent_workbench/ui/workbench/__init__.py`：导出 Host 类与基类。
- `agent_workbench/tests/test_agent_workbench.py`：UI 测试调整到 Host 接口层（`navigator.modules()` / `inspector.object_id` / `status_bar.values()`）。

### Tests
- `pytest tests/v6/`：**176/176 passed**。
- `pytest agent_workbench/tests/`：**34/34 passed**。
- 合计：**210/210 passed**。

## v6.9.1-alpha (2026-07-08) — Runtime Observability Foundation

> **里程碑语义**：Runtime 可观测基座成型。Trace 不再是聊天日志，而是结构化执行事件流；事件语义围绕 Task → Capability → Engine → Provider → Execution → Request → Response 分层，避免绑定 LLM Streaming，为未来图片、视频、工作流扩展预留同一套可观测协议。

### Added
- 新增 `agent_workbench/runtime/capability_router.py`：`CapabilityRouter` 作为 Runtime 组件，根据 `Task.capability` 发射 `capability.resolved` 事件。
- 新增 `agent_workbench/ui/workbench/trace_event_registry.py`：`TraceEventRegistry` 提供事件显示元数据（label / icon / level / status），UI 不再硬编码字符串映射。
- 新增 `agent_workbench/ui/workbench/trace_workspace.py`：`TraceWorkspaceItem` 以树形结构实时展示 Trace 事件，支持状态图标与父子层级。
- 新增 `v6/runtime/enums.py` 分层 `TraceEvent` 枚举：Task / Capability / Engine / Provider / Execution / Stream / Request 七层事件，各层通过 `TRACE_EVENT_LEVEL` / `TRACE_EVENT_PARENT_LEVEL` 自动推断 `parent_id`。
- 新增 `tests/v6/test_v6_trace.py::test_trace_scope_is_reserved_interface`：验证 `RuntimeTrace.scope()` 作为 Workflow Runtime 预留接口存在。
- 新增 `agent_workbench/tests/test_agent_workbench.py` 三个 Trace 端到端测试：事件顺序、父子关系、Workspace 接收。

### Changed
- `v6/runtime/event_bus.py`：Trace Hook 改为 `publish` 阶段同步写入，订阅者回调保持异步；保证事件顺序与 `task.finish` 不丢失。
- `v6/runtime/orchestrator.py`：在 `submit()` 中提前注册 Trace Hook；移除 `_on_task_started` 中重复的 `TASK_STARTED` 发布；`_complete_task` / `_fail_task` 先发布最终事件再移除 Hook。
- `v6/runtime/planner_loop.py`：决策事件从 `TASK_STARTED` 改为 `DECISION_PLANNED`，避免混入 Task 生命周期事件。
- `v6/runtime/enums.py`：`REQUEST_SENT` 层级从 `execution` 调整为 `request`（parent = execution），修复 `FIRST_TOKEN` parent 指向问题。
- `agent_workbench/engines/workbench_llm_engine.py`：发射 `EXECUTION_STARTED` / `PROVIDER_SELECTED` / `REQUEST_SENT` / `FIRST_TOKEN` / `CHUNK_RECEIVED` / `STREAM_FINISHED` / `EXECUTION_FINISHED` 结构化事件。
- `agent_workbench/ui/workbench_ui_controller.py`：注册 Trace Workspace，订阅 Runtime 事件并刷新树形 UI。

### Tests
- `pytest tests/v6/`：**176/176 passed**。
- `pytest agent_workbench/tests/`：**20/20 passed**。

## v6.9.0-alpha (2026-07-08) — Agent Workbench Single Instance

> **里程碑语义**：V6 框架内第一个真实 Agent 产品实例落地。
> 本版本在 `v6-agent` 分支基于 `v6.8.0-alpha` Framework Core Foundation Baseline，构建可运行、可配置的单一 Agent Workbench，证明基座可以承载完整 Agent 产品实例。
> 配置/Prompt/Memory 工程先下放到 Agent 层，不引入 Embedding、向量搜索、多 Agent 协作等复杂能力；目标是把所有可调能力统一管理，并通过 UI 配置面板支持 Runtime 热更新。

### Added
- 新增 `agent_workbench/` 应用层目录，作为 V6 第一个真实产品实例：
  - `agent_workbench/app.py`：CLI / GUI 双入口，`--mode cli/gui` 启动。
  - `agent_workbench/controller.py`：`WorkbenchController`，Application Layer 唯一入口，只持有 `AgentWorkbenchRuntime`，不直接持有 Module。
  - `agent_workbench/runtime/agent_runtime.py`：`AgentWorkbenchRuntime`，组合 `ConfigStore` / `ProfileManager` / `ModuleRegistry` / `CoreAgentRuntime`，注册 `WorkbenchLLMEngine` 与 `WorkbenchToolEngine`。
  - `agent_workbench/runtime/config_store.py`：`ConfigStore`，YAML 唯一配置源 + 内存缓存 + 点分路径 get/set/delete + 按 namespace 变更通知。
  - `agent_workbench/runtime/profile_manager.py`：`ProfileManager`，独立管理 Profile 切换 / 导入 / 导出 / 合并，通过 `ConfigStore` 读写。
  - `agent_workbench/runtime/module_registry.py`：`ModuleRegistry`，注册 10 个 `BaseRuntimeModule`，统一调用 `initialize` / `apply_config` / `dispose`。
  - `agent_workbench/runtime/modules/base.py`：`BaseRuntimeModule` 抽象基类，统一生命周期与 `to_form()` UI 表单接口。
  - 10 个 RuntimeModule：
    - `runtime_module.py` —— Agent 生命周期、运行状态、热加载入口。
    - `session_module.py` —— Conversation 状态、History、Context Window。
    - `config_module.py` —— 完整 YAML 配置查看与编辑入口。
    - `profile_module.py` —— Profile 切换 / 导入 / 导出 UI 入口。
    - `prompt_module.py` —— Prompt 模板、Renderer 切换、热更新。
    - `model_module.py` —— Provider Registry、Sampling / Context 参数。
    - `tool_module.py` —— Tool 注册、开关、权限。
    - `memory_module.py` —— Memory Provider、参数、生命周期。
    - `strategy_module.py` —— Agent 行为策略、Planner 参数、Reflection、阈值。
    - `trace_module.py` —— Trace 开关、日志等级、Runtime Trace 参数。
  - `agent_workbench/services/`：能力服务（第一版下放到 Agent 层）。
    - `model_provider.py` / `echo_provider.py`：统一 Provider 接口，Echo 占位实现。
    - `prompt_renderer.py` / `python_renderer.py`：PromptRenderer 统一接口，Python `str.format()` 实现。
    - `tool_registry.py`：Tool 注册表，支持开关、权限、schema。
    - `memory_service.py`：SQLite Memory 服务，基础 CRUD + namespace，不引入 Embedding / 向量搜索。
  - `agent_workbench/engines/workbench_llm_engine.py` / `workbench_tool_engine.py`：Workbench 专用 Engine，调用 ModelModule / ToolModule，通过 RuntimeContext 与 Runtime 交互。
- 扩展 v6 三栏高级 UI：
  - `agent_workbench/ui/left_panel.py`：`WorkbenchLeftPanel` 在 v6 左栏基础上新增左下角「设置」按钮，发射 `settings_requested` 信号。
  - `agent_workbench/ui/right_panel.py`：`WorkbenchRightPanel` 在 v6 右栏基础上新增「配置」标签页，内嵌配置面板。
  - `agent_workbench/ui/config_panel.py`：`AgentConfigPanel`，左侧模块列表 + 右侧 JSON 编辑器，支持查看 / 修改 / 保存 / 热更新四件事。
  - `agent_workbench/ui/main_window.py`：`WorkbenchMainWindow`，基于 v6 三栏 UI 组装完整窗口，集成自定义左右栏与配置面板。
  - `agent_workbench/ui/workbench_ui_controller.py`：`WorkbenchUIController` 继承 `v6.ui_controller.UIController`，复用 Session/Chat 服务，聊天请求转发给 `WorkbenchController`；设置按钮切换到右侧配置标签页。
- 新增 `agent_workbench/config/default.yaml`：完整 10 模块默认配置，YAML 唯一配置源。
- 新增 `agent_workbench/tests/test_agent_workbench.py`：7 个端到端测试，覆盖聊天生命周期、Tool Engine、PlannerLoop 决策、ConfigStore 读写、CLI 入口。

### Architecture
- Agent Workbench 内部分层：
  ```
  Desktop UI (WorkbenchMainWindow)
    |
    v
  WorkbenchUIController ──► v6 UIController (Session/Chat/Config 服务复用)
    |
    v
  WorkbenchController
    |
    v
  AgentWorkbenchRuntime
    ├── ConfigStore (YAML 唯一源)
    ├── ProfileManager
    ├── ModuleRegistry (10 RuntimeModules)
    ├── CoreAgentRuntime (v6 Framework Core)
    │     ├── Orchestrator
    │     ├── PlannerLoop
    │     ├── EngineManager
    │     ├── CapabilityRegistry
    │     ├── EventBus
    │     ├── RuntimeTrace
    │     └── ReplayService
    └── WorkbenchLLMEngine / WorkbenchToolEngine
  ```
- 10 模块分层：
  - 运行态：Runtime / Session
  - 配置态：Config / Profile
  - 能力态：Prompt / Model / Tool / Memory / Strategy
  - 观测态：Trace
- 热更新机制：`ConfigStore` 变更 → namespace 通知 → `Module.apply_config()`，无需重启 Runtime。
- UI 不直接持有 Module：`WorkbenchController` 只暴露 `AgentWorkbenchRuntime` 能力给 UI。

### test
- V6 核心测试：`pytest tests/v6/` **175/175 通过**。
- Workbench 测试：`pytest agent_workbench/tests/` **7/7 通过**。
- 合计：**182/182 通过**。
- GUI 冒烟：WorkbenchMainWindow 可正常实例化并退出。
- 打包验证：`python -m PyInstaller agent_workbench.spec` 成功生成 `dist/AgentWorkbenchV6.exe`；CLI/GUI 均可独立启动。

### Guarantees
- 不引入 Embedding、向量搜索、RAG、多 Agent 协作。
- 不引入真实 LLM 依赖；第一版仅 Echo Provider。
- 不修改 v6-core 功能；仅在 `v6/runtime/planner_loop.py` 补充 `set_policy()` 公共方法以修复外部切换策略的边界问题。
- 保持 v6 三栏 UI 设计风格 100% 不变，只做扩展不做重构。

## v6.8.0-alpha (2026-07-07) — V6 Framework Core Foundation

> **里程碑语义**：V6 共享核心框架基座版本已冻结。
> 从本版本开始，V6 Runtime 的核心控制面完整闭环：统一入口（`RuntimeContext` / `Task`）、统一协议（`Engine`）、统一通信（`EventBus`）、能力发现（`CapabilityRegistry`）、执行追踪（`RuntimeTrace` / `Replay`）、任务编排（`Orchestrator`）、调度决策（`PlannerLoop` / `Decision`）。
> 该版本作为后续 Agent / Service / Adapter 开发的基础版本，不是普通功能迭代。
> 注意：`PlannerLoop` 是 Runtime 决策机制，`PlannerEngine` 是八大 Engine 之一的能力组件，二者职责刻意分离。

### Added
- 新增 `v6/runtime/decision.py`：
  - `DecisionAction` 枚举：`execute_engine` / `wait` / `complete` / `fail`。
  - `Decision` 数据类：描述"下一步做什么"，含 `action` / `target` / `reason` / `metadata`。
- 新增 `v6/runtime/decision_policy.py`：
  - `DecisionPolicy` 策略基类。
  - `RuleBasedDecisionPolicy`：基于规则推断所需能力（image/code/tool/text），并通过 `CapabilityRegistry` 选择最佳 Engine。
- 新增 `v6/runtime/planner_loop.py`：
  - `Observation`：对当前 Runtime 状态的观察摘要。
  - `PlannerLoop`：Runtime 决策循环（Foundation），包含 `observe()` / `decide()` / `evaluate()` / `plan()` / `on_event()`。
  - 通过 EventBus 发布 `task.started`（phase=decision）事件，不直接写 Trace。
- 升级 `v6/runtime/orchestrator.py`：
  - 构造函数支持注入 `PlannerLoop`。
  - `_execute_task()` 改为先调用 `_make_decision()` 获取 `Decision`，再按决策执行 Engine / 完成 / 失败。
  - `_ensure_context()` 自动从 `ChatTask` 提取 `task_type` 与 `messages`，供策略匹配。
  - 增加状态防护：`_on_task_started()` 只处理 `CREATED` 状态任务，避免已失败/已完成任务被重入。
- 升级 `v6/runtime/runtime.py`：
  - `AgentRuntime` 默认构造 `PlannerLoop`（使用 `RuleBasedDecisionPolicy`）。
  - 将 `PlannerLoop` 注入 `Orchestrator`。
  - 新增 `planner_loop` 属性。
- 升级 `v6/runtime/engine_manager.py`：
  - 新增 `capability_registry` 只读属性，供 `PlannerLoop` / `Orchestrator` 使用。

### test
- 新增 `tests/v6/test_v6_planner_loop.py` 共 10 个测试，覆盖：
  - 文本任务决策为 `execute_engine` 并选择 `llm`。
  - 图像任务决策为 `execute_engine` 并选择 `vision`。
  - 无匹配能力时决策为 `fail`。
  - 无对应 Engine 时决策为 `fail`。
  - `Observation` 包含 `task_type`、`status`、`available_capabilities`。
  - `evaluate()` 返回 `complete`。
  - `plan()` 通过 EventBus 发布决策事件。
  - `PlannerLoop` 不直接写 Trace。
  - Orchestrator 通过 PlannerLoop 选择 VisionEngine 并完成 Task。

### Architecture
- 定义 V6 Framework Core Foundation：
  ```
  Task / RuntimeContext
    |
    v
  AgentRuntime
    |
    v
  Orchestrator + PlannerLoop
    |
    +---> EventBus (Runtime 神经系统)
    |
    +---> CapabilityRegistry (能力发现)
    |
    +---> EngineManager.execute(name, ctx) (Engine 单入口)
    |
    +---> RuntimeTrace / ReplayService (可观测与回放)
  ```
- 明确 `PlannerLoop` 与 `PlannerEngine` 分离：
  - `PlannerLoop`：Runtime 调度决策机制，输入 `RuntimeContext`，输出 `Decision`。
  - `PlannerEngine`：八大 Engine 之一，未来负责生成计划（plan generation）。
- 保持 Engine 单入口：`EngineManager.execute(name, ctx)` 继续作为 Runtime 调用 Engine 的唯一入口。
- 事件驱动：PlannerLoop 不直接调用 Trace，决策通过 EventBus 发布，由 Trace Hook 记录。
- V6 核心控制面闭环：统一入口、统一协议、统一通信、能力发现、执行追踪、任务编排、调度决策七要素齐备。

### Guarantees
- 不引入 LangChain Agent / ReAct / OpenAI function calling / MCP / Prompt Chain。
- 第一版 `PlannerLoop` 使用规则策略；未来可替换为 LLM-based / Human-approval 策略，而 Orchestrator 不变。
- Orchestrator 不硬编码 Engine 名称，所有 Engine 选择通过 `CapabilityRegistry` + `DecisionPolicy` 完成。
- 不接真实 LLM，不做自治循环（observe → think → act → repeat）。

## v6.6.0-alpha (2026-07-07) — Runtime Event Bus Foundation

> **里程碑语义**：V6 Runtime 内部神经系统（communication backbone）已冻结。
> 本版本之后，Engine / Service / Adapter / Observer 之间的通信统一走 Runtime Event Bus，不再允许 Engine 直接调用 Trace 或其他 Engine。

### Added
- 升级 `v6/runtime/event_bus.py`：从普通 EventEmitter 升级为 **Runtime Event Bus**。
  - 新增 `RuntimeEventType` 枚举：统一 `task.*` / `engine.*` / `service.*` / `tool.*` / `adapter.*` 事件命名。
  - 扩展 `RuntimeEvent` Schema：必填 `type` / `payload` / `task_id`，可选 `source` / `trace_id` / `phase` / `timestamp`。
  - 保留原有同步 `publish` / `emit` API，兼容旧调用。
  - 新增异步 `dispatch(event)` API：供 Runtime 内部精确控制事件时机。
  - 新增按 `task_id` 路由的 **Trace Hook**：`add_trace_hook(task_id, trace)` / `remove_trace_hook(task_id)`，使 `RuntimeTrace` 成为事件订阅者，Engine 不再直接调用 Trace。
- 升级 `v6/runtime/engines/base.py`：`BaseEngine` 支持 `set_event_bus()` 注入 EventBus，在 `execute()` 生命周期关键点发布 `engine.started` / `engine.completed` / `engine.failed` 标准事件。
- 升级 `v6/runtime/engine_manager.py`：构造函数支持 `event_bus` 参数；注册 Engine 时自动调用 `set_event_bus()` 完成注入。
- 升级 `v6/runtime/runtime.py`：`AgentRuntime` 默认将自身 `EventBus` 注入 `EngineManager`；任务执行期间自动将 `ctx.trace` 注册为 Trace Hook，任务结束后移除。

### test
- 新增 `test_runtime_event_schema`：验证 `source` / `trace_id` / `phase` 字段。
- 新增 `test_async_dispatch`：验证 `dispatch(RuntimeEvent)` 可 await。
- 新增 `test_trace_hook_routes_by_task_id` / `test_trace_hook_does_not_write_without_task_id`：验证 Trace Hook 按 task 路由。
- 新增 `test_engine_manager_wires_event_bus_to_engines`：验证 EngineManager 自动注入 EventBus。
- 新增 `test_engine_publishes_lifecycle_events_to_trace`：验证 Engine 事件经 EventBus 写入 Trace。
- 新增 `test_event_bus_prevents_engine_direct_trace_calls`：验证 Engine 不直接写 Trace，事件流是 Trace 唯一来源。

### Architecture
- 明确 EventBus 定位：**Runtime 内部神经系统（communication backbone）**，连接 Task / AgentRuntime / Engine / Service / Adapter / Observer。
- 明确与 Trace 的关系：EventBus 是事件来源，RuntimeTrace 是记录器；Engine 只 publish 事件，不调用 `ctx.trace.add`。
- 明确 Engine 间通信规则：禁止 Engine 直接互相调用，未来协作通过 EventBus 事件驱动。
- 事件流向：
  ```
  Engine
    |
    v
  RuntimeEventBus
    |
    +------> RuntimeTrace (via Trace Hook)
    |
    +------> Subscribers
  ```

### Guarantees
- Engine 不直接访问 `RuntimeTrace`；所有生命周期事件通过 `RuntimeEventBus` 路由。
- Engine 间通信使用标准 `RuntimeEvent`，禁止 `engine_a.call(engine_b)` 式直接调用。
- 每个 `RuntimeEvent` 必须携带 `task_id`，确保 Trace 可按 Task 关联与回放。
- `EngineManager` 负责 Engine 生命周期；事件总线负责 Engine 间通信；两者职责分离。

## v6.6.1-alpha (2026-07-07) — Engine Capability Registry

> **里程碑语义**：Runtime 进入"按能力选择 Engine"阶段。
> `EngineManager` 继续负责生命周期；`CapabilityRegistry` 负责按需求匹配与选择 Engine。

### Added
- 新增 `v6/runtime/capability_registry.py`：
  - `CapabilityQuery`：能力查询条件，支持 `capability` / `priority` / `streaming` / `metadata`。
  - `EngineMatch`：匹配结果，包含名称、得分与描述符。
  - `CapabilityRegistry`：按能力注册、查询、排序和选择 Engine。
- 为八大 Engine 声明 `capabilities`：
  - `llm`：`text_generation`
  - `tool`：`tool_execution`
  - `memory`：`memory_retrieval`, `memory_storage`
  - `planner`：`orchestration`
  - `workflow`：`workflow_execution`
  - `code`：`code_generation`, `code_execution`
  - `vision`：`image_understanding`
  - `knowledge`：`knowledge_retrieval`
- 升级 `v6/runtime/engine_manager.py`：
  - 构造函数支持 `capability_registry` 参数；默认自建。
  - `register()` 自动将 EngineDescriptor 同步到 CapabilityRegistry。
  - 新增 `capabilities()` / `find_engines(query)` / `select_engine(query)` 方法。
  - `unregister()` / `clear()` 同步清理 CapabilityRegistry。

### test
- 新增 `tests/v6/test_v6_capability_registry.py` 共 13 个测试，覆盖：
  - 能力列表聚合。
  - 按能力名称查询。
  - 匹配结果排序。
  - 最佳候选选择。
  - dict 查询条件转换。
  - metadata 过滤。
  - EngineManager 与 Registry 集成。

### Architecture
- 明确职责分离：
  - `EngineManager` = Engine 生命周期管理。
  - `CapabilityRegistry` = Engine 能力发现与选择。
- 调用方式升级：
  ```
  旧：manager.execute("llm")
  新：manager.execute(manager.select_engine({"capability": "text_generation"}))
  ```

## v6.6.2-alpha (2026-07-07) — Runtime Trace Replay Foundation

> **里程碑语义**：V6 Runtime Execution Replay 基础已落地。
> 本版本只做 **Deterministic Trace Replay**：记录、导出、查看执行轨迹，不重新调用 LLM/Tool/Memory。

### Added
- 新增 `v6/runtime/replay.py`：
  - `ReplayRecord`：独立回放记录，字段包括 `trace_id` / `task_id` / `timestamp` / `component` / `component_type` / `event_type` / `input_snapshot` / `output_snapshot` / `metadata`。
  - `ReplayLog`：线程安全的 ReplayRecord 容器，支持 `filter` / `timeline` / `export`。
  - `ReplayService`：Runtime Infrastructure 服务，订阅 EventBus 事件并生成 ReplayRecord；支持从 `RuntimeTrace` 批量导入历史步骤。
- `ReplayService` 作为 EventBus 订阅者接入 Runtime 事件流：
  ```
  Engine
    |
    v
  RuntimeEventBus
    |
    +------> RuntimeTrace (via Trace Hook)
    |
    +------> ReplayService
  ```

### Design
- `ReplayRecord` 与 `TraceStep` 职责分离：
  - `TraceStep` 关注"发生了什么"。
  - `ReplayRecord` 关注"如何重新发生"（输入 / 输出 / 组件 / 事件类型）。
- `ReplayService` 不是 Engine，不替代 `EngineManager` 或 `EventBus`；属于 Runtime Infrastructure。
- 第一版范围：
  - 5.3.1 Trace Persistence：保存 Task / Phase / Engine / Event / Result 轨迹。
  - 5.3.2 Replay Viewer：通过 `trace_id` / `task_id` 查看 Timeline 与 Step Detail。
  - 5.3.3 Replay Execution：暂不实现真正重新执行，待后续 checkpoint + snapshot + engine sandbox 成熟后再推进。

### test
- 新增 `tests/v6/test_v6_replay.py` 共 9 个测试，覆盖：
  - `ReplayRecord.from_event()` 字段解析。
  - `ReplayLog` 排序、筛选、导出。
  - `ReplayService` 从 `RuntimeTrace` 导入记录。
  - `ReplayService.view()` 摘要统计。
  - `ReplayService` 订阅 EventBus 事件。
  - `ReplayService` 不重新执行 Engine（Deterministic Replay 保证）。

### Architecture
- Runtime 可观测链路成型：
  ```
  Task → Phase → Engine → Service → Tool → Event → Result
                |
                v
        RuntimeEventBus
                |
        +-------+-------+
        |               |
  RuntimeTrace    ReplayService
        |               |
        +------> Timeline / Export / View
  ```

## v6.7.0-alpha (2026-07-07) — Runtime Orchestration Foundation

> **里程碑语义**：V6 Runtime 进入编排层。
> 本版本建立 **Orchestrator** 层与 **Task Lifecycle State Machine**，让 Runtime 从"调用者驱动 execute"升级为"Runtime 接收 Task 后自主推进生命周期"。
> 当前为 Foundation 阶段：不接真实 LLM，不做自治循环，只做线性状态推进。

### Added
- 扩展 `v6/runtime/enums.py` 的 `RuntimeState`：新增 `PLANNING` 与 `EXECUTING` 状态。
- 扩展 `v6/runtime/state_machine.py`：
  - 支持 `CREATED -> PLANNING -> EXECUTING -> COMPLETED/FAILED` 生命周期。
  - 保留原有 `RUNNING` 兼容路径。
  - 终态（`COMPLETED` / `CANCELLED`）无出边。
- 新增 `v6/runtime/orchestrator.py`：
  - `Orchestrator` 位于 AgentRuntime 与 EngineManager/CapabilityRegistry/EventBus/Trace 之间。
  - 维护每个 Task 的当前生命周期状态。
  - 通过 EventBus 订阅/发布任务事件驱动流程。
  - 使用 CapabilityRegistry 选择 Engine（如 `text_generation` -> `llm`）。
  - 不直接访问 Trace；Trace 由 EventBus Trace Hook 自动记录。
- 升级 `v6/runtime/runtime.py`：
  - `AgentRuntime` 默认创建并持有 `Orchestrator`。
  - 新增 `orchestrator` 属性。
  - 新增 `orchestrate(task)` 方法，通过 Orchestrator 提交任务。

### Design
- 明确 `Planner` 不是 Runtime 大脑：
  - `Orchestrator` 负责任务编排与生命周期。
  - `Planner` 只是 Orchestrator 可调度的一种决策能力（未来可替换为 Rule Planner / Workflow Planner / Human Approval Planner）。
- 明确第一阶段边界：
  - 不做 LLM 决策。
  - 不做自治循环（Observe → Reason → Plan → Act → Evaluate → Repeat）。
  - 只做线性 Task Lifecycle + EventBus 驱动 + Capability-based Engine 选择。

### test
- 新增 `tests/v6/test_v6_orchestrator.py` 共 7 个测试，覆盖：
  - Task 经历 `CREATED -> PLANNING -> EXECUTING -> COMPLETED`。
  - Orchestrator 通过 EventBus 发布任务事件。
  - 非法状态迁移返回 False。
  - Capability Registry 选择 Engine。
  - Orchestrator 不直接写 Trace。

### Architecture
- Runtime 核心层次成型：
  ```
  AgentRuntime
        |
        v
  Orchestrator
        |
        +---- EngineManager (lifecycle)
        +---- CapabilityRegistry (selection)
        +---- EventBus (communication)
        +---- RuntimeTrace (observation)
        +---- ReplayService (replay)
  ```

## v6.0.0-alpha (2026-07-07) — V6 独立 Runtime 架构线公开立项

### declaration
- **V6.0.0-alpha marks the beginning of the independent V6 Runtime architecture line.**
- 从本版本起，V6 作为 AI Agent Workbench 的第二代独立产品线正式立项，与 V5 在架构、接口、版本号上完全隔离。
- `v6.5.8-alpha` 保留为**内部迁移标签**，记录 Step 4 在 `v5-dev` 上的最终技术成果；`v6.0.0-alpha` 作为**公开立项标签**，代表 V6 独立产品线的起点。
- 后续 V6 版本号统一在 `v6-dev` / `v6` 分支上演进，格式为 `v6.x.y-alpha`。

### docs
- 新增 `PROJECT_LINEAGE.md`：根目录项目血统文件，明确 V5（Frozen/Legacy）与 V6（Active Development）身份、分支、标签规则及 AI 行为守则。
- 更新 `PROJECT_BLUEPRINT.md`：新增 `Current Development Authority` 区块；在元信息旁明确标注 `v6.0.0-alpha` 为公开立项版本。
- 更新 `README.md` 与 `PROJECT_BLUEPRINT.md`「V6 全新主线声明」：强调 `v6.0.0-alpha` 的立项意义。
- 更新 `.handoff/HANDOFF.md`：新增 `Current Development Authority` 区块，记录 `v6.0.0-alpha` 标签语义与分支状态。

## v6.5.8-alpha (2026-07-07) — Step 4：Eight Engine Skeleton + Runtime Integration Test

### feat
- 新增 `v6/runtime/engines/base.py`：`BaseEngine` 抽象基类，内置统一 `EngineState` 状态机与默认生命周期。
- 新增八大 Engine 空壳：
  - `llm.py` — LLM Engine
  - `tool.py` — Tool Engine
  - `memory.py` — Memory Engine
  - `planner.py` — Planner Engine（构造函数注入 `EngineManager`，演示编排 LLM/Tool）
  - `workflow.py` — Workflow Engine
  - `code.py` — Code Engine
  - `vision.py` — Vision Engine
  - `knowledge.py` — Knowledge Engine
- 所有 Engine 统一实现 `load()` / `initialize(ctx)` / `health_check()` / `execute(ctx)` / `shutdown()`。
- `execute(ctx)` 返回 `RuntimeResult`，占位数据写入 `result.extra`，`status="placeholder"`。

### refactor
- 清理 `v6/runtime/engines/` 下与新版 Engine Protocol 不兼容的旧实现（Context/Prompt/Inference/Metrics/Phase/Policy 等）。
- 删除 `tests/v6/test_v6_engines.py`，更新 `tests/v6/test_v6_smoke.py` 导入新的 Engine 模块。

### test
- 新增 `tests/v6/test_v6_runtime_kernel.py` Runtime Kernel 集成测试，覆盖：
  - EngineManager 动态发现八大 Engine。
  - 所有 Engine 生命周期一致性（CREATED → READY → STOPPED）。
  - 所有 Engine 执行返回 `RuntimeResult`。
  - `EngineManager.execute()` 自动产生 `engine:{name}` TraceStep。
  - Planner 编排 LLM/Tool 并产生对应 Trace Timeline。
  - Planner 无 `EngineManager` 注入时回退到 placeholder。
- V6 全量测试 `pytest tests/v6/` **130/130 通过**。

## v6.5.7-alpha (2026-07-07) — Step 3：Engine Protocol 与 EngineManager 生命周期

### feat
- 新增 `v6/runtime/engine_state.py`：定义 `EngineState` 枚举，与 `RuntimeState` 分离。
  - 生命周期链：`CREATED -> LOADING -> LOADED -> INITIALIZING -> READY -> RUNNING -> STOPPING -> STOPPED`
  - 异常状态：`DEGRADED`、`ERROR`
- 新增 `v6/runtime/engines/protocol.py`：
  - `Engine` Protocol：`load()` / `initialize(ctx)` / `health_check()` / `execute(ctx)` / `shutdown()`
  - `EngineDescriptor`：name / version / capabilities / dependencies / state / instance / metadata
  - `EngineNotReadyError`：execute 阶段状态校验异常
- `RuntimeContext` 新增 `request` 字段：作为 Engine 执行请求载荷容器，`EngineManager.execute()` 调用前由调用方写入 `ctx.request`，Engine 从 `ctx.request` 读取。
- 重构 `v6/runtime/engine_manager.py`：
  - `register(engine)` 注册 Engine 实例，自动创建 `EngineDescriptor` 与状态。
  - 支持完整生命周期：`load()` / `initialize(ctx)` / `health_check()` / `execute(name, ctx)` / `shutdown()`。
  - 支持批量操作：`initialize_all(ctx)` / `health_check_all()` / `shutdown_all()`。
  - `execute()` 入口自动调用 `RuntimeTrace.timed_step()` 记录 Engine Timeline。
  - 生命周期异常时自动迁移到 `ERROR` 状态。

### refactor
- Engine 公共接口统一为单 `RuntimeContext` 入口：
  - 禁止 `Engine.execute(request, ctx)` 双参数设计。
  - 所有 Engine 通过 `ctx.request` / `ctx.metrics` / `ctx.trace` / `ctx.result` 协作。

### test
- 新增/更新 Engine 测试共 26 个：
  - `tests/v6/test_engine_protocol.py`：Protocol、Descriptor、Error 共 6 个测试。
  - `tests/v6/test_v6_engine_manager.py`：注册、生命周期、健康检查、执行、Trace 记录、失败转 ERROR 共 20 个测试。
- V6 全量测试 `pytest tests/v6/` **144/144 通过**。

## v6.5.6-alpha (2026-07-07) — Step 2：RuntimeTrace + Metrics 联动

### feat
- 扩展 `v6/runtime/trace.py` 的 `TraceStep`，新增四个指标字段：
  - `duration_ms`：步骤耗时（毫秒）
  - `tokens`：步骤 Token 消耗
  - `cost`：步骤估算成本
  - `tool_time_ms`：步骤中工具执行耗时
- `RuntimeTrace.add()` 支持两种指标写入方式：
  - 显式传入 `duration_ms` / `tokens` / `cost` / `tool_time_ms`。
  - 传入 `metrics=RuntimeMetrics(...)`，自动提取当前指标快照。
  - 显式值优先于 metrics 提取值。
- 新增 `RuntimeTrace.timed_step()` 上下文管理器：
  - 进入时自动记录 `timestamp`。
  - 退出时自动计算 `duration_ms`。
  - 退出时自动抓取 `RuntimeMetrics` 的 `tokens` / `cost` / `tool_time_ms`。
  - 支持在 `with` 块内修改 `step.payload`。

### test
- 扩展 `tests/v6/test_v6_trace.py`，新增 9 个联动测试：
  - 默认指标字段为 0。
  - 显式传入指标。
  - 从 `RuntimeMetrics` 自动提取指标。
  - 显式指标覆盖 metrics 提取值。
  - `timed_step` 自动计时。
  - `timed_step` 退出时抓取 metrics。
  - `timed_step` 支持修改 `step.payload`。
  - `snapshot()` 包含指标字段。
  - 步骤间指标相互独立。
- V6 全量测试 `pytest tests/v6/` 125/125 通过。

## v6.5.5-alpha (2026-07-07) — V6.5 Runtime Foundation Layer：状态机固化

### feat
- 明确 V6.5 阶段定位为 **Runtime Foundation Layer**，V7 为 Runtime Kernel，V8 为 Distributed Agent Runtime。
- 新增 `v6/runtime/state_machine.py`：定义 `RuntimeStateMachine`，固化 `RuntimeState` 生命周期迁移规则。
- 支持状态：`CREATED` / `QUEUED` / `RUNNING` / `WAITING` / `PAUSED` / `CANCELLED` / `COMPLETED` / `FAILED`。
- 支持重试语义：`FAILED -> QUEUED`。
- 终态无出边：`COMPLETED`、`CANCELLED`。
- 非法迁移抛出 `RuntimeStateTransitionError`。

### test
- 新增 `tests/v6/test_runtime_state_machine.py`，覆盖 10 个迁移场景：
  - `CREATED -> QUEUED / CANCELLED` 合法，`CREATED -> RUNNING / COMPLETED` 非法。
  - `QUEUED -> RUNNING` 合法。
  - `RUNNING -> WAITING / PAUSED / CANCELLED / COMPLETED / FAILED` 全部合法。
  - `WAITING -> RUNNING / CANCELLED / FAILED` 合法。
  - `PAUSED -> RUNNING / CANCELLED` 合法。
  - `FAILED -> QUEUED` 重试合法。
  - 终态无出边。
  - 非法迁移报错且错误信息含状态名。
- V6 全量测试 `pytest tests/v6/` 116/116 通过。

## v6.5.4-alpha (2026-07-07) — Runtime Kernel 预备层：Metrics / Result / State / EngineManager

### feat
- 新增 `v6/runtime/metrics.py`：定义 `RuntimeMetrics` 统一统计接口，覆盖 `tokens`/`latency_ms`/`tool_time_ms`/`memory_hits`/`cache_hits`/`cost`/`retry`/`queue_time_ms`/`custom`。
- 新增 `v6/runtime/result.py`：定义 `RuntimeResult` 统一输出协议，覆盖 `answer`/`tool_result`/`files`/`images`/`artifacts`/`error`/`status`/`extra`。
- 新增 `v6/runtime/engine_manager.py`：统一管理 Engine 注册、获取、注销，避免 Runtime 直接 `new Engine`，为动态替换与测试预留扩展点。

### refactor
- `RuntimeContext.metrics` 从裸 `dict` 升级为 `RuntimeMetrics`。
- `RuntimeContext.result` 从裸 `dict` 升级为 `RuntimeResult`。
- `RuntimeContext.status` 从字符串升级为 `RuntimeState` 枚举，序列化时自动转换字符串。
- `RuntimeContext.snapshot()` / `restore()` / `clone()` / `reset()` 全面兼容 `RuntimeMetrics` / `RuntimeResult` / `RuntimeState`。
- `AgentRuntime` 统一使用 `RuntimeState.RUNNING` / `COMPLETED` / `FAILED` 枚举设置任务状态。
- `v6/runtime/trace.py` 补回 `Enum` 导入，`TraceStep.__post_init__` 可正确转换枚举为字符串。

### test
- 新增 `tests/v6/test_v6_engine_manager.py`，覆盖 `register` / `get` / `has` / `names` / `unregister` / `clear` / `run` / 覆盖注册。
- 更新 `tests/v6/test_v6_trace.py`，改用 `TraceEvent` / `RuntimeState` 枚举进行断言。
- V6 全量测试 `pytest tests/v6/` 106/106 通过。

### docs
- `docs/v6/SPEC.md` 将 8.16 节 RuntimeTask 四对象模型升级为五对象模型，新增 `RuntimeState` 生命周期对象。
- 新增 8.17 节：RuntimeMetrics 统一统计接口设计原则。
- 新增 8.18 节：RuntimeResult 统一输出协议设计原则。
- 新增 8.19 节：RuntimeState 生命周期枚举设计原则。

## v6.5.3-alpha (2026-07-07) — Runtime Trace 基础能力与 Replay 支持

### feat
- 新增 `v6/runtime/trace.py`：定义 `TraceStep`、`RuntimeTrace`、`ReplayPlayer`。
- `RuntimeTrace` 记录 `Task → Phase → Engine/Service/Tool → Finish` 执行历史，线程安全，支持 `snapshot` / `filter` / `last`。
- `ReplayPlayer` 可按 trace 中记录的 `emit_*` 步骤重放事件，供调试、审计、回归测试。
- `RuntimeContext` 新增 `trace` 与 `result` 字段，与 Task 生命周期绑定。
- `RuntimeContext.snapshot()` / `restore()` / `clone()` / `reset()` 全面支持 `trace` 与 `result`。
- `AgentRuntime` 自动记录任务生命周期：`task_start` / `handler_dispatch` / `task_finish` / `task_error`。
- `EchoHandler` 记录 Engine 步骤：`echo_start` / `input_read` / `emit_start` / `emit_chunk` / `emit_end` / `echo_end`。
- `LocalRuntimeAdapter.submit()` 记录 Adapter 步骤。

### docs
- `docs/v6/SPEC.md` 新增 8.15 节：Runtime Trace 设计原则与 Replay 能力。
- `docs/v6/SPEC.md` 新增 8.16 节：RuntimeTask 四对象模型长期演进方向。

### test
- 新增 `tests/v6/test_v6_trace.py`，覆盖 `RuntimeTrace` 基础操作、`RuntimeContext` trace 生命周期、Runtime 自动记录 trace、`ReplayPlayer` 事件回放。
- V6 全量测试 `pytest tests/v6/` 99/99 通过。

## v6.5.2-alpha (2026-07-07) — UIController ↔ RuntimeAdapter Application Boundary 集成

### refactor
- `AgentRuntime._execute` 支持从 `Task.payload["ctx"]` 接收已有的 `RuntimeContext`，实现 Adapter → Runtime 的上下文透传。
- `AgentRuntime._echo_handler` 优先从 `ctx.messages` 读取用户输入，回写 AI 回复到同一 `ctx`。
- `UIController` 移除对 `AgentRuntime` 的直接依赖，改为依赖 `IRuntimeAdapter`。
- `UIController.startup()` / `shutdown()` 改为启动 / 停止 `RuntimeAdapter`。
- `UIController.on_send_msg()` 构造 `RuntimeContext` 后通过 `adapter.submit(ctx)` 提交。
- `UIController.on_stop_msg()` 通过 `adapter.cancel(task_id)` 取消任务。
- 事件订阅统一走 `adapter.subscribe(...)`，保持 Runtime Core 不感知调用方。

### test
- 新增 `test_adapter_submit_propagates_context`，验证 `RuntimeContext` 经 `LocalRuntimeAdapter` 透传到 `AgentRuntime` 后状态一致。
- V6 全量测试 `pytest tests/v6/` 91/91 通过。

## v6.0.1-alpha (2026-07-07) — V6 Runtime 协议深化与 Service 层统一改造

### refactor
- `RuntimeContext` 新增 `new()` 工厂方法，由 Runtime Task 自动生成 `task_id` 并初始化 Runtime Facts。
- `ConfigService` / `SessionService` / `ChatService` 统一为 `(ctx: RuntimeContext)` 输入接口，彻底移除 legacy 方法。
- `UIController` 全面改用 `RuntimeContext.new()` 构造上下文，避免业务代码手动填写无意义 `task_id`。

### docs
- `docs/v6/SPEC.md` 补充 Runtime Interface Principle。
- 明确 `RuntimeContext` 为 Runtime 唯一 Public Runtime Protocol。
- 明确 Adapter 属于 Application Layer，不保存状态、不做业务。
- 新增 8.14 节，澄清 `RuntimeContext.new()` 语义为“创建 Runtime Task”而非创建数据对象。

### test
- 更新 `tests/v6/test_v6_services.py`、`tests/v6/test_v6_runtime.py`、`tests/v6/test_v6_ui_contract.py`，全部使用 `RuntimeContext.new()`。
- 修复 `test_v6_ui_contract.py` 首行 docstring 语法错误。
- V6 全量测试 `pytest tests/v6/` 90/90 通过。

## v6.0.0-alpha (2026-07-07) — V6 项目启动与架构规格

### feat
- 判定 V5 失败并完整归档冻结，启动 V6 从零重写。
- 建立 V6 独立目录 `v6/`，包含 `ui/`、`runtime/`、`runtime/engines/`、`services/`、`main_window.py`、`ui_controller.py`、`layout_manager.py`、`session_manager.py`、`config_manager.py`。
- 编写 V6 架构文档 `docs/v6/PROJECT_BLUEPRINT_v6.md`、接口契约 `docs/v6/SPEC.md`、路线图 `docs/v6/ROADMAP.md`、变更日志 `docs/v6/CHANGELOG_v6.md`。
- 明确分层架构：MainWindow → UIController → Manager → AgentRuntime → Engines。
- 建立专业 Agent 协作流程：UI Agent / Runtime Agent / Review Agent，每阶段必须 Review + Smoke + Git 存档。

### chore
- 清理 V5 失败尝试残留未跟踪文件：`v5/widgets/apple_menu.py`、`function_page.py`、`header_bar.py`、`input_area.py`、`session_group.py`、`session_item.py`。

### test
- 新增 `tests/v6/test_v6_smoke.py`，V6 模块 import smoke 测试 5/5 通过。

## v5.0.23-alpha (2026-07-06) — v4 归档打包入口与 v5 并行构建

### fix
- 修复 `v5/service/chat_worker.py` 中 `AgentWorker.TOOL_DEFINITIONS` 属性错误，改为从 `workers.agent_worker` 导入 `TOOL_DEFINITIONS`。

### build
- 创建 `v4/v4_main.py` 归档入口、`v4/AgentWorkbenchV4.spec` 打包配置、`v4/scripts/rebuild_v4.ps1` 一键打包脚本。
- `scripts/rebuild.ps1` 生成的桌面快捷方式命名为「AI Agent Workbench V5」。
- `v4/scripts/rebuild_v4.ps1` 生成 `dist/AgentWorkbenchV4/` 与桌面快捷方式「AI Agent Workbench V4」。
- 验证 `dist/AgentWorkbench/AgentWorkbench.exe` 与 `dist/AgentWorkbenchV4/AgentWorkbenchV4.exe` 均可独立启动。

### chore
- 更新 `v4/README.md`，说明 v4 已冻结于 `v4-refactor` 分支 `v4.0.11-alpha`，并标注独立打包入口。

### test
- 全量测试：`pytest tests/` 272/272 通过。

## v5.0.22-alpha (2026-07-06) — 补充 Git 忽略规则

### chore
- 更新 `.gitignore`，排除 `.reference/`、`.scripts/`、`review/` 等本地参考仓库、调试脚本和归档目录，保持 `git status` 干净。

## v5.0.21-alpha (2026-07-06) — 工作区整理与文档同步

### chore
- 修正 `config/config.yaml` 中 `app.version` 为 `v5.0.20-alpha`，与文档版本对齐。
- 统一以 `docs/` 为正式文档目录，根目录新建 `README.md` 并指向 `docs/` 下文档。
- 将根目录旧版 `CHANGELOG.md` / `PROJECT_BLUEPRINT.md` 与 `docs/` 版本同步。

### docs
- 更新根目录与 `docs/` 下 `PROJECT_BLUEPRINT.md` 目录树：
  - `AgentWorkbench.spec` → `AgentWorkbenchV5.spec`
  - 移除已归档的顶层 `blueprints/`、`ui/`、`resources/` 目录
  - `tests/` 描述改为 272 个 V5 测试，删除 `test_v4_*` / `test_explorer_*` 文件列表
- 修正所有文档中测试数量为 `272/272`。

### archive
- 将 `AgentWorkbench.spec` 移入 `v4/legacy/build/`。
- 将 `ui/` 目录移入 `v4/legacy/ui/`。
- 将 `resources/themes/*.qss` 移入 `v4/legacy/resources/themes/`。
- 将 `blueprints/` 移入 `docs/archive/blueprints/`。
- 将 `tests/test_v4_*.py` 与 `test_explorer_*.py` 移入 `v4/tests/`。
- 将 `scripts/verify_ui_fold.py` 与 `test_llm_orchestrator_like.py` 移入 `v4/scripts/`。

### test
- 全量测试：`pytest tests/` 272/272 通过。

## v5.0.20-alpha (2026-07-06) — V5 剩余 5% 细节功能闭环

### fix
- 修复 `v5/service/adapter.py` 中实例属性 `self._on_tool_executed` 与类方法 `_on_tool_executed` 同名冲突，导致 `worker.tool_executed` 信号连接到空 lambda、终端工具日志无法输出的 Bug。
- 将实例属性重命名为 `self._on_tool_executed_cb`，保留类方法名不变，信号现在正确连接到方法（先输出终端日志，再转发外部回调）。
- 修复 `AgentWorkbench.spec` 隐藏导入：移除已删除的 `v5.model.events`，添加 `v5.service.chat_worker`。

### feat
- `v5/widgets/chat_area.py` 的 `_add_ai_entry` 支持按 `phase` 渲染 `PhasePanel` 阶段面板。
- `v5/widgets/chat_items.py` 的 `PhasePanel.PHASE_COLORS` 补充 `confirm` 阶段样式，完整支持 analyze/confirm/execute/verify/archive 五种阶段。
- `ChatArea.to_plain_text()` 增加对 `role == "tool"` 的 HTML 内容拼接，方便测试验证。

### test
- `tests/test_v5_adapter.py` 新增工具执行/确认请求的终端日志与回调转发测试。
- `tests/test_v5_controller.py` 新增 `sign_tool_executed`、`sign_confirm_required` 信号透传，`handle_confirmation_result`、`handle_analyze_project`、`handle_session_rename` 行为测试。
- `tests/test_v5_chat_area.py` 新增 `append_tool` 渲染与全部五种 phase 渲染测试。
- `tests/test_v5_integration.py` 新增 craft 模式下完整工具调用流程测试（chunk → tool → confirm → ai final）。
- 全量测试：`pytest tests/` 272/272 通过。

### build
- PyInstaller 重新打包 `dist/AgentWorkbench/AgentWorkbench.exe`，验证 exe 可独立启动并保持运行。

## v5.0.19-alpha (2026-07-06) — V5 模式列表统一与全量测试补齐

### fix
- 修复 `v5/widgets/chat_area.py` 硬编码模式列表 `["ask", "plan", "build", "review"]` 与引擎 `PHASE_FLOW` 不一致的 Bug。
- 新增 `WorkController.manual_modes` 属性，从 `config.yaml` 的 `manual_modes` 键动态读取引擎支持的模式，默认回退 `["ask", "plan", "craft"]`。
- `ChatArea` / `SettingsDialog` 改为从 Controller 注入模式列表，避免 UI 层与引擎不一致。

### refactor
- 将 `v5/service/adapter.py` 中的 `_ChatWorker` 拆分为独立模块 `v5/service/chat_worker.py`，保持对外接口不变。
- 删除未使用的 `v5/model/events.py`。

### test
- 新增 `tests/test_v5_chat_area.py`（55 用例），覆盖 HeaderBar / SearchBar / MoreDropdown / InputArea / ChatArea UI 组件。
- 新增 `tests/test_v5_adapter.py`（16 用例），覆盖 V5Adapter 回调注册、会话操作转发、消息总线事件处理。
- 新增 `tests/test_v5_integration.py`（7 用例），端到端验证 Controller + ChatService + SessionService + Adapter 链路。
- 全量测试：`pytest tests/` 319/319 通过。

### build
- 修复 `AgentWorkbenchV5.spec` 隐藏导入错误：移除不存在的 `v5.model.events`，添加 `v5.service.chat_worker`。
- PyInstaller 重新打包 `dist/AgentWorkbench/AgentWorkbench.exe`，验证 exe 可独立启动并创建主窗口。

## v5.0.18-alpha (2026-07-06) — V5 P6/P7 收尾归档

### docs
- README / PROJECT_BLUEPRINT / CHANGELOG 版本号对齐至 `v5.0.18-alpha`。
- 新增 `v4/README.md` 归档说明，明确 `v4/` 为只读区，`v5/` 为新开发主线。

### test
- 提交 `tests/test_v5_service.py`、`tests/test_v5_controller.py`、`tests/test_v5_smoke.py`，15 个 V5 用例纳入版本控制。
- 全量测试 `240/240` 通过。

### build
- 提交 `AgentWorkbenchV5.spec` 作为 V5 独立打包配置。

### chore
- 清理 P8/P9/P10/P15 调试产物与临时截图，保持仓库整洁。

## v5.0.17-alpha (2026-07-06) — V5 彻底隔离 v4 与 P6/P7 主体整改

### refactor
- **彻底隔离 v4**：清理 `v5/` 全部含 v4 文字残留，确认无任何 `v4` 导入；Service 层仅依赖根目录共享核心模块。
- **Widget 层信号契约统一**：修复 `ChatArea` 与 `MainWindow`、`RightPanel` 与 `MainWindow` 的信号连接，补齐终端/文件/浏览器用户操作信号转发到 `WorkController`。
- **布局修复**：修正 `InvisibleResizeHandle` 被误作 `QSplitter` pane 的问题，热区父控件改为 central widget，保证三栏尺寸正确。

### test
- 新增 `tests/test_v5_service.py`、`tests/test_v5_controller.py`、`tests/test_v5_smoke.py`，覆盖 V5 Service/Controller/MainWindow 核心行为，新增 15 个用例。
- 全量测试 `240/240` 通过。

### build
- 新增 `AgentWorkbenchV5.spec` 作为 V5 独立打包配置。
- PyInstaller 打包 `dist/AgentWorkbench/AgentWorkbench.exe` 可正常启动并存活 6 秒以上。

### docs
- 新增 `v4/README.md` 标注 v4 目录为只读归档区，明确新主线为 `v5/`。
- 更新 `docs/PROJECT_BLUEPRINT.md` 版本与目录结构说明。

## v5.0.13-alpha (2026-07-06) — 修复打包后浏览器标签不可用

### fix
- **修复 exe 内浏览器初始化失败**：在 [AgentWorkbench.spec](file:///f:/Agent/agent_workbench/AgentWorkbench.spec) 中显式打包 `PySide6/QtWebEngineProcess.exe`、`PySide6/resources/` 与 `PySide6/translations/qtwebengine_locales`，并恢复 `PySide6.QtWebChannel`、`PySide6.QtWebSockets`、`PySide6.QtSql` 依赖（之前被 excludes 误排除）。

### build
- **PyInstaller 重新打包**：`dist/AgentWorkbench/AgentWorkbench.exe` 已验证浏览器可正常加载 Bing 页面，架构 / 终端 / 文件编辑器 / 浏览器四个标签均非空。

### docs
- 更新 README / PROJECT_BLUEPRINT / CHANGELOG 至 `v5.0.13-alpha`，记录打包修复与右栏功能验证结果。

### test
- 全量 225 项测试通过，零回归。

## v5.0.12-alpha (2026-07-06) — UI 完全移植工程最终完整性检查与存档

### docs
- **PROJECT_BLUEPRINT 升级至 v5.0.12-alpha**：存档次数 12，项目概要补充 P10 复核、P11 `v4-refactor` 最终归档与真实 GUI 验证结论，最近变更记录本阶段。
- **README 当前状态更新**：版本 `v5.0.12-alpha`，补充 exe 独立启动验证与 `v4-refactor` 归档信息。
- **CHANGELOG 顶部记录本阶段**：归档 P10 复核与 P11 旧线路归档结果。

### chore
- **P10 复核**：确认 `v4/legacy/` 旧 UI 备份完整，`v4/` 根目录无重复旧 UI 文件；`AgentWorkbench.spec` hiddenimports 已包含全部 `v4.widgets.*`；PyInstaller 重新打包成功。

### build
- **exe 独立启动冒烟**：`dist/AgentWorkbench/AgentWorkbench.exe` 启动后存活 10 秒无异常退出。

### archive
- **`v4-refactor` 旧线路最终归档**：在 `v4-refactor` 分支更新 README / PROJECT_BLUEPRINT / CHANGELOG 归档声明，冻结文档；推送标签 `v4.0.11-alpha`。

### test
- 全量 225 项测试通过，零回归。

## v5.0.10-alpha (2026-07-06) — v5 项目文档同步

### docs
- **README 升级为 v5 线路**：项目描述改为 v5 新 UI 完整版，测试数更新为 225，文件地图补充 `v4/widgets/` 与 `v4/legacy/`，当前状态更新为 v5.0.9-alpha / v5-dev。
- **PROJECT_BLUEPRINT 升级为 v5**：版本号 `v5.0.10-alpha`，存档次数 10，项目概要重写为 v5 新 UI 完全移植历程，目录结构同步 `v4/widgets/` 控件库与 `v4/legacy/` 旧 UI 备份，最近变更与历史归档补充 v5.0.0~v5.0.9 全部阶段。
- **CHANGELOG 补充 v5 历史**：在顶部记录 v5.0.10-alpha，并补录 v5.0.0~v5.0.9 各阶段变更。

## v5.0.9-alpha (2026-07-06) — P10 清理旧UI与打包验证

### chore
- 删除 `v4/` 根目录下重复的旧 UI 文件（`chat_items.py`、`chat_scene.py`、`conversation_list.py`、`icons.py`、`input_area.py`、`right_panel.py`），完整备份保留在 `v4/legacy/`。
- 旧测试迁移导入：`tests/test_v4_input_area.py`、`tests/test_v4_right_panel.py` 改为从 `v4.legacy.*` 导入。
- 修复 `v4/legacy/right_panel.py` 内部导入路径。

### build
- 更新 `AgentWorkbench.spec` 的 `hiddenimports`：移除已删除旧模块，补全 `v4.widgets.*` 新模块。

### test
- PyInstaller 打包成功，输出 `dist/AgentWorkbench/AgentWorkbench.exe`。
- 独立启动 exe 验证三栏加载、会话创建、UI 事件分发正常。
- 全量测试 225/225 通过。

## v5.0.8-alpha (2026-07-06) — P8 完整功能回填与GUI冒烟修复

### fix/ui
- 修复 `v4/widgets/chat_area.py` 中 `QPen` 导入缺失导致的 `paintEvent` 崩溃。
- 验证三栏布局加载、会话创建、UI 事件分发正常。

### test
- 全量测试 225/225 通过。

## v5.0.7-alpha (2026-07-06) — P7 右栏真实功能回填

### feat/ui
- 新增 `v4/widgets/terminal_widget.py`：终端命令输入、执行、输出显示、停止/清空。
- 新增 `v4/widgets/file_reader_widget.py`：文件读取/编辑、保存、大文件截断、多编码解码。
- 新增 `v4/widgets/browser_widget.py`：嵌入式浏览器（QWebEngineView）、地址栏、前进/后退/刷新/主页。
- `v4/widgets/right_panel.py` 集成上述三组件，实现最近文件列表及点击打开。

### fix
- `workers/terminal_worker.py` 添加 `creationflags=subprocess.CREATE_NO_WINDOW`，修复 Windows 下命令窗口闪现。

### test
- 新增 `tests/test_v4_widgets_right_panel.py` 覆盖 TerminalWidget / FileReaderWidget / BrowserWidget / RightPanel，共 13 个用例。
- 全量测试 225/225 通过。

## v5.0.6-alpha (2026-07-06) — P5/P6 持久化校验与测试整改

### fix
- `v4/main_window.py` 启动时校验 `app.last_mode` / `app.last_model`，无效值回退到首个有效值。
- `_on_settings_applied` 校验 theme / mode / model，防止外部配置污染。
- `v4/widgets/base.py` 补充主题键 `send_btn`、`send_btn_hover`、`stop_btn`、`stop_btn_hover`、`tag_text`，兼容旧 UI 组件测试。

### test
- 修复 `test_settings_dialog_persists_theme_mode_model` 与 `test_window_starts_without_crash`。
- 新增 4 个边界测试覆盖无效 mode/model 回退与配置持久化。
- 全量测试 212/212 通过。

## v5.0.5-alpha (2026-07-06) — P5 会话数据持久化与列表同步

### feat
- 实现 `app.last_session_id` 持久化与启动恢复。
- 会话切换 / 创建 / 删除时同步更新配置。
- 无效会话清理与左栏空状态显示。
- `SessionMetadata` 新增 `last_preview` 字段，`repository.list_sessions` 子查询最后消息，确保预览文本正确。

### test
- 新增会话持久化相关集成测试。
- 全量测试通过。

## v5.0.4-alpha (2026-07-06) — P4 关键用户动作对接

### feat/ui
- 停止按钮 → `UserStopEvent`。
- 确认按钮 → `UserConfirmEvent`。
- 分析项目按钮 → `UIAnalyzeProjectEvent`。
- 导出会话、打开设置对话框。
- HeaderBar 搜索过滤：`search_text_changed` 连接到 `_left.filter_sessions`。
- 模式 / 模型下拉选择器 `DropdownSelector`，配置持久化。

### fix
- 修复会话列表预览显示问题：优先使用 `last_preview` 字段。
- 修复置顶会话标题未显示 "📌" 标记。

## v5.0.3-alpha (2026-07-06) — 模块化骨架拆分与致命Bug修复

### refactor
- 将 `v4/main_window.py` 拆分为 `v4/widgets/` 下的 9 个模块（base / window_frame / left_panel / chat_items / chat_scene / chat_area / right_panel / dropdown_selector / settings_dialog），主窗口降至 357 行。

### fix
- 修复 `_session_idx_map` 永远为空导致会话选择/操作失效的问题，统一使用 `LeftPanel._idx_to_sid`。
- 修复 `TabButton` 缺少 `text()` 方法。
- 修复 `LeftPanel.refresh` 覆盖预览文本等问题。

## v5.0.2-alpha (2026-07-06) — P3 UIRenderer与新UI桥接完成

### feat/ui
- `ChatArea` 实现真实消息渲染、流式输出、确认条和阶段状态。
- `LeftPanel` 实现会话列表按项目分组刷新与 badge 更新。
- `UIRenderer` 与新 UI 控件桥接完成。

### fix
- 修复 `SessionGroup` 右键动作信号。

## v5.0.1-alpha (2026-07-06) — 备份v4旧UI组件并标记v5-dev线路

### chore
- 将 `conversation_list.py`、`input_area.py`、`right_panel.py`、`chat_items.py`、`chat_scene.py`、`icons.py`、`main_window_legacy.py` 移至 `v4/legacy/`。
- 更新文档标记 v5-dev 线路。

## v5.0.0-alpha (2026-07-06) — v5-dev线路起点与新UI后端核心注入

### feat/ui
- `v5-dev` 分支起点。
- 新 UI 后端核心注入：`v4/main_window.py` 接入新 UI 壳层，保留 v4 单轨后端骨架。

## v4.0.8-alpha (2026-07-01) — v4全量UI三位一体对齐SVG设计稿

### feat
- **HeaderToolbar 按钮尺寸/样式对齐 SVG**：按钮 28×24→18×22，图标 18px→14px，SVG stroke-width 2→1.5，标题字号 15/12px→12/10px，边框加 0.5px solid + border-radius 3px。
- **InputArea 标签式 mode/model 替代 QComboBox**：`TagSelectButton` 实现"标签名 + 值 + ▼"弹出菜单，模式/模型选择从下拉框改为贴纸标签样式；`SkillSendButton` 36×36→24×24（r=12），技能按钮 32×32→20×20（r=10）。
- **RightPanel 标签栏交互增强**：`setTabsClosable(True)` + `tabCloseRequested` 支持关闭非核心标签；新增搜索角标按钮（🔍）；标签栏样式改为圆角 + 紧凑边距；新增 `RecentFilesList` 组件（路径+时间列表）。
- **聊天区 Phase 面板与折叠块样式对齐**：去掉 `max-width:85%` 限制 + 4px 左边色条卡片化；fold-block 加 0.5px solid border；Phase 面板 header 加底部 border-bottom；清理旧 CSS。
- **左栏 Tag 等宽**：功能/会话标签页使用 `addWidget(btn, 1)` 均分宽度。
- **死代码清理**：删除 `v4/right_panel.py` 中未使用的 `FunctionPageWidget`（与 conversation_list 中的同名类无关）。

### refactor
- `v4/input_area.py` 重写：QComboBox → TagSelectButton，SkillSendButton 尺寸对齐 SVG，InputTextEdit 封装 Enter/Shift+Enter 逻辑。

### test
- 修复 `tests/test_v4_input_area.py` 适配新 TagSelectButton API（`mode_selector` → `mode_tag`、`model_selector` → `model_tag`）。
- 全量 29 项测试通过，零回归。

## v4.0.5-alpha (2026-06-30) — 工程目录标准化 + PyInstaller 路径适配

### refactor
- **工程目录标准化改造**：根目录文件按职责分组，结束配置/文档/脚本/图标一股脑堆在根目录的状态。
  - `config/`：存放 `config.yaml`、`.env`、`.env.example`。
  - `assets/`：存放 `app.ico` 应用图标。
  - `scripts/`：存放 `rebuild.ps1`、`runtime_hook.py`、`start.bat`。
  - `docs/`：存放 `README.md`、`ARCHITECTURE.md`、`CHANGELOG.md`、`PROJECT_BLUEPRINT.md`、`getting-started.md`。
  - 源码分组（src/）在 `PROJECT_BLUEPRINT.md` 目录树中统一标注：`agent_engine/`、`core/`、`v4/`、`services/`、`tools/`、`workers/`、`ui/`、`resources/`。

### build
- **PyInstaller 路径同步**：`AgentWorkbench.spec` 更新 `datas`（`config/config.yaml`）、`runtime_hooks`（`scripts/runtime_hook.py`）、`icon`（`assets/app.ico`）。
- **打包脚本路径修正**：`scripts/rebuild.ps1` 因自身移动到 `scripts/`，改用 `$projectRoot = Split-Path -Parent $PSScriptRoot` 计算工程根目录，并同步更新 `dist/`、`build/`、`assets/app.ico` 路径。

### fix
- **配置路径解析**：`services/config_service.py` 与 `agent_engine/llm_registry.py` 新增 `_get_app_root()` / `_get_readonly_root()`，打包时读 `_MEIPASS` 内只读副本，写 `exe 同级目录`；相对路径自动解析为绝对路径；`save()` 自动创建 `config/` 子目录。
- **调用点路径同步**：`v4/worker.py`、`v4/main_window.py`、`tests/test_v4_gui_smoke.py`、`tests/integration_test_deepseek_metrics.py`、`scripts/test_llm_direct.py`、`scripts/test_llm_orchestrator_like.py`、`scripts/smoke_craft_flow.py`、`v4/后续接入指南.md` 统一改为 `config/config.yaml` / `docs/README.md`。
- **持久化路径适配**：`v4/repository.py`、`services/activity_service.py`、`services/session_service.py` 默认数据文件定位到 `exe 同级 storage/`，避免打包后找不到数据库路径。

### docs
- **三份核心文档交叉同步**：`docs/README.md` 文件地图、当前状态、启动/打包命令更新为新目录；`docs/PROJECT_BLUEPRINT.md` 目录树重构为 config/assets/scripts/docs/src/tests/storage 分组；`docs/ARCHITECTURE.md`、`docs/getting-started.md`、`blueprints/integration/workspace-context.md` 中的配置与文档链接同步修正。

### test
- 全量 193 项测试通过，零回归。

## v4.0.4-alpha (2026-06-30) — v4 对话 UI 三层折叠结构

### feat
- **对话 UI 三层折叠结构**：`v4/main_window.py` 重写 `SimpleChatArea`，支持阶段面板、工具执行、思考过程、内部命令输出的分级折叠。
  - 阶段面板（第 1 层）始终展开：analyze / execute / verify / archive 对应不同左侧色条与标题。
  - 工具执行摘要（第 2 层）默认收起：`v4/worker.py` 测量工具耗时与成功状态，`WorkerToolEvent` 上报后由 `UIRenderer._build_tool_fold` 生成可折叠块。
  - 思考过程（第 3 层）默认收起：`UIRenderer._build_thinking_fold` 从 AI 回复中提取任务列表并显示完成进度。
  - 内部命令输出（第 3 层）默认收起：工具结果超过 200 字符时折叠，显示行数。
  - 折叠交互：聊天区改用 `QTextBrowser`，拦截 `anchorClicked` 信号，点击折叠头切换展开/收起状态。
- **左栏会话列表精简化**：`v4/conversation_list.py` 每项显示标题（20 字）+ 最后消息预览（40 字）+ 时间；注入 `SessionRepository` 获取最后一条消息内容。

### refactor
- **工具事件路由**：`v4/orchestrator.py` 订阅 `worker.tool` 并转发为 `ui.append_tool`，`v4/ui_renderer.py` 改由 `ui.append_tool` 渲染工具折叠块。

### test
- 新增 `scripts/verify_ui_fold.py`：无 LLM 依赖的 UI 折叠验证脚本，验证 craft 流程下的阶段面板、思考折叠、工具折叠及点击交互。
- 全量 193 项测试通过，零回归。

## v4.0.3-alpha (2026-06-30) — Phase 工作流接入 v4 + PyInstaller 打包适配 + 清理零引用旧代码

### feat
- **V4Worker 内建 PhaseEngine**：craft 模式完整 analyze→confirm→execute→verify→archive 流程。
  - `v4/worker.py` 重构 `_run` 方法，新增 `_run_phased` 驱动 Phase 循环。
  - analyze 阶段解绑工具，强制 LLM 输出文本任务清单。
  - execute 阶段绑定工具执行 ReAct 循环。
  - verify 阶段解绑工具，强制 LLM 输出验证总结。
- **`v4/orchestrator.py` Phase 事件路由**：订阅 `PhaseChangedEvent` / `PhaseConfirmRequiredEvent` / `PhaseCompleteEvent`，处理确认门控与任务终态同步。
- **`v4/event_bus.py` 新增 `unsubscribe`**：支持测试时解绑默认 WorkerManager。

### refactor
- **PyInstaller 打包适配 v4**：更新 `AgentWorkbench.spec` 的 hiddenimports，加入 v4 模块与 agent_engine 引擎；清理已删除的 v2/v3 模块引用。
- **清理零引用 v2/v3 旧代码**：扫描并删除 27 个文件（`ui/main_window.py`、`services/app_context.py`、`agent_engine/classifier.py` 等），移除双轨维护成本。

### fix
- **用户停止任务后状态正确收敛**：`_on_user_stop` 更新任务状态为 `CANCELLED`，并发射 `WorkerDestroyEvent` 终止 Worker，避免 phase 事件覆盖取消状态。
- **测试 StubWorkerManager 注入**：`tests/test_v4_integration.py` 在创建窗口前解绑默认 WorkerManager，避免真实 V4Worker 干扰集成测试。

### test
- 新增 `smoke_craft_deepseek.py`：craft 模式端到端冒烟测试，验证 analyze→confirm→execute→verify→archive 完整流程。
- 全量 193 项测试通过，零回归。

## v4.0.2-alpha (2026-06-30) — v4原生Worker八引擎推理

### feat
- **新建 `v4/worker.py` — V4Worker**：以八引擎（PromptEngine/ContextEngine/ToolEngine/PolicyEngine/MetricsEngine）原生驱动 ReAct 推理循环。
  - 零绞杀者依赖：不禁旧 AgentWorker / AgentOrchestrator / AgentSession。
  - 直接通过 `LLMRegistry.get_llm()` + `bind_tools()` 调用 LLM，自行检测 `tool_calls` 并执行工具循环。
  - 通过 `ToolEngine.call()` 执行工具，支持 Phase 白名单校验。
  - QThread + asyncio 事件循环架构，`submit(user_text)` 外部注入任务。
  - 信号兼容旧 AgentWorker：`chunk_ready` / `result_ready` / `error_occurred`。

### refactor
- **`v4/worker_manager.py`**：`_create_worker` 改用 `V4Worker` 替代 `EngineWorker`；移除 `engines`/`llm_registry` 构造参数（Worker 自行初始化引擎）；`worker.submit(user_text)` 启动任务。
- **`v4/orchestrator.py`**：`_on_queue_task_ready` 从队列获取 `QueuedTask.user_text` 并传入 `WorkerCreateEvent`。
- **`v4/events.py`**：`WorkerCreateEvent` 新增 `user_text: str = ""`。
- **`v4/main_window.py`**：修 `config.load()`→`config.config`；移除 WorkerManager 多余参数。

### test
- 全量 193 项测试通过，零回归。

## v4.0.1-alpha (2026-06-30) — v4 Solo极简UI重构与主题切换

### feat
- **Solo极简两栏UI重构**：重写 `v4/main_window.py` 与 `v4/conversation_list.py`，固定两栏布局（左 280px + 右填充）；移除 IDE 元素（三栏布局/状态栏/容量标签/Phase-工具按钮/资源管理器/终端/文档编辑器）。
  - 左栏：Agent 标题 + 模型下拉 + 主题切换按钮（🌙/☀️）+ 「+ 新任务」按钮 + 极简会话列表（标题 + 预览 + 时间）。
  - 右栏：SimpleChatArea 含会话标题/环境、消息流（用户/AI气泡 + 系统卡片）、多行输入框（Enter发送/Shift+Enter换行）。
- **主题切换系统**：定义 dark/light 两套 `THEMES` 配色字典；左栏顶部 🌙/☀️ 按钮即时切换主题，同步更新左栏/聊天区/输入区所有控件样式；主题状态持久化到 `config.yaml` 的 `app.theme`。
- **延迟创建会话**：点击「+ 新任务」仅重置为草稿窗口（不写 DB），用户发送首条消息后由 `SessionOrchestrator._on_user_send` 创建会话并刷新列表，消除空会话条目。

### test
- 新增 `tests/test_v4_gui_smoke.py::test_theme_toggle_button_switches_and_persists`：验证按钮 emoji 初始值、点击切换后按钮与配置变更、左右栏样式差异化。
- 适配 `tests/test_v4_integration.py` 所有用例：`chat_view` → `chat_area`、`_btn_chat` / `_btn_work` → `new_task_btn`，移除会话图标断言。
- 全量 193 项测试通过。

## v4.0.0-alpha (2026-06-30) — v4 单轨架构：MessageBus + SessionRuntime + 薄 MainWindow

### feat
- **v4 单轨事件总线架构**：新增 `v4/` 目录，实现基于 PySide6 Signal 的强类型 MessageBus，统一跨组件通信。
  - `v4/models.py`：不可变数据模型 `SessionMetadata` / `Message` / `Environment` / `TaskState`。
  - `v4/event_bus.py`：`MessageBus` 支持 namespace / name / session_id 订阅与全量分发。
  - `v4/events.py`：44+ 个事件类，覆盖 user / session / queue / phase / worker / ui 六大命名空间。
  - `v4/repository.py`：基于 SQLite 的会话仓库，消息唯一权威来源；支持置顶排序、环境持久化、任务状态快照。
  - `v4/queue.py`：会话级双槽位 `QueueManager`，控制消息并发，支持取消、自动出队、状态广播。
  - `v4/runtime.py`：`SessionRuntime` 聚合根，内聚本会话队列、Worker 引用、Phase 状态、环境上下文。
  - `v4/worker_manager.py`：系统级 Worker 管理，最多 5 个并发 Worker，超出排队；Worker 绑定会话与项目环境。
  - `v4/orchestrator.py`：`SessionOrchestrator` 统一协调会话生命周期、消息持久化、事件路由。
  - `v4/ui_renderer.py`：唯一 UI 更新者，订阅 `ui.*` 事件驱动 `ChatView`、状态栏、会话列表。
  - `v4/conversation_list.py`：数据驱动会话列表，支持 Chat/Work 类型、置顶、重名、状态徽章。
  - `v4/main_window.py`：薄编排层，只负责 UI 构建与信号路由，所有业务状态委托给 v4 核心。
- **main.py 接入 v4**：入口直接实例化 `v4.main_window.MainWindow`，移除对旧 v2/v3 全局服务的依赖。

### refactor
- **清理 v2/v3 残留**：删除 `ui/managers/*` 下的 `phase_coordinator.py`、`queue_manager.py`、`session_manager.py`、`session_registry.py`、`signal_adapter.py`、`ui_renderer.py`、`worker_manager.py` 及对应测试，避免双轨维护成本。

### test
- 新增 `tests/test_v4_basics.py`、`tests/test_v4_gui_smoke.py`、`tests/test_v4_integration.py` 共 17 个测试，覆盖会话创建、消息持久化、会话切换、队列满/自动出队、停止任务、置顶、重名、并发槽位、重启恢复。
- 全量 192 项测试中 191 项通过；剩余 1 项 `tests/test_explorer_model.py::test_delete_non_empty_folder_fails` 与 v4 无关，系 Python 3.14 / Windows 环境下 `os.rmdir` 对非空目录返回成功但不删除的异常行为，已单独记录待跟进。

## v3.12.0 (2026-06-30) — AI Engine 架构升级：八引擎模块化 + Prompt 增强 + 记忆系统重构

### feat
- **八引擎模块化架构**：`agent_engine/engines/` 下新增 ContextEngine / PromptEngine / InferenceEngine / ToolEngine / PhaseEngine / MemoryEngine / MetricsEngine / PolicyEngine，每个引擎单一职责，通过 `interfaces.py` 抽象接口交互。
  - **ContextEngine**: 上下文组装、4 种压缩策略（滑动窗口/语义/实体保留/混合）、token 估算。
  - **PromptEngine**: System prompt 分层构建（基础+Phase+画像），支持 Analyze/Verify 追加而非覆盖。
  - **InferenceEngine**: LLM 调用、指数退避重试、模型降级（fallback_map）、指标反馈闭环。
  - **ToolEngine**: Phase 级工具白名单、敏感操作确认回调、超时与结果截断。
  - **PhaseEngine**: Mode-Phase 矩阵、插件扩展、硬 checkpoint 校验。
  - **MemoryEngine**: 三层记忆（会话/画像/项目），读取 app_root/.memory/ 注入 prompt。
  - **MetricsEngine**: 指标采集与聚合（avg/sum/max/min）、阈值告警。
  - **PolicyEngine**: dot-path 配置查询、模型选择决策、压缩触发判断。
- **绞杀者模式集成**：`AgentOrchestrator` 新增 `engines` 可选参数，有引擎则委托，无引擎回退旧逻辑。旧代码全部保留，零破坏。

### refactor
- **System prompt 增强**：三模式 prompt 加入角色定位、回复深度、推理链、语气风格要求，从 2-5 行扩展为结构化中文提示。
- **LLM 参数可配置化**：`llm_registry.py` 从 config 读取 temperature/top_p/max_tokens/request_timeout，替代硬编码。
- **User rules 增强**：从 2 条扩展为 6 条，含专业风格 + 项目规范约束。

### fix
- **记忆路径修正**：`SelfContext._build_memory_context()` 改用 `app_root/.memory/` 替代 `project_root/.workbuddy/memory/`。
- **Analyze 阶段不再覆盖基础 prompt**：`set_phase()` 中 analyze/verify 阶段在 base_system_prompt 后追加，不再替换。

### docs
- 新建 `.memory/` 目录（项目级记忆系统），含 MEMORY.md + 每日日志，已加入 `.gitignore`。
- `config.yaml` 新增 `ai_engine` 配置节（context/prompt/inference/tool/phase/memory/metrics）。
- 同步更新 `tests/test_self_context.py` 适配新路径。

## v3.11.4 (2026-06-29) — MainWindow 架构收敛与 UI 修复

### fix
- **新会话按钮只能添加一个标签**：`ui/main_window.py` 的 `_new_conversation` 彻底移除空会话守卫，每次点击都创建新会话，支持无限添加。
- **会话标签名均为"新对话"**：`_send_message_v3` 在首条用户消息后将会话标题与列表项文本更新为消息内容前 20 字；`ui/managers/session_manager.py` 的 `update_title` 补充 `Qt` 导入，修复 `Qt.UserRole` 未定义导致的标题不刷新。
- **Enter 键首次失效**：`_new_conversation`、`_on_session_switch`、`_switch_project` 在切换/新建完成后调用新增的 `_focus_input_field()`，通过 `activateWindow()` + `raise_()` + `QTimer.singleShot(0, setFocus(Qt.OtherFocusReason))` 强制输入框获得焦点，解决首次 Enter 被其他控件吞掉的问题。
- **项目新对话按钮触发 AttributeError**：`ui/widgets/sidebar.py` 补充 `FileTreeWidget.get_root_path()`，修复 `_on_new_conversation_requested` 中诊断日志调用不存在方法导致的崩溃。
- **切换新会话显示无意义接替上下文**：`services/self_context.py` 的 `build_handoff` 增加 `task.phase == "idle"` 守卫，避免任务刚创建、PhaseManager 尚未推进时切换会话显示"🔄 此会话中有未完成的任务 / 当前阶段: idle"。

### refactor
- **MainWindow 架构收敛**：移除 `_pending_queue`、`_worker`、`_workers`、`_phase_manager` 等旧全局状态的活跃使用，统一委托给 `SessionOrchestrator` / `WorkerManager` / `SessionRuntime` 的 v3 事件路径；保留兼容属性供测试引用。

### test
- 全量 214 个单元/集成测试通过。
- 新增 `tests/test_main_window_ui_automation.py` 覆盖三个 UI 修复点。

## v3.11.3 (2026-06-29) — 修复真实运行时 v3 Worker 无响应与状态卡死

### fix
- **WorkerManager 无法解析真实 LLM 导致任务永远卡住**：`ui/managers/worker_manager.py` 的 `_resolve_llm` 之前调用 LLMRegistry 不存在的 `has_provider` / `get`，真实运行时永远返回 `None`，Worker 创建失败、analyze 不执行、队列槽位不释放。现兼容测试 stub（`has_provider` / `get`）与真实注册表（`list_providers` / `get_llm`），并支持首个 provider 回退。
- **Phase 错误后状态机未 reset 导致后续消息 PHASE_BUSY**：`ui/managers/phase_coordinator.py` 错误路径补充 `self._phase_manager.reset()`；`services/session_orchestrator.py` 在 `PhaseFlowCompletedEvent` 处理后统一 reset，确保同一会话可继续发送新消息。
- **空对话守卫导致项目会话永远只有一个"新对话"标签**：`ui/main_window.py` 的 `_new_conversation_requested` 将守卫条件改为"已有空会话且不是当前选中"才复用，否则新建，使每次点击"+ 新对话"都能看到新标签。
- **新建会话后 Orchestrator 当前会话不同步**：`ui/main_window.py` 在创建新会话后调用 `self._orchestrator.switch_session(session_id)`，保证 `SessionOrchestrator._current_session_id` 与 `SessionManager` 一致，避免 UI 过滤与暂停/恢复逻辑错乱。
- **SessionManager 标题更新失效**：`ui/managers/session_manager.py` 的 `update_title` 改为使用 `Qt.UserRole` 获取 session_id，修复会话重命名/首条消息生成标题后 UI 不更新。

### chore
- 新增 `pytest.ini`，将 `testpaths` 限定为 `tests/`，排除 `scripts/test_llm_direct.py` 被 pytest 误识别导致的 fixture 错误。

### test
- 全量 210 个单元/集成测试通过。

## v3.11.2 (2026-06-29) — 修复 v3 Worker 重复创建与文档规范化

### fix
- **Worker 被重复创建导致 analyze 无法触发**：`services/session_orchestrator.py` 移除对 `worker.created` / `worker.execute_required` / `worker.verify_required` 的重复订阅，仅由 `WorkerManager` 统一处理 Worker 输入侧事件，避免 Worker 被覆盖后 `request_analyze` 丢失、消息发送无响应。
- **新 runtime 创建后 UI 状态未同步**：`SessionOrchestrator.create_runtime` 结束处调用 `_emit_queue_ui_state`，确保新会话发送按钮与队列条立即处于正确状态。

### docs
- **README 补全开发环境指引**：明确工作目录 `F:\Agent\agent_workbench`、venv 激活方式、`start.bat` 一键启动、`rebuild.ps1` 打包 + 桌面快捷方式。
- **定位语修正**：MT5 从头版标题移除，聚焦事件总线 + Phase-Driven Workflow + 多会话运行时隔离。
- **新增「AI 进入本工作区须知」**：声明不得盲目运行系统 Python/pip install，文档由存档流程统一维护。
- **同步修正 `docs/getting-started.md`**：对齐 Python 版本（3.14）、补全 cd + venv + activate 步骤、移除不存在的依赖（pandas/numpy）。
- **`PROJECT_BLUEPRINT.md` 存档流程规则对齐**：`git add` 扩展为全文档目录（git add -u + 显式新文档），标签推送改为单标签（禁 --tags）。

### test
- 新增 `tests/integration/test_v3_flow.py::test_worker_created_only_once`：验证 `UserSendEvent` → `WorkerCreatedEvent` 链路中 `AgentWorker` 只实例化一次且 `request_analyze` 只调用一次。
- 全量 210 个单元/集成测试通过。

## v3.11.1 (2026-06-29) — v3 事件流与会话切换修复

### fix
- **Worker 创建后未触发 analyze**：`core/events.py` 的 `WorkerCreatedEvent` 新增 `user_text` 字段；`ui/managers/worker_manager.py` 在 Worker 创建后立即调用 `request_analyze(event.user_text, event.context)`，解决消息发送后无响应。
- **会话切换后输入框/队列条状态未同步**：`services/session_orchestrator.py` 新增 `_emit_queue_ui_state`，在 `switch_session` 时向当前会话发射 `UISetSendEnabledEvent` 与 `UIUpdateQueueBarEvent`。
- **历史会话缺少 runtime**：`services/session_orchestrator.py` 与 `ui/main_window.py` 在切换历史会话时自动创建缺失的 `SessionRuntime`。
- **v3 切换会话误杀后台任务**：`ui/main_window.py` 的 `_abort_current_session_task` 在 v3 路径下仅停止旧路径 Worker，不再调用 `cancel_task`，避免 completed 任务被错误改回 failed。

### refactor
- 移除 `ui/managers/session_manager.py` 中 `current_session` setter 的 `traceback.print_stack` 调试输出。

### docs
- 恢复并完善 `README.md`，补充 v3 文件地图、快速启动、运行测试与 AI 认知加载路径。

### test
- 全量 209 个单元/集成测试通过。

## v3.11.0 (2026-06-29) — v3 架构重构：事件总线、会话运行时与统一协调器

### feat
- **事件总线（MessageBus）**：
  - `core/event_bus.py` 实现基于 Qt Signal 的强类型事件总线，支持 namespace/name 订阅与全量订阅。
  - `core/events.py` 定义全量跨组件事件（user.*、session.*、queue.*、phase.*、worker.*、ui.*）。
- **会话运行时聚合根（SessionRuntime）**：
  - `services/session_runtime.py` 每个会话拥有独立的 `PendingQueue`、`QueueManager`、`PhaseManager`、`PhaseCoordinator`。
  - 支持 Worker / Task 引用绑定、phase_state 快照、流式 chunk 标记。
- **统一协调器（SessionOrchestrator）**：
  - `services/session_orchestrator.py` 作为 v3 单一协调权威，持有所有 `SessionRuntime`。
  - 订阅 MessageBus 事件并路由到正确的运行时，保证任务完成路径唯一、会话切换状态不被覆盖。
- **PhaseCoordinator 解耦**：
  - `ui/managers/phase_coordinator.py` 将 `PhaseManager` 的 Qt 信号转换为带 `session_id` 的 Bus 事件。
  - 错误路径只发送一次系统消息，避免重复；`flow_finished.emit()` 在 `reset()` 之后执行，防止状态机重入。
- **WorkerManager 事件驱动化**：
  - `ui/managers/worker_manager.py` 订阅 `worker.*` 事件，统一创建/停止/复用 Worker，支持 pause/resume。
- **UI 渲染器（UIRenderer）**：
  - `ui/managers/ui_renderer.py` 统一订阅 `ui.*` 事件，按当前会话 ID 过滤并更新 `ChatView`、状态栏、会话列表、队列条等。
- **双槽位队列会话级化**：
  - `services/pending_queue.py` `PendingTask` 新增 `session_id` 字段。
  - `ui/managers/queue_manager.py` 封装会话级队列状态机，支持 `mark_current_done()` 唯一完成路径。
- **TaskService 终态保护**：
  - `services/task_service.py` 的 `complete_task`、`fail_task`、`cancel_task` 均跳过已到达终态的任务，避免覆盖 completed/failed。
  - `_drain_queue` 跳过 stale 队列项，不重新激活终端任务。

### refactor
- **MainWindow 绞杀者瘦身**：
  - `ui/main_window.py` 引入 `UIRenderer`，将用户操作转换为事件发射。
  - 新增 `_send_message_v3()` 路径，通过 `MessageBus` 委托给 `SessionOrchestrator`。
- **AppContext 延迟导入**：
  - `services/app_context.py` 延迟导入 `WorkerManager`，消除 `AppContext -> WorkerManager -> MainWindow -> AppContext` 循环依赖。

### test
- 新增 `tests/integration/test_v3_flow.py`：验证 `UserSendEvent` → `QueueStateChangedEvent` → `PhaseAnalyzeRequiredEvent` → `WorkerCreatedEvent` 完整事件链路。
- 新增 `tests/test_phase_coordinator.py`：`start_flow`、阶段变化、确认、完成、错误路径全覆盖。
- 新增 `tests/test_ui_renderer.py`：当前会话事件透传、非当前会话事件过滤、流式 finalize、Phase UI 事件处理。
- 新增 `tests/test_session_orchestrator.py` 与 `tests/test_session_runtime.py`：运行时生命周期、会话切换不覆盖终态、Phase 完成后状态清理。
- 全部 209 个单元/集成测试通过。

## v3.9.1 (2026-06-29) — 修复 Phase 状态机重入与任务状态回收

### fix
- **Phase 状态机重入**：`agent_engine/phase_manager.py` 中 `flow_finished.emit()` 在 `reset()` 之前执行，导致新任务启动时 PhaseManager 仍处于 ARCHIVE 状态而被 PHASE_BUSY 拦截。已调整为先 `reset()` 再 `emit()`。
- **任务状态未回收**：`MainWindow` 各完成/错误路径改为统一调用 `TaskService.complete_task()`，确保 `task_status_changed` / `task_completed` / `capacity_changed` 信号发射，UI 状态正确刷新。
- **会话切换覆盖已完成状态**：`_abort_current_session_task()` 原本无条件 `cancel_task()`，会把 completed 任务改回 failed。改为仅对 active 状态任务取消，保留已完成状态。
- **会话列表 completed 图标缺失**：`ui/widgets/conversation.py` 的 `update_task_status()` 增加 `"completed": "✅ "`，已完成的任务显示绿色。
- **SessionManager 标题更新失效**：`ui/managers/session_manager.py` 中 `item.data(1)` 改为 `item.data(Qt.UserRole)`，会话重命名后 UI 正确更新。

### refactor
- **Worker/任务资源回收闭路**：`_on_phase_flow_finished`、`_on_phase_error`、`_on_worker_error`、`_on_result`（空结果）路径统一清理 `_workers` 字典和 `WorkerPool` 资源。
- **Managers 模块化准备**：完善 `ui/managers/session_registry.py`、`worker_manager.py`、`phase_coordinator.py`、`queue_manager.py`，为后续 MainWindow 绞杀者模式接入做准备。

### test
- `tests/test_pending_queue.py`：更新 `mark_task_completed` 相关测试用例。
- `tests/test_self_context.py`：补充任务状态上下文测试。

## HANDOFF (2026-06-27) — v3.9.0 模型交接
- 移交模型: Kimi-K2.7-Code
- 交接内容: TaskService + WorkerPool 多任务管理、Session-as-Room 会话隔离、Trae 暗黑主题、底栏状态条、会话状态图标
- 状态: 全部单元测试通过，已推送 origin/main + tag v3.9.0

## v3.9.0 (2026-06-27) — 多任务管理系统 + Trae 暗黑主题

### feat
- **多任务管理系统（TaskService + WorkerPool）**：
  - `services/task_service.py`：任务生命周期管理，`submit_task()` / `on_phase_change()` / `on_tool_start()` / `on_tool_end()` / `mark_completed()`
  - `workers/task_capacity.py`：资源容量控制，最大并发任务/排队任务/工具数
  - `workers/task_queue.py`：FIFO 排队与超时驱逐
  - `workers/worker_pool.py`：Worker 实例池管理
  - `workers/session_task.py`：会话级任务状态跟踪（analyzing → executing → verifying → confirm → completed/failed）
  - `workers/task_worker_adapter.py`：TaskService 与 AgentWorker 之间的适配桥接
  - 相关信号：`task_status_changed` / `capacity_changed` / `task_progress` / `tool_usage_changed` / `task_completed`

- **Session-as-Room (v3.9.0 会话隔离)**：
  - `_on_session_switch()` 实现完整 AB 切换协议：detach(旧) → save phase → switch → clear → load(新) → render → reattach(新)
  - `_make_current_only_guard()` 信号路由守卫：同时校验 Worker 实例和当前会话 ID，防止跨会话消息泄漏
  - `_detach_ui_signals()` / `_attach_ui_signals()` 信号解绑/重绑，Worker 后台继续运行
  - `_save_phase_state()` / `_restore_confirm_ui()` 跨会话保存/恢复 confirm 阶段状态
  - `_append_ai_message()` 按 session_id 独立落盘，后台 Worker 完成时无条件写入 SQLite

- **Trae 暗黑主题**：
  - `resources/themes/trae_dark.qss`：637 行 QSS，覆盖 QMainWindow / QListWidget / QTreeWidget / QTextEdit / QLineEdit / QPushButton / QLabel / QStatusBar / QScrollBar
  - 色值基于 Trae IDE 暗黑风格（深紫灰 #1e1e2e、选中指示器 #89b4fa、绿色 #a6e3a1、黄色 #f9e2af、红色 #f38ba8）
  - `ThemeService` 支持 frozen exe 路径解析（`sys._MEIPASS`），`trae_dark` 设为默认主题

- **底栏容量状态条**：
  - `QLabel` 永久控件显示：🟢 任务:0/3 | ⏳ 排队:0/5 | 🔧 工具:0/12
  - 实时响应 `capacity_changed` / `tool_usage_changed` 信号刷新

- **会话列表状态图标**：
  - `ConversationItem.set_task_status()` 方法，emoji 图标：🟢(运 行) / 🟡(确认) / ⏳(排队) / 🔴(失败)

### fix
- **信号调试管道**：添加 `_log_signal` 装饰器在 emit 端记录信号轨迹，`[RECV]` 日志在 recv 端确认到达
- **ThemeService 路径修复**：exe 环境下 `get_qss()` 使用 `_MEIPASS` 解析相对路径
- **AgentWorkbench.spec**：补充 `trae_dark.qss` 到 PyInstaller datas

### test
- `tests/test_agent_session_integration.py`：Analyze → Execute → Verify 全链路状态隔离 + phase_messages 滑动窗口
- `tests/test_main_window_session_isolation.py`：会话切换信号守卫 / 同 session ID 放行 / 切回非当前会话丢弃

## v3.8.1 (2026-06-27) — 填充架构占位 + 对话气泡与活动面板交互优化

### feat
- **填充 4 个架构占位文件**：
  - `tools/screen.py`：基于 ctypes + gdi32 的屏幕截图与显示器信息，无 Pillow 外部依赖。
  - `ui/overlay.py`：`OverlayWidget` 全局半透明遮罩层，支持淡入淡出动画与进度条。
  - `ui/settings.py`：`SettingsPage` 嵌入式设置页，含 LLM 提供商 / 用户规则 / 界面日志三栏。
  - `ui/tools_panel.py`：`ToolsPanel` 工具开关面板，按分类展示并允许启用/禁用。
- **屏幕工具注册**：`tools/__init__.py` 与 `workers/agent_worker.py` 的 `TOOL_DEFINITIONS` 已注册 `screen_capture`、`screen_info`。
- **活动面板多选增强**：右侧「当前项目 / 全局」列表开启 `ExtendedSelection`，支持 Ctrl+A 全选、Ctrl/Shift 连选、右键「复制选中项」。

### fix
- **对话气泡排版**：`ui/chat_view.py` 改为圆角矩形气泡，用户气泡右对齐、文本统一左对齐，最大宽度 85%，解决多行文本边缘不齐问题。
- **确认卡片排版**：系统/确认消息改为居中卡片样式，任务清单与操作提示使用有序/无序列表工整呈现。

## v3.8.0 (2026-06-27) — MVC 资源管理器、持久化服务与生产修复

### feat
- **MVC 资源管理器**：新增 `ui/models/explorer_tree_model.py`（QAbstractItemModel）、`ui/widgets/explorer_view.py`（QTreeView + emoji 委托），重构 `ui/widgets/explorer.py` 为 Controller，支持懒加载与过滤。
- **PersistenceService**：新增 `services/persistence_service.py`，集中处理 mode/model/UI 状态持久化，替换 `MainWindow` 中分散的 `config_service` 直接访问。
- **MemoryManager 画像 schema**：`config.yaml` 新增 `memory.user_profile_defaults`（含 `schema_version`）；`agent_engine/memory_manager.py` 实现双边版本判断、安全合并与迁移钩子，运行时画像仅补齐缺失字段，不覆盖用户已有值。
- **模式/模型持久化边界测试**：新增空模型列表、损坏 mode 配置自动修复、跨 mode 隔离、空 config 文件启动回退等 4 个高/中高风险边界 case。

### fix
- **依赖补全**：`requirements.txt` 补充 `python-dotenv`，避免新环境 `ModuleNotFoundError`。
- **PyInstaller hiddenimports 对齐**：`AgentWorkbench.spec` 补充 `services.persistence_service`、`services.mcp_service`、`ui.models.explorer_tree_model`、`ui.widgets.explorer_view`、`ui.widgets.explorer`，并修正版本注释为 v3.8。
- **工具定义对齐**：`workers/agent_worker.py` 的 `TOOL_DEFINITIONS` 补齐 `run_python`、`run_powershell`、`run_bash`，与 `tools/__init__.py` 的 `TOOL_MAP` 一一对应，确保 LLM 可见。

### test
- 新增 `tests/test_memory_manager.py`，覆盖默认值初始化、缺失字段补齐、嵌套 dict 不覆盖、版本迁移触发、`schema_version` 防覆盖。
- 补充 `tests/test_persistence_service.py` 4 个模式/模型持久化边界 case。

## v3.7.4 (2026-06-27) — Analyze 阶段强制只读工具

### feat
- **Analyze 阶段强制收集信息**：在 Plan/Craft 模式的 `_build_analyze_prompt` 中新增"工具调用要求"，要求 LLM 在输出 JSON 任务清单前，必须先调用 `read_file`、`list_dir`、`web_fetch` 等只读工具收集必需信息。
- **工具结果截断对齐**：`AgentOrchestrator.TOOL_RESULT_MAX_LEN` 从 3000 调整为 5000，与 `read_file` 工具声明的 "first 5000 chars" 保持一致。

### fix
- **Analyze 摘要保留长度不足**：`AgentSession.run_analyze` 中 `phase_messages` 的 AI 摘要从 800 字符提升到 1500 字符，减少 Verify 阶段信息丢失。

## v3.7.3 (2026-06-26) — 分级超时与持久化路径修复

### feat
- **分级超时控制**：`AgentOrchestrator` 内 LLM 调用与单轮工具调用分别使用 `asyncio.wait_for` 控制，错误码区分为 `LLM_TIMEOUT` / `TOOL_TIMEOUT`，任务总超时仍为 `TASK_TIMEOUT`。
- **模型/模式持久化**：`config.yaml` 新增 `app.last_mode` / `app.last_model`；切换模式时保留当前选择的模型；启动时自动恢复上次模式/模型。

### fix
- **统一持久化路径**：`MainWindow` 统一计算 `_app_storage_dir`，`SessionService`、`MemoryManager`、`ActivityService` 均使用同一目录，避免开发与打包后数据库位置漂移。
- **本地验证使用 venv Python**：`MainWindow._run_local_verification()` 优先通过 `InterpreterService` 选择项目 venv Python 执行语法检查与单元测试。
- **隐藏系统工具控制台窗口**：`tools/system.py` 所有 `subprocess.run/Popen` 统一添加 `CREATE_NO_WINDOW`，避免 AI 调用工具时闪烁 PowerShell/CMD 黑窗。

## v3.7.2 (2026-06-26) — 修复 v3.7.1 打包启动崩溃

### fix
- **窗口标题初始化顺序**：将动态读取 `app.version` 的代码移到 `config_service` 初始化之后，修复 PyInstaller 打包后启动报 `AttributeError: 'MainWindow' object has no attribute 'config_service'`。

## v3.7.1 (2026-06-26) — 修复启动弹窗、历史会话与终端输入

### fix
- **启动隐藏控制台窗口**：`InterpreterService` 解释器版本检测使用 `CREATE_NO_WINDOW`，避免启动时闪烁 PowerShell/CMD 黑窗。
- **历史会话 AI 回复丢失**：在 `_on_phase_result` 中统一持久化 analyze/verify 阶段的 AI 完整回复，重开程序后对话历史完整可读。
- **终端输入框无法编辑**：重构 `TerminalWidget`，使用 `TerminalInput(QLineEdit)` 子类重写 `keyPressEvent`，恢复默认文本编辑并保留 ↑↓ 历史切换。

### feat
- **窗口可持续迭代**：`config.yaml` 新增 `app.version`，主窗口标题动态读取，后续升级无需改代码。
- **活动面板增强**：增加「当前项目 / 全局」说明文字；系统级活动（模式/模型切换、设置更新、解释器切换等）归入全局；列表与详情区右键支持「复制」「全选」。

## v3.7 (2026-06-26) — 终端解释器管理与 AI 上下文感知

### feat
- **终端解释器管理**：新增 `InterpreterService`，自动发现 Python(venv/系统)/PowerShell/CMD/Git Bash，支持手动下拉切换与持久化。
- **终端 UI 增强**：`TerminalWidget` 顶部新增解释器选择下拉框，切换时自动清空终端。
- **解释器上下文注入**：`ContextService` 将当前终端解释器信息注入 prompt，Agent 可知悉可用解释器。
- **解释器专用工具**：`tools/system.py` 新增 `run_python` / `run_powershell` / `run_bash`，AI 可直接调用指定解释器执行命令。

### refactor
- `TerminalWorker` 同时支持 str（shell=True）与 list（shell=False）命令执行。

### fix
- 修复 `workers/terminal_worker.py` 缩进错误导致的模块无法导入问题。
- 修复 `MainWindow` 中 `_project_root` 未初始化就传给 `InterpreterService` 的顺序错误。
- 修复 `TerminalWidget` 创建时未传入 `interpreter_service` 导致下拉框为空的问题。

### test
- 新增 `tests/test_interpreter_service.py`，覆盖解释器发现、选择、命令构造。

## v3.6 (2026-06-26) — Phase-Driven Workflow Engine

### feat
- **阶段驱动工作流**：新增 `PhaseManager`，将每次请求按 Mode 切分为 Analyze → Confirm → Execute → Verify → Archive。
- **Mode × Phase 矩阵**：Ask 只分析/归档；Plan 分析+确认+归档；Craft 完整五阶段。
- **任务清单驱动**：Analyze 阶段让 LLM 输出结构化任务清单，经用户确认后进入 Execute。
- **软硬 Checkpoint 分离**：用户确认、危险命令等为硬门控；语法检查、单元测试为可跳过软提示。
- **Phase 上下文切换**：`ContextService.get_phase_context()` 按阶段注入不同上下文。
- **UI 阶段指示器**：底部状态栏显示 `[分析中]` `[等待确认]` `[执行中 N/M]` `[验证中]` 等阶段标签。
- **确认门控**：对话区显示任务清单 + 「确认执行」/「重新分析」按钮，防止 AI 直接写错代码。
- **Orchestrator.run_phase()**：新增 phase-aware 入口，Analyze/Verify 阶段不绑定工具，输出结构化结果。

### refactor
- `AgentWorker` 增加 `phase` 参数，复用同一 worker 完成不同阶段调用。
- `MainWindow._send_message()` 改为启动 `PhaseManager` 工作流，而非直接创建 worker。

### fix
- 修复 `AgentWorkbench.spec` 文件头 BOM/零宽字符污染。

### test
- 新增 `tests/test_phase_manager.py`，覆盖 Mode×Phase 矩阵、软硬 checkpoint、阶段流转、任务解析。

## v3.5 (2026-06-26) — 推理指标：Token 与响应时间可视化

### feat
- **单轮指标收集**：新增 `MetricsCollector`，基于 `time.perf_counter()` 在 `AgentWorker` 线程内零额外线程地记录 TTFT、总耗时、input/output tokens。
- **AI 气泡指标 footer**：每次 AI 回复气泡右下角显示 `33546tok/34ms` 格式。
- **Orchestrator metrics callback**：`metrics_start` / `metrics_first_token` / `token_usage` 三个 callback 接入指标采集。

### refactor
- `BaseWorker` 新增 `turn_metrics_ready` 信号，将 `TurnMetrics` 从 worker 线程传回主线程。
- `AgentWorker` 转发 chunk 时自动标记首 token 时间；最终 usage_metadata 提取后统一 emit `token_used` + `turn_metrics_ready`。
- `MainWindow._on_token_used` 仅保留持久化，UI 展示与详细日志由 `_on_turn_metrics_ready` 统一处理，状态栏不再显示 token。

### chore
- 新增 `services/metrics_collector.py` 单元测试与 DeepSeek 集成测试。
- 更新 `AgentWorkbench.spec` hiddenimports。

## v3.4 (2026-06-26) — 工作空间上下文感知

### feat
- **项目目录自动检测**：启动时基于当前工作目录或最近活动自动检测 Project Root。
- **右侧文件上下文注入**：活动文件自动提取前 500 字符摘要，随 prompt 注入 Agent。
- **文件工具相对路径解析**：新增 `PathResolver`，基于项目根目录解析相对路径。
- **工作空间上下文服务**：新增 `ContextService`，统一管理项目根目录、活动文档、打开文档、选中项。
- **资源管理器最近项目**：顶部新增「打开文件夹」按钮 + 最近项目下拉切换。

### refactor
- `tools/system.py` 文件工具接入项目根目录解析。
- `AgentWorker` 向系统工具注入当前项目根目录。
- `orchestrator` system prompt 接入 workspace_context。

### chore
- 新增 `tests/test_context_service.py` 单元测试。
- 更新 `AgentWorkbench.spec` hiddenimports。

## v3.3 (2026-06-25) — 精细化：文件预览、纯对话、分栏与活动面板

### feat
- **任意格式文件预览**：文档编辑器支持文本、图片、二进制文件预览；二进制文件显示 MIME、大小、十六进制预览。
- **双击编辑**：文本文件双击编辑区自动进入编辑模式；工具栏显示 编辑 / 取消 / 保存 按钮。
- **纯对话**：新建对话支持「项目新对话」与「纯对话」两种类型；纯对话不绑定任何目录。
- **对话列表分栏**：左侧对话 Tab 分为「当前项目」与「全局」两栏。
- **活动面板**：右侧工作区「日志」标签改为「活动」标签，以中文标题 + 类别 + 时间展示事件；分「当前项目 / 全局」两栏，点击展开详情。
- **结构化活动记录**：新增 `ActivityService`，持久化活动到 JSON。

### refactor
- `WorkspaceWidget` 用 `ActivityWidget` 替换原有日志 QTextEdit。
- `DocumentEditor` 重写文件类型检测与展示逻辑，支持取消编辑恢复原始内容。
- `ConversationListWidget` 重构为双列表分栏结构。

### fix
- 修复模型切换后 `current_model` 未正确持久化到 `config.yaml` 的问题。
- 修复文件打开时产生重复活动记录的问题，并在活动详情中显示文件大小。
- 修复对话列表「当前项目」标题在多次切换目录后无法更新的问题。

### chore
- 文档编辑器新增 `Ctrl+S` 保存、`Esc` 取消编辑快捷键。

## v3.2 (2026-06-25) — 项目目录与对话上下文

### feat
- **项目目录管理**：新增 `ProjectService`，支持按项目目录组织会话，当前目录持久化到 `config.yaml`。
- **资源管理器增强**：文件树顶部新增「打开文件夹」「刷新」按钮、当前路径显示、Ctrl+O 快捷键。
- **目录右键菜单**：树视图右键支持「在当前目录开启新对话」「切换到该文件夹」「在该文件夹下开启新对话」「在右侧打开」。
- **目录下新对话**：新建对话自动关联当前项目目录；切换目录时自动加载该目录下的历史会话。

### refactor
- `SessionService` 新增 `project_path` 字段，支持按目录过滤与会话迁移。
- `MainWindow` 会话初始化改为按当前项目目录加载；移除固定 `default` 会话概念。
- `FileTreeWidget` 支持动态 `set_root_path` 与文件夹/文件点击区分。

## v3.1 (2026-06-25) — 右侧工作区重构

### feat
- **右侧工作区标签页**：新增 `WorkspaceWidget`，顶部集成“终端 / 日志 / 文档”三标签切换。
- **文档编辑器**：新增 `DocumentEditor`，支持文本文件预览、只读/编辑模式切换、保存、二进制文件检测、大文件提示。
- **文件树联动**：左侧资源管理器选中文件后，右侧自动切换到“文档”标签并显示内容。
- **日志自动截断**：日志面板迁移到工作区，保留最大行数限制与自动清理。

### refactor
- `ui/main_window.py` 中央区域仅保留 `ChatView`，底部终端移除，右侧改为 `WorkspaceWidget`。
- 侧边栏“终端”按钮改为聚焦右侧工作区终端标签。
- 日志面板显隐开关改为控制整个右侧工作区可见性。

### fix
- 样式表补充工作区、标签栏、文档编辑器样式，保持 GitHub Dark 主题一致。

## v3 (2026-06-25) — 生产级工具编排、身份系统、UI/UX 全栈修复

### feat
- **工具层级编排**: 17 个工具按 [PRIORITY-1/2/3] 分级，web_fetch 优先于 MT5
- **工具按模式分配**: Ask=11 个(无MT5/破坏性)，Plan=13个(+回测)，Craft=17个(全量)
- **AI 身份声明**: system_prompt 注入 "YOUR IDENTITY"，不再冒充 Claude/GPT
- **系统工具库扩展**: +9个工具(read_file/write_file/list_dir/web_fetch/clipboard/clipboard_write/send_notification/list_processes/kill_process)
- **用户规则系统**: config.yaml user_rules + SettingsDialog 规则编辑标签页
- **桌面快捷方式**: .lnk + app.ico 图标，rebuild.ps1 自动刷新
- **用户画像注入**: user_profile.json → system_prompt 自动合并
- **工具描述标准化**: 全部 17 个工具 description 带 [PRIORITY-X] + 触发词约束

### fix
- **工具调用不执行**: astream() → ainvoke()，tool_calls 正确检测和执行
- **<tool_calls> XML 泄露**: response.content 归零 + 历史消息渲染过滤
- **API Key 回写泄露**: LLMRegistry._save() 自动替换为 ${VAR} 占位符
- **SSL 证书缺失**: certifi/cacert.pem 嵌入 + runtime_hook.py 自动设置
- **Ollama 内存溢出**: OLLAMA_CONTEXT_LENGTH=4096 环境变量
- **gemma2 工具调用异常**: AgentWorker 跳过 bind_tools
- **会话记忆丢失**: LangChain 历史注入(切换/发送/回复三处)
- **中文编码损坏**: sidebar.py QLabel 重写

### refactor
- Act → Craft 重命名(main.py/chat_view/status_indicator/PROJECT_BLUEPRINT)
- ChatView 布局重构: 底部控件栏(模式按钮左/发送右) + 多行输入
- system_prompt 英文化 + 精简(3种模式各 ≤6行)
- PyInstaller excludes: 排除20+未用Qt模块(setuptools/QtWebEngine等)

### chore
- Ollama 环境: OLLAMA_CONTEXT_LENGTH=4096, OLLAMA_NUM_PARALLEL=1
- rebuild.ps1 自动刷新桌面 .lnk 快捷方式

## v0.3 (2026-06-25) — v2生产级重构：模块化架构、8工具实现、流式UI

### feat
- **模块化架构重构**: main.py 从 1546 行拆分为 45 行入口 + 18 个模块文件（ui/widgets/, ui/dialogs/, workers/, services/）
- **流式输出**: AgentWorker 基于 astream() 逐 token 渲染，打字机效果
- **停止生成**: 新增 Stop 按钮 + Escape 快捷键
- **键盘快捷键**: Ctrl+Enter 发送 / Ctrl+L 清空 / Escape 停止
- **外部 QSS 主题**: resources/themes/dark_github.qss，GitHub Dark 深色风格
- **对话持久化**: SQLite 三表（conversations/messages/token_usage），重启不丢失
- **Token 追踪**: 按 provider/model 统计用量，状态栏实时显示
- **终端命令历史**: TerminalWidget 支持 ↑↓ 导航历史命令
- **状态指示器**: StatusIndicator 显示连接状态、当前模式、Token 计数
- **新增工具**: fetch_financial_news（全球财经快讯）、fetch_macro_data（CPI/GDP/PMI）
- **工具升级**: fetch_stock_data（akshare A股/港股/美股）、run_backtest（backtrader 均线策略）、mt5_get_price/place_order（MT5 + Forex API 双通道）
- **模型选择**: QComboBox 下拉 + ⚙ 齿轮按钮进入 SettingsDialog

### refactor
- AgentWorker → workers/agent_worker.py（流式 + 工具调用）
- TerminalWorker → workers/terminal_worker.py
- ChatView → ui/chat_view.py（流式渲染 + 模型下拉 + 快捷键）
- SettingsDialog / ProviderFormDialog → ui/dialogs/settings.py
- SidebarButton / FileTreeWidget → ui/widgets/sidebar.py
- ConversationListWidget → ui/widgets/conversation.py
- TaskListWidget → ui/widgets/tasks.py
- TerminalWidget → ui/widgets/terminal.py
- MainWindow → ui/main_window.py

### chore
- .env 密钥管理：API Keys 从 config.yaml 移至 .env（加入 .gitignore）
- ConfigService：.env 优先 → config.yaml 回退的统一配置层
- SessionService：SQLite 对话持久化服务
- ThemeService：QSS 主题加载与切换服务
- PyInstaller spec 更新：新增 hiddenimports 和 datas 路径

## v0.2 (2026-06-25) — DeepSeek密钥修复与模型选择下拉功能
### fix
- 修复 DeepSeek API key 为占位符导致的 401 认证失败
- 更新 model 名称 deepseek-chat → deepseek-v4-flash（旧名 2026/07/24 废弃）

### feat
- 新增 deepseek-pro provider，支持 V4 Pro 旗舰模型
- 工具栏新增模型下拉选择器（QComboBox），实时切换 LLM 提供商
- 新增模型设置对话框（SettingsDialog），支持添加/编辑/删除提供商
- 新增 ProviderFormDialog，支持填写 name/base_url/api_key/model 并测试连接
- llm_registry 重构：支持运行时增删改查并持久化到 config.yaml
- 模型切换自动持久化到当前模式的 current_model 字段

### refactor
- default_llm → current_model 配置项重命名
- LLMRegistry 支持可写路径，打包模式下写入 exe 同目录 config.yaml

## v0.1 (2026-06-24) — 初始提交AI工作台项目
### feat
- 手动模式切换（Ask / Plan / Act），所有模式共享完整工具权限
- 集成系统命令、管理员提权、股票数据、回测、MT5 等工具
- Trae 风格深色 UI：资源管理器、对话列表、任务列表、终端控制台、Agent 日志
- 敏感操作二次确认机制
- PyInstaller 一键打包脚本 rebuild.ps1
- 配置驱动：config.yaml 管理模式、模型、工具与记忆
