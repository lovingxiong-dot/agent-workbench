"""CapabilityViewModel → NavigationItem 转换器。

Capability 作为导航项展示（功能页），每个 Capability 映射为一个 NavigationItem。
"""
from __future__ import annotations

from typing import List

from agent_workbench.presentation.view_models.capability import CapabilityViewModel
from agent_workbench.presentation.shell.protocol import NavigationItem


def to_navigation_items(
    capabilities: List[CapabilityViewModel],
) -> List[NavigationItem]:
    """CapabilityViewModel 列表 → NavigationItem 列表。

    每个 Capability 映射为一个导航项：
    - category → NavigationItem.kind
    - id/name/description → id/title/preview
    - is_enabled → is_active
    """
    return [
        NavigationItem(
            id=cap.id,
            title=cap.name,
            preview=cap.description,
            kind=cap.category or "tool",
            is_active=cap.is_enabled,
        )
        for cap in capabilities
    ]
