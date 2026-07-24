"""presentation/view_models/tool.py — Tool ViewModel。

v6.10.0-alpha Tool Runtime Product Layer。

设计原则：
  ✓ 纯数据，无 Runtime import
  ✓ 零 UI import
  ✓ 与 Foundation Protocol 互补
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ToolViewModel:
    """Tool UI 视图模型。

    字段：
      - tool_id: Tool 唯一标识
      - name: 人类可读名称
      - description: Tool 描述
      - status: UI 展示状态 (enabled / disabled / error)
      - permission: 权限级别 (user / admin)
      - schema: Tool 参数 schema
      - metadata: 扩展展示属性
    """

    tool_id: str
    name: str
    description: str = ""
    status: str = "unknown"
    permission: str = "user"
    schema: Dict[str, object] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema is None:
            self.schema = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolListViewModel:
    """Tool 列表视图模型。"""

    tools: List[ToolViewModel] = field(default_factory=list)
    total_count: int = 0
    enabled_count: int = 0

    def __post_init__(self) -> None:
        if self.tools is None:
            self.tools = []
        self.total_count = len(self.tools)
        self.enabled_count = sum(1 for t in self.tools if t.status == "enabled")

    def get_enabled(self) -> List[ToolViewModel]:
        return [t for t in self.tools if t.status == "enabled"]