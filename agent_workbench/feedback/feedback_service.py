"""agent_workbench/feedback/feedback_service.py — Feedback 收集服务。

职责：
- 将用户反馈保存为 `feedback/YYYY-MM-DD-NNN.md`。
- 自动按日期递增序号。
- 文件头部包含结构化元数据，便于后续 Trae 批量读取与分析。
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


class FeedbackService:
    """管理 Feedback 文件的创建与读取。"""

    def __init__(self, feedback_dir: str | Path | None = None) -> None:
        self._dir = Path(feedback_dir) if feedback_dir else Path.cwd() / "feedback"
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, title: str, content: str, version: str = "") -> Path:
        """保存一条反馈，返回生成的文件路径。

        参数：
            title: 反馈标题（单行）。
            content: 反馈正文（多行）。
            version: 当前产品版本，可选。

        返回：
            生成的 markdown 文件路径，格式为 feedback/YYYY-MM-DD-NNN.md。
        """
        today = datetime.now().strftime("%Y-%m-%d")
        next_index = self._next_index(today)
        filename = f"{today}-{next_index:03d}.md"
        path = self._dir / filename

        body = self._render(title, content, version)
        path.write_text(body, encoding="utf-8")
        return path

    def list_all(self) -> list[Path]:
        """返回所有反馈文件，按文件名排序。"""
        if not self._dir.exists():
            return []
        return sorted(p for p in self._dir.iterdir() if p.suffix == ".md")

    def _next_index(self, date_prefix: str) -> int:
        """计算当天下一个可用序号。"""
        pattern = re.compile(re.escape(date_prefix) + r"-(\d{3})\.md$")
        max_index = 0
        for path in self._dir.iterdir():
            match = pattern.match(path.name)
            if match:
                max_index = max(max_index, int(match.group(1)))
        return max_index + 1

    @staticmethod
    def _render(title: str, content: str, version: str) -> str:
        """渲染 Feedback markdown 内容。"""
        now = datetime.now().isoformat(timespec="seconds")
        lines = [
            "# Feedback",
            "",
            f"- **Title**: {title}",
            f"- **Time**: {now}",
        ]
        if version:
            lines.append(f"- **Version**: {version}")
        lines.extend([
            "",
            "## Content",
            "",
            content,
            "",
        ])
        return "\n".join(lines)
