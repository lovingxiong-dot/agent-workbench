"""SessionViewModel → NavigationGroup 转换器。"""
from __future__ import annotations

from typing import List

from agent_workbench.presentation.view_models.session import SessionViewModel
from agent_workbench.presentation.shell.protocol import NavigationItem, NavigationGroup


def to_navigation_groups(sessions: List[SessionViewModel]) -> List[NavigationGroup]:
    """SessionViewModel 列表 → NavigationGroup 列表。

    按 group_id 分组，同组会话合并为一个 NavigationGroup。
    """
    groups: dict[str, List[SessionViewModel]] = {}
    for s in sessions:
        gid = s.group_id or "default"
        groups.setdefault(gid, []).append(s)

    return [
        NavigationGroup(
            id=gid,
            title=gid,
            items=[
                NavigationItem(
                    id=s.id,
                    title=s.title,
                    preview=s.preview,
                    kind="session",
                    group=gid,
                    is_active=s.is_active,
                )
                for s in items
            ],
        )
        for gid, items in groups.items()
    ]
