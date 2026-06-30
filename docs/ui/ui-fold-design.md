# v4 对话 UI 三层折叠结构 — 施工指南

> 阶段: Phase 7（Phase 5+6 完成后执行）
> 改动文件: v4/main_window.py、v4/ui_renderer.py、v4/conversation_list.py
> 原则: 默认收起内部细节，只向用户展示结果面板

---

## 一、三层折叠模型

每条 AI 消息按嵌套层级折叠：

```
┌─────────────────────────────────────────┐
│ ▶ 思考过程  [5/7 已完成]               │  ← 第3层: 默认收起
│   ├ ✓ 修复模型选择器初始化               │
│   ├ ✓ 修复 orchestrator 模型获取         │
│   └ ✓ 运行全量测试                      │
│   [展开后可见完整子任务列表]              │
├─────────────────────────────────────────┤
│ ▶ 工具执行  [3 工具 · 共 2.1s]         │  ← 第2层: 默认收起
│   ├ run_command      0.8s   ✓           │
│   ├ grep_refs        0.3s   ✓           │
│   └ pytest           1.0s   ✓           │
│   [展开后可见命令内容+输出截断前200行]     │
├─────────────────────────────────────────┤
│ ▶ 内部命令输出  [212 行]               │  ← 第3层: 默认收起
│   [展开后可见完整 stdout/stderr]        │
├─────────────────────────────────────────┤
│                                         │
│  📋 分析结果                            │  ← 第1层: 始终展开
│  需要修改 3 个文件:                     │
│  1. v4/events.py — 新增 model 字段       │
│  2. v4/main_window.py — 模型下拉框       │
│  3. v4/orchestrator.py — 使用当前模型     │
│                                         │
│  ⚠ 注意: config.yaml 已存在 model 配置   │
│  无需额外修改                            │
│                                         │
└─────────────────────────────────────────┘
```

### 折叠规则

| 层级 | 内容 | 默认状态 | 触发条件 |
|------|------|:---:|------|
| 第1层 | 阶段面板（分析/计划/报告） | 展开 | 始终 |
| 第2层 | 工具执行摘要 | 收起 | 有 tool_calls 时 |
| 第3层 | 思考过程 + 内部命令 | 收起 | 有子任务列表或命令输出时 |

---

## 二、阶段面板（第1层 — 始终展开）

每个 Phase 对应一个面板：

```
analyze  →  📋 分析结果
confirm  →  📋 分析结果 + [确认] [取消] 按钮
execute  →  📝 执行计划 (步骤列表 + 实时状态)
verify   →  🔍 验证结果
archive  →  ✅ 完成报告
```

### 分析面板示例

```html
<div class="phase-panel analyze">
  <div class="phase-header">📋 分析结果</div>
  <div class="phase-body markdown">
    ## 任务分析
    
    需要修改 3 个文件：
    1. **v4/events.py** — 新增 `model: str = ""` 字段
    2. **v4/main_window.py** — 初始化模型下拉框，持久化选择
    3. **v4/orchestrator.py** — `_on_user_send` 使用 `event.model`
    
    > ⚠ config.yaml 已存在 model 配置，无需额外修改
  </div>
</div>
```

### 执行计划面板示例

```html
<div class="phase-panel execute">
  <div class="phase-header">📝 执行计划</div>
  <div class="phase-body">
    <div class="step done">
      <span class="step-icon">✓</span>
      <span class="step-name">修改 v4/events.py</span>
      <span class="step-detail">新增 model 字段</span>
    </div>
    <div class="step running">
      <span class="step-icon">⟳</span>
      <span class="step-name">修改 v4/main_window.py</span>
      <span class="step-detail">模型下拉框 + 持久化</span>
    </div>
    <div class="step pending">
      <span class="step-icon">○</span>
      <span class="step-name">运行全量测试</span>
      <span class="step-detail">pytest tests/ -v</span>
    </div>
  </div>
</div>
```

### 完成报告面板示例

```html
<div class="phase-panel archive">
  <div class="phase-header">✅ 完成报告</div>
  <div class="phase-body markdown">
    ## 执行摘要
    
    | 文件 | 改动 |
    |------|------|
    | v4/events.py | +1 line |
    | v4/main_window.py | +45 lines |
    | v4/orchestrator.py | +3 lines |
    
    **测试**: 193/193 passed
    
    > 模型选择器已就绪，可以切换 deepseek-pro/deepseek 等模型。
  </div>
</div>
```

---

## 三、工具执行折叠（第2层）

V4Worker 每次 `tool_engine.call()` 后，通过 `WorkerToolEvent` 上报。

ui_renderer 收到 `WorkerToolEvent` 后，生成折叠块而非裸露输出：

```python
# v4/ui_renderer.py — 新增方法
def _handle_worker_tool(self, event):
    if not self._is_current(event):
        return
    tool_html = self._build_tool_fold(event)
    self._chat_view.append_tool_fold(tool_html)

def _build_tool_fold(self, event) -> str:
    """构建工具执行折叠块"""
    name = event.tool_name or "unknown"
    elapsed = event.elapsed_ms or 0
    success = event.success
    icon = "✓" if success else "✗"
    cls = "tool-ok" if success else "tool-fail"
    return f'''
    <div class="tool-entry {cls}">
      <span class="tool-icon">{icon}</span>
      <span class="tool-name">{name}</span>
      <span class="tool-time">{elapsed}ms</span>
      <span class="tool-args-fold" onclick="this.classList.toggle('expanded')">
        ▶ 参数
        <pre class="fold-content">{json.dumps(event.args, indent=2)}</pre>
      </span>
    </div>
    '''
```

### 视觉效果

```
▶ 工具执行  [3 工具 · 共 2.1s]
  ✓ run_command      0.8s   ▶ 参数
  ✓ grep_refs        0.3s   ▶ 参数
  ✓ pytest           1.0s   ▶ 参数
```

点击 ▶ 参数 后展开：

```
  ✓ run_command      0.8s   ▼ 参数
    {
      "command": "pip install requests",
      "timeout": 30
    }
    ── stdout ──
    Successfully installed requests-2.32.3
```

---

## 四、思考过程折叠（第3层）

解析 AI 回复中的「思考过程」标记，生成可折叠的任务列表。

当 AI 回复包含 `Thought` 或 `思考过程` 标记时，提取其中带 `[x]` / `[ ]` / `✓` / `✗` 的子任务行：

```python
# v4/ui_renderer.py
def _build_thinking_fold(self, ai_text: str) -> str:
    """从 AI 回复提取思考过程，生成折叠任务清单"""
    lines = ai_text.split('\n')
    tasks = []
    in_thinking = False
    for line in lines:
        if '思考过程' in line or 'Thought' in line:
            in_thinking = True
            continue
        if in_thinking and (line.strip().startswith(('[x]','[ ]','✓','✗','- [x]','- [ ]'))):
            tasks.append(line.strip())
        if in_thinking and line.strip() == '':
            in_thinking = False
    
    if not tasks:
        return ai_text  # 无思考过程，原样返回
    
    done = sum(1 for t in tasks if any(kw in t for kw in ['[x]','✓','- [x]']))
    total = len(tasks)
    
    task_html = '\n'.join(
        f'<div class="think-task {'done' if any(kw in t for kw in ['[x]','✓','- [x]']) else ''}">'
        f'{t}</div>'
        for t in tasks
    )
    
    return f'''
    <div class="think-fold collapsed">
      <div class="fold-header" onclick="this.parentElement.classList.toggle('collapsed')">
        ▶ 思考过程  [{done}/{total} 已完成]
      </div>
      <div class="fold-body">
        {task_html}
      </div>
    </div>
    '''
```

### 视觉效果

```
▶ 思考过程  [5/7 已完成]
  ✓ Fix task state not updated on error
  ✓ 修复 PhaseManager 状态机 emit/reset 顺序
  ✓ 修复闭路泄露：Worker 资源未完整回收
  ✓ 修复任务完成后 UI 状态未更新
  ✓ 修复新对话按钮延迟创建会话
  ○ Phase 工作流接入 craft 模式
  ○ PyInstaller 打包适配
```

---

## 五、内部命令输出折叠（第3层）

WorkerToolEvent 如果 `result` 超过 200 字符，截断前 200 字符作为预览，完整输出折叠：

```python
def _build_command_output_fold(self, result_text: str, max_preview=200) -> str:
    if len(result_text) <= max_preview:
        return f'<pre class="cmd-output">{result_text}</pre>'
    
    preview = result_text[:max_preview]
    line_count = result_text.count('\n') + 1
    
    return f'''
    <div class="cmd-fold collapsed">
      <div class="fold-header" onclick="this.parentElement.classList.toggle('collapsed')">
        ▶ 内部命令输出  [{line_count} 行]
      </div>
      <pre class="cmd-preview">{preview}...</pre>
      <pre class="fold-content cmd-full">{result_text}</pre>
    </div>
    '''
```

---

## 六、左栏对话列表精简化

`v4/conversation_list.py` 每项只显示 3 个字段：

```
┌──────────────────────────────┐
│ 📌 修复模型选择器初始化         │  ← 标题（最多 20 字）
│    ✓ 193/193 passed           │  ← 最后消息预览（状态 + 摘要）
│    20:15                      │  ← 时间
└──────────────────────────────┘
```

```python
def _create_item(self, metadata: SessionMetadata) -> QListWidgetItem:
    last_msg = self._repo.get_last_message(metadata.session_id)
    preview = last_msg.content[:40] if last_msg else ""
    
    text = (
        f"{metadata.title[:20]}\n"
        f"  {preview}\n"
        f"  {metadata.updated_at.strftime('%H:%M')}"
    )
    item = QListWidgetItem(text)
    item.setData(Qt.UserRole, metadata.session_id)
    return item
```

---

## 七、CSS 折叠组件样式

```css
/* 折叠容器 */
.fold-collapsed .fold-body,
.fold-collapsed .fold-content,
.fold-collapsed .cmd-full { display: none; }

.fold-header {
    cursor: pointer;
    padding: 4px 8px;
    color: #569cd6;
    font-size: 13px;
    user-select: none;
}
.fold-header:hover { background: #2a2d2e; }

/* 阶段面板 */
.phase-panel {
    margin: 8px 0;
    border-radius: 8px;
    overflow: hidden;
}
.phase-panel.analyze { border-left: 3px solid #569cd6; }
.phase-panel.execute { border-left: 3px solid #dcdcaa; }
.phase-panel.archive { border-left: 3px solid #4ec9b0; }
.phase-header {
    padding: 8px 12px;
    font-weight: 600;
    font-size: 14px;
    background: #252526;
}
.phase-body {
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.6;
}

/* 步骤条 */
.step {
    display: flex;
    align-items: center;
    padding: 6px 0;
    gap: 8px;
}
.step.done { color: #4ec9b0; }
.step.running { color: #dcdcaa; }
.step.pending { color: #6a6a6a; }
.step-icon { width: 20px; }

/* 工具条目 */
.tool-entry {
    display: flex;
    align-items: center;
    padding: 3px 8px;
    gap: 8px;
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 12px;
}
.tool-ok { color: #4ec9b0; }
.tool-fail { color: #f14c4c; }
.tool-args-fold {
    cursor: pointer;
    color: #569cd6;
    font-size: 11px;
}

/* 思考任务 */
.think-task {
    padding: 2px 8px;
    font-size: 12px;
    color: #858585;
}
.think-task.done { color: #4ec9b0; }

/* 命令输出 */
.cmd-output, .cmd-preview, .cmd-full {
    font-family: 'Cascadia Code', monospace;
    font-size: 11px;
    padding: 8px;
    margin: 4px 0;
    background: #1e1e1e;
    border-radius: 4px;
    white-space: pre-wrap;
    max-height: 120px;
    overflow-y: auto;
}
.cmd-preview { color: #858585; }
.cmd-full { max-height: 400px; color: #d4d4d4; }
```

---

## 八、实施步骤

1. **v4/ui_renderer.py** — 新增 `_build_thinking_fold()`、`_build_tool_fold()`、`_build_command_output_fold()` 三个方法；在 `_handle_worker_tool` 和 `_handle_append_ai` 中调用
2. **v4/main_window.py** — ChatArea 的 `append_ai` 改为接受结构化数据（phase/tools/thinking）；新增 `append_tool_fold` 方法
3. **v4/conversation_list.py** — `_create_item` 改为三字段极简布局
4. **全量测试** — pytest 确认 193+ 通过
5. **视觉验证** — 发送一条 craft 模式对话，确认三个阶段面板 + 工具折叠 + 思考折叠正确渲染
