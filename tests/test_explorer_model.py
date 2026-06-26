"""
Tests for ui.models.explorer_model.ExplorerModel

验证 T3-1/T3-2 ExplorerModel 能力：
- 打开文档列表维护
- 文件系统操作（新建、删除、重命名）
"""
import os
import tempfile
import unittest

from PySide6.QtCore import QCoreApplication

from ui.models.explorer_model import ExplorerModel


def _ensure_qapp():
    app = QCoreApplication.instance()
    if app is None:
        return QCoreApplication([])
    return app


class TestExplorerModelDocuments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _ensure_qapp()

    def setUp(self):
        self.model = ExplorerModel()

    def _norm(self, path: str) -> str:
        return ExplorerModel.normalize_path(path)

    def test_set_open_documents(self):
        docs = [
            {"path": "/a.txt", "is_active": True},
            {"path": "/b.txt", "is_active": False},
        ]
        self.model.set_open_documents(docs)
        self.assertEqual(len(self.model.open_documents), 2)
        self.assertTrue(self.model.open_documents[0]["is_active"])

    def test_open_document_appends(self):
        self.model.open_document("/a.txt")
        self.model.open_document("/b.txt", is_active=True)
        self.assertEqual(len(self.model.open_documents), 2)
        # active 只有一个
        self.assertFalse(self.model.open_documents[0]["is_active"])
        self.assertTrue(self.model.open_documents[1]["is_active"])

    def test_open_existing_document_updates_active(self):
        self.model.open_document("/a.txt", is_active=True)
        self.model.open_document("/b.txt")
        self.model.open_document("/a.txt")  # 重新打开 a，应切换 active
        docs = self.model.open_documents
        self.assertTrue(docs[0]["is_active"])
        self.assertFalse(docs[1]["is_active"])

    def test_activate_document(self):
        self.model.open_document("/a.txt")
        self.model.open_document("/b.txt")
        self.model.activate_document("/a.txt")
        docs = self.model.open_documents
        self.assertTrue(docs[0]["is_active"])
        self.assertFalse(docs[1]["is_active"])

    def test_close_document_removes_it(self):
        self.model.open_document("/a.txt")
        self.model.open_document("/b.txt", is_active=True)
        self.model.close_document("/a.txt")
        paths = [d["path"] for d in self.model.open_documents]
        self.assertEqual(paths, [self._norm("/b.txt")])
        self.assertTrue(self.model.open_documents[0]["is_active"])

    def test_close_active_document_promotes_last(self):
        self.model.open_document("/a.txt", is_active=True)
        self.model.open_document("/b.txt")
        self.model.close_document("/a.txt")
        self.assertTrue(self.model.open_documents[0]["is_active"])


class TestExplorerModelFileOperations(unittest.TestCase):
    """验证 ExplorerModel 文件系统操作方法"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_file(self):
        success, path = ExplorerModel.create_file(self.tmpdir, "new.txt")
        self.assertTrue(success)
        self.assertTrue(os.path.isfile(path))

    def test_create_file_rejects_empty_name(self):
        success, msg = ExplorerModel.create_file(self.tmpdir, "  ")
        self.assertFalse(success)
        self.assertIn("不能为空", msg)

    def test_create_folder(self):
        success, path = ExplorerModel.create_folder(self.tmpdir, "subdir")
        self.assertTrue(success)
        self.assertTrue(os.path.isdir(path))

    def test_delete_file(self):
        target = os.path.join(self.tmpdir, "del.txt")
        open(target, "a").close()
        success, _ = ExplorerModel.delete_path(target)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(target))

    def test_delete_empty_folder(self):
        target = os.path.join(self.tmpdir, "empty_dir")
        os.makedirs(target)
        success, _ = ExplorerModel.delete_path(target)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(target))

    def test_delete_non_empty_folder_fails(self):
        target = os.path.join(self.tmpdir, "nonempty")
        os.makedirs(target)
        open(os.path.join(target, "file.txt"), "a").close()
        success, msg = ExplorerModel.delete_path(target)
        self.assertFalse(success)
        self.assertTrue(os.path.exists(target))

    def test_rename_path(self):
        old = os.path.join(self.tmpdir, "old.txt")
        open(old, "a").close()
        success, new = ExplorerModel.rename_path(old, "new.txt")
        self.assertTrue(success)
        self.assertTrue(os.path.isfile(new))
        self.assertFalse(os.path.exists(old))


if __name__ == "__main__":
    unittest.main()
