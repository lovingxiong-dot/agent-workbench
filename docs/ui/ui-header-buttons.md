# v4 会话区右上角三键操作 — 施工指南

> 阶段: Phase 7 — UI 精细化（与 ui-fold-design.md 同级）
> 改动文件: `v4/ui_renderer.py`、`v4/main_window.py`、`v4/conversation_list.py`
> 原则: 精确定位、矢量图标、三态完整，AI 可直接按坐标施工

---

## 一、三键总览

会话区标题栏（x=221-623, h=40, bg=#1a1a2e 深色 / #f8f9fa 浅色）右侧放置三个操作键：

| # | 键名 | Icon | 功能 | 快捷键 |
|---|------|------|------|--------|
| 1 | 搜索 | 🔍 | 在当前会话内搜索文本 | Ctrl+F |
| 2 | 更多 | ⋯ | 打开上下文菜单（导出/设置/新窗口） | — |
| 3 | 展开 | ⤡ | 收起左右面板，全屏对话区 | Ctrl+B |

---

## 二、精确坐标（深色 + 浅色统一）

### 2.1 标题栏容器

```
x = 0    (组件内坐标)
y = 0
w = 402
h = 40
```

### 2.2 分隔线

```
深色: <line x1="553" y1="8" x2="553" y2="32" stroke="#2a2a4a" stroke-width="1"/>
浅色: <line x1="553" y1="8" x2="553" y2="32" stroke="#dee2e6" stroke-width="1"/>
```

### 2.3 三个按钮（从左到右）

每个按钮均为 18×22 圆角矩形，y=8, h=24, rx=4。间距 4px。

#### 搜索键

| 属性 | 深色 | 浅色 |
|------|------|------|
| rect x | 559 | 559 |
| rect y | 8 | 8 |
| rect w | 18 | 18 |
| rect h | 22 | 22 |
| rect rx | 4 | 4 |
| bg normal | #2a2a4a | #e9ecef |
| bg hover | #3a3a5a | #dee2e6 |
| bg active | #0f3460 | #ced4da |
| icon stroke | #a0a0b0 | #6c757d |
| icon stroke-width | 1.5 | 1.5 |
| tooltip | "搜索 (Ctrl+F)" | "搜索 (Ctrl+F)" |

**Icon 路径 (放大镜)**

```
<path d="M 564 14 a 3.5 3.5 0 1 0 0 7 a 3.5 3.5 0 1 0 0 -7
         M 567 21 L 570 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"/>
```

#### 更多键

| 属性 | 深色 | 浅色 |
|------|------|------|
| rect x | 581 | 581 |
| rect y | 8 | 8 |
| rect w | 18 | 18 |
| rect h | 22 | 22 |
| rect rx | 4 | 4 |
| bg normal | #2a2a4a | #e9ecef |
| bg hover | #3a3a5a | #dee2e6 |
| bg active | #0f3460 | #ced4da |
| icon stroke | #a0a0b0 | #6c757d |
| icon stroke-width | 1.5 | 1.5 |
| tooltip | "更多操作" | "更多操作" |

**Icon 路径 (三点)**

```
<circle cx="586" cy="15" r="1.2" fill="currentColor"/>
<circle cx="590" cy="15" r="1.2" fill="currentColor"/>
<circle cx="594" cy="15" r="1.2" fill="currentColor"/>
```

#### 展开键

| 属性 | 深色 | 浅色 |
|------|------|------|
| rect x | 603 | 603 |
| rect y | 8 | 8 |
| rect w | 18 | 18 |
| rect h | 22 | 22 |
| rect rx | 4 | 4 |
| bg normal | #2a2a4a | #e9ecef |
| bg hover | #3a3a5a | #dee2e6 |
| bg active | #0f3460 | #ced4da |
| icon stroke | #a0a0b0 | #6c757d |
| icon stroke-width | 1.5 | 1.5 |
| tooltip | "展开/收起面板 (Ctrl+B)" | "展开/收起面板 (Ctrl+B)" |

**Icon 路径 (对角箭头 — 展开态)**

```
<path d="M 609 12 L 614 12 L 614 17
         M 609 18 L 614 18 L 614 13"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"/>
```

---

## 三、完整 SVG 标题栏模板（可直接复制到布局中）

### 深色

```xml
<!-- ===== 标题栏 ===== -->
<text x="240" y="16" fill="#e0e0e0" font-size="12" font-weight="500">v4 架构升级</text>
<text x="240" y="30" fill="#6a6a8a" font-size="10">F:\Agent\agent_workbench</text>

<!-- 分隔线 -->
<line x1="553" y1="8" x2="553" y2="32" stroke="#2a2a4a" stroke-width="1"/>

<!-- 搜索 -->
<rect x="559" y="8" width="18" height="22" rx="4" fill="#2a2a4a"/>
<path d="M 564 14 a 3.5 3.5 0 1 0 0 7 a 3.5 3.5 0 1 0 0 -7 M 567 21 L 570 24" fill="none" stroke="#a0a0b0" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>

<!-- 更多 -->
<rect x="581" y="8" width="18" height="22" rx="4" fill="#2a2a4a"/>
<circle cx="586" cy="15" r="1.2" fill="#a0a0b0"/>
<circle cx="590" cy="15" r="1.2" fill="#a0a0b0"/>
<circle cx="594" cy="15" r="1.2" fill="#a0a0b0"/>

<!-- 展开 -->
<rect x="603" y="8" width="18" height="22" rx="4" fill="#2a2a4a"/>
<path d="M 609 12 L 614 12 L 614 17 M 609 18 L 614 18 L 614 13" fill="none" stroke="#a0a0b0" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>

<line x1="221" y1="40" x2="623" y2="40" stroke="#2a2a4a" stroke-width="0.5"/>
```

### 浅色

```xml
<!-- ===== 标题栏 ===== -->
<text x="240" y="16" fill="#212529" font-size="12" font-weight="500">v4 架构升级</text>
<text x="240" y="30" fill="#adb5bd" font-size="10">F:\Agent\agent_workbench</text>

<!-- 分隔线 -->
<line x1="553" y1="8" x2="553" y2="32" stroke="#dee2e6" stroke-width="1"/>

<!-- 搜索 -->
<rect x="559" y="8" width="18" height="22" rx="4" fill="#e9ecef"/>
<path d="M 564 14 a 3.5 3.5 0 1 0 0 7 a 3.5 3.5 0 1 0 0 -7 M 567 21 L 570 24" fill="none" stroke="#6c757d" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>

<!-- 更多 -->
<rect x="581" y="8" width="18" height="22" rx="4" fill="#e9ecef"/>
<circle cx="586" cy="15" r="1.2" fill="#6c757d"/>
<circle cx="590" cy="15" r="1.2" fill="#6c757d"/>
<circle cx="594" cy="15" r="1.2" fill="#6c757d"/>

<!-- 展开 -->
<rect x="603" y="8" width="18" height="22" rx="4" fill="#e9ecef"/>
<path d="M 609 12 L 614 12 L 614 17 M 609 18 L 614 18 L 614 13" fill="none" stroke="#6c757d" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>

<line x1="221" y1="40" x2="623" y2="40" stroke="#dee2e6" stroke-width="0.5"/>
```

---

## 四、交互行为规范

### 4.1 搜索键
- **点击**: 在标题栏下方弹出搜索条（高 28px，y=42, w=380, x=229）；输入框 + 上/下箭头 + 关闭 ×
- **输入**: 实时过滤当前会话中的消息，高亮匹配文本
- **Enter**: 跳转到下一条匹配
- **Shift+Enter**: 上一条
- **Esc / 点击 ×**: 关闭搜索条

### 4.2 更多键
- **点击**: 在按钮正下方弹出菜单（宽 160px）
- 菜单项:
  - 导出会话 (📥)
  - 复制链接 (🔗)
  - 会话设置 (⚙)
  - 开发者工具 (</>)
- **点击外部 / Esc**: 关闭菜单

### 4.3 展开键
- **点击**: 切换左右面板可见性
- **收起时**: 左+右面板隐藏，对话区扩到全宽 0-1024
- **展开时**: 恢复三面板布局
- **图标变化**: 展开态 → 对角外箭头；收起态 → 对角内箭头（方向相反）
- **收起态 icon**:
```
<path d="M 611 12 L 606 12 L 606 17
         M 611 18 L 606 18 L 606 13"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"/>
```

---

## 五、CSS 样式

```css
/* 标题栏按钮 */
.header-btn {
    width: 20px;
    height: 22px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s ease;
}
.header-btn { background: #2a2a4a; }
.header-btn:hover { background: #3a3a5a; }
.header-btn:active { background: #0f3460; }

/* 浅色 */
.theme-light .header-btn { background: #e9ecef; }
.theme-light .header-btn:hover { background: #dee2e6; }
.theme-light .header-btn:active { background: #ced4da; }

/* 搜索条 */
.search-bar {
    position: absolute;
    top: 42px;
    left: 8px;
    right: 8px;
    height: 28px;
    background: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    display: flex;
    align-items: center;
    padding: 0 8px;
    gap: 8px;
    z-index: 10;
}
.search-bar input {
    flex: 1;
    background: transparent;
    border: none;
    color: #e0e0e0;
    font-size: 12px;
    outline: none;
}
.search-bar input::placeholder { color: #6a6a8a; }

/* 更多菜单 */
.more-menu {
    position: absolute;
    top: 36px;
    right: 25px;  /* 对齐更多按钮 */
    width: 160px;
    background: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 4px;
    z-index: 20;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.more-menu-item {
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
    color: #a0a0b0;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
}
.more-menu-item:hover {
    background: #2a2a4a;
    color: #e0e0e0;
}
.more-menu-item .shortcut {
    margin-left: auto;
    color: #6a6a8a;
    font-size: 10px;
}
```

---

## 六、Python 实现接口

```python
# v4/ui_renderer.py — 标题栏按钮管理

class HeaderToolbar:
    """右上角三键控制器"""
    
    BUTTON_CONFIG = {
        "search": {
            "tooltip": "搜索 (Ctrl+F)",
            "shortcut": "Ctrl+F",
        },
        "more": {
            "tooltip": "更多操作",
            "shortcut": None,
        },
        "expand": {
            "tooltip_expanded": "展开/收起面板 (Ctrl+B)",
            "tooltip_collapsed": "展开/收起面板 (Ctrl+B)",
            "shortcut": "Ctrl+B",
        },
    }
    
    def on_search_click(self):
        """显示/隐藏搜索条"""
        pass
    
    def on_more_click(self):
        """弹出更多菜单"""
        pass
    
    def on_expand_click(self):
        """切换面板可见性"""
        # 触发 MainWindow.toggle_panels()
        pass


# v4/main_window.py — 面板切换

def toggle_panels(self):
    """切换左/右面板可见性，对话区全屏"""
    if self.left_panel.isVisible():
        self.left_panel.hide()
        self.right_panel.hide()
        self._header.update_expand_icon(collapsed=True)
    else:
        self.left_panel.show()
        self.right_panel.show()
        self._header.update_expand_icon(collapsed=False)
```

---

## 七、施工检查清单

- [ ] **SVG 预览**: ui-full-dark.svg / ui-full-light.svg 中三个按钮均可见、坐标无遮挡
- [ ] **三态颜色**: normal / hover / active 色值正确
- [ ] **Icon 矢量**: 放大镜、三点、对角箭头均使用 SVG path 而非 Unicode
- [ ] **搜索条**: 弹出/关闭动画流畅，上下跳转可用
- [ ] **更多菜单**: 四项菜单均可点击，点击外部关闭
- [ ] **展开/收起**: 面板切换无闪烁，图标随状态变化
- [ ] **键盘快捷键**: Ctrl+F 搜索、Ctrl+B 展开、Esc 关闭
- [ ] **双主题**: 深色/浅色 CSS 变量正确覆盖
