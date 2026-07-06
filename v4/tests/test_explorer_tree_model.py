"""
ExplorerTreeModel 单元测试

验证资源管理器树模型的 QAbstractItemModel 接口、懒加载、多根节点结构。
"""
import os
import tempfile
import unittest

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QApplication

from ui.models.explorer_model import ExplorerModel
from ui.models.explorer_tree_model import ExplorerTreeModel, NodeKind

# 确保 QApplication 实例存在
if QApplication.instance() is None:
    _app = QApplication([])


class TestExplorerTreeModel(unittest.TestCase):
    def _make_model(self, project_root: str = "", storage_dir: str = ""):
        base = ExplorerModel(project_root, storage_dir)
        return ExplorerTreeModel(base)

    def test_root_categories(self):
        model = self._make_model()
        root = QModelIndex()
        self.assertEqual(model.rowCount(root), 5)
        names = []
        for row in range(5):
            idx = model.index(row, 0, root)
            names.append(idx.data(Qt.DisplayRole))
            self.assertEqual(idx.data(Qt.UserRole + 1), NodeKind.CATEGORY.name)
        self.assertIn("打开编辑器", names)
        self.assertIn("当前项目", names)
        self.assertIn("最近项目", names)
        self.assertIn("此电脑", names)
        self.assertIn("全局配置", names)

    def test_open_editors(self):
        base = ExplorerModel()
        base.open_document("/tmp/foo.py", is_active=True)
        model = ExplorerTreeModel(base)
        cat = model._category_item(model.CATEGORY_OPEN_EDITORS)
        self.assertEqual(len(cat.children), 1)
        self.assertEqual(cat.children[0].kind, NodeKind.OPEN_DOC)

    def test_current_project_lazy_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "src"))
            open(os.path.join(tmp, "main.py"), "w").close()
            base = ExplorerModel(tmp)
            model = ExplorerTreeModel(base)
            cat = model._category_item(model.CATEGORY_CURRENT_PROJECT)
            self.assertTrue(cat.loaded)
            self.assertEqual(len(cat.children), 2)
            kinds = {c.kind for c in cat.children}
            self.assertEqual(kinds, {NodeKind.DIRECTORY, NodeKind.FILE})

    def test_this_pc_lazy_loading(self):
        base = ExplorerModel()
        model = ExplorerTreeModel(base)
        cat = model._category_item(model.CATEGORY_THIS_PC)
        self.assertFalse(cat.loaded)
        self.assertEqual(len(cat.children), 0)

    def _find_category_index(self, model: ExplorerTreeModel, key: str):
        root = QModelIndex()
        for row in range(model.rowCount(root)):
            idx = model.index(row, 0, root)
            if idx.data(Qt.UserRole + 2).get("category") == key:
                return idx
        return QModelIndex()

    def test_can_fetch_more_and_fetch(self):
        base = ExplorerModel()
        model = ExplorerTreeModel(base)
        cat_index = self._find_category_index(model, model.CATEGORY_THIS_PC)
        self.assertTrue(cat_index.isValid())
        self.assertTrue(model.canFetchMore(cat_index))
        model.fetchMore(cat_index)
        self.assertTrue(model._category_item(model.CATEGORY_THIS_PC).loaded)

    def test_parent_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "a.py"), "w").close()
            base = ExplorerModel(tmp)
            model = ExplorerTreeModel(base)
            cat = model._category_item(model.CATEGORY_CURRENT_PROJECT)
            file_item = cat.children[0]
            file_index = model.createIndex(0, 0, file_item)
            parent_index = model.parent(file_index)
            self.assertTrue(parent_index.isValid())
            self.assertEqual(parent_index.data(Qt.UserRole + 2).get("category"), model.CATEGORY_CURRENT_PROJECT)

    def test_recent_projects(self):
        base = ExplorerModel()
        base.set_recent_projects([{"path": "/tmp/proj"}])
        model = ExplorerTreeModel(base)
        cat = model._category_item(model.CATEGORY_RECENT_PROJECTS)
        self.assertEqual(len(cat.children), 1)
        self.assertEqual(cat.children[0].kind, NodeKind.RECENT_ITEM)

    def test_global_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "config.yaml"), "w").close()
            base = ExplorerModel("", tmp)
            model = ExplorerTreeModel(base)
            cat = model._category_item(model.CATEGORY_GLOBAL_CONFIG)
            self.assertEqual(len(cat.children), 1)
            self.assertEqual(cat.children[0].kind, NodeKind.CONFIG_ITEM)
