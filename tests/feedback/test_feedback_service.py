"""Tests for FeedbackService — product iteration system foundation."""
from __future__ import annotations

import re

from agent_workbench.feedback import FeedbackService


class TestFeedbackService:
    def test_save_creates_markdown_file(self, tmp_path):
        svc = FeedbackService(feedback_dir=tmp_path)
        path = svc.save("Welcome feels empty", "The home page needs more context.")
        assert path.exists()
        assert path.suffix == ".md"
        assert path.parent == tmp_path
        text = path.read_text(encoding="utf-8")
        assert "# Feedback" in text
        assert "Welcome feels empty" in text
        assert "The home page needs more context." in text

    def test_save_increments_index_per_day(self, tmp_path):
        svc = FeedbackService(feedback_dir=tmp_path)
        p1 = svc.save("First", "content")
        p2 = svc.save("Second", "content")
        assert re.search(r"\d{4}-\d{2}-\d{2}-001\.md$", p1.name)
        assert re.search(r"\d{4}-\d{2}-\d{2}-002\.md$", p2.name)

    def test_save_includes_version(self, tmp_path):
        svc = FeedbackService(feedback_dir=tmp_path)
        path = svc.save("Bug", "It broke.", version="1.0.0")
        text = path.read_text(encoding="utf-8")
        assert "1.0.0" in text

    def test_list_all_sorted(self, tmp_path):
        svc = FeedbackService(feedback_dir=tmp_path)
        p1 = svc.save("A", "a")
        p2 = svc.save("B", "b")
        files = svc.list_all()
        assert files == [p1, p2]
