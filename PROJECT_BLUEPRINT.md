# Project Blueprint — Agent Workbench UI Template

## 元信息
- **项目**: agent_workbench
- **模块**: ui_template.py
- **版本**: v0.4-alpha
- **存档次数**: 2
- **最后更新**: 2026-07-02

## 技术栈
- **UI 框架**: PySide6 (Qt6)
- **渲染**: QGraphicsView/Scene 像素级 + SVG 图标
- **主题**: 深色/浅色双主题，ThemeManager + C 字典
- **布局**: QSplitter 三栏（左 220px + 中 stretch + 右 400px）

## 目录结构
```
agent_workbench/
├── ui_template.py          # 主 UI 模板（~2100 行）
├── .reference/
│   └── agent-workbench-ui/ # SVG 设计稿（ui-full-dark/light.svg）
├── .handoff/
│   └── HANDOFF.md          # Agent 交接文档
├── CHANGELOG.md
└── PROJECT_BLUEPRINT.md
```

## 最近变更
v0.4-alpha: Tab 背景框恢复 + 输入区可拖拽分隔条 + 分割线防抖处理 + 交接文档 + 窗口边缘 resize 分析

## 历史归档
- v0.4-alpha (2026-07-02): 文档更新 + 标签创建（WorkBuddy 存档）

## Agent 交接记录
| 时间 | Agent | 操作 | 内容 |
|------|-------|------|------|
| 2026-07-02 | WorkBuddy | 存档+移交 | 更新文档至 v0.4-alpha，生成新 HANDOFF.md |
| 2026-07-01 | Trae-CN | 移交 | 窗口边缘 resize 失败分析、输入区拖拽已实现、防抖已实现 |
