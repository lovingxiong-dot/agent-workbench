"""
测试 ContextService 和 PathResolver
"""
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.path_resolver import resolve_path
from services.context_service import ContextService


class PathResolverTest(unittest.TestCase):
    def test_absolute_path(self):
        self.assertEqual(
            resolve_path("C:/Users/test/doc.txt", "D:/projects"),
            "C:\\Users\\test\\doc.txt",
        )

    def test_relative_path(self):
        self.assertEqual(
            resolve_path("src/main.py", "D:/projects"),
            "D:\\projects\\src\\main.py",
        )

    def test_empty_path_returns_project_root(self):
        self.assertEqual(resolve_path("", "D:/projects"), "D:\\projects")
        self.assertEqual(resolve_path("   ", "D:/projects"), "D:\\projects")

    def test_parent_relative(self):
        self.assertEqual(
            resolve_path("../config.yaml", "D:/projects/app"),
            "D:\\projects\\config.yaml",
        )

    def test_no_project_root_uses_cwd(self):
        result = resolve_path("relative.txt", "")
        self.assertEqual(result, os.path.normpath(os.path.join(os.getcwd(), "relative.txt")))


class ContextServiceTest(unittest.TestCase):
    def setUp(self):
        self.project_service = MagicMock()
        self.project_service.normalize_path = lambda p: os.path.normpath(os.path.abspath(p)) if p else ""
        self.ctx = ContextService(self.project_service)

    def test_set_project_root(self):
        self.ctx.set_project_root("D:/projects/app")
        self.assertEqual(self.ctx.get_project_root(), "D:\\projects\\app")

    def test_active_document_in_prompt(self):
        self.ctx.set_project_root("D:/projects/app")
        self.ctx.set_active_document("D:/projects/app/readme.md", "# Hello\nWorld", 100)
        prompt = self.ctx.build_prompt_context()
        self.assertIn("项目目录: D:\\projects\\app", prompt)
        self.assertIn("活动文件: readme.md", prompt)
        self.assertIn("# Hello", prompt)

    def test_selected_paths_in_prompt(self):
        self.ctx.set_project_root("D:/projects/app")
        self.ctx.set_selected_paths(["D:/projects/app/src", "D:/projects/app/main.py"])
        prompt = self.ctx.build_prompt_context()
        self.assertIn("选中项: src, main.py", prompt)

    def test_resolve_path(self):
        self.ctx.set_project_root("D:/projects/app")
        self.assertEqual(
            self.ctx.resolve_path("config.yaml"),
            "D:\\projects\\app\\config.yaml",
        )

    def test_clear_context_on_project_change(self):
        self.ctx.set_project_root("D:/projects/app")
        self.ctx.set_active_document("D:/projects/app/readme.md", "content", 10)
        self.ctx.set_project_root("D:/other")
        self.assertIsNone(self.ctx.get_active_document())
        self.assertEqual(len(self.ctx.get_selected_paths()), 0)

    def test_activate_preserves_preview_and_size(self):
        """激活文档时若未提供 preview/size，应保留首次打开时的值"""
        self.ctx.set_project_root("D:/projects/app")
        self.ctx.set_active_document("D:/projects/app/readme.md", "# Hello", 100)
        self.ctx.set_active_document("D:/projects/app/readme.md")  # 仅激活
        active = self.ctx.get_active_document()
        self.assertEqual(active.preview, "# Hello")
        self.assertEqual(active.size, 100)

    def test_rename_open_document(self):
        """重命名后应同步更新打开文档列表中的路径"""
        self.ctx.set_project_root("D:/projects/app")
        self.ctx.set_active_document("D:/projects/app/readme.md", "# Hello", 100)
        self.ctx.rename_open_document("D:/projects/app/readme.md", "D:/projects/app/README.md")
        active = self.ctx.get_active_document()
        self.assertEqual(active.path, "D:\\projects\\app\\README.md")
        self.assertEqual(self.ctx.get_open_documents()[0].path, "D:\\projects\\app\\README.md")


if __name__ == "__main__":
    unittest.main()
