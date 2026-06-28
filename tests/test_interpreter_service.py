import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.interpreter_service import InterpreterService, Interpreter


class TestInterpreterService(unittest.TestCase):
    def setUp(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.svc = InterpreterService(self.project_root)
        self.svc.discover()

    def test_discover_finds_venv_python_first(self):
        """优先发现项目 venv 的 Python"""
        interpreters = self.svc.list_all()
        self.assertTrue(len(interpreters) > 0, "应至少发现一个解释器")
        first = interpreters[0]
        if os.path.exists(os.path.join(self.project_root, "venv", "Scripts", "python.exe")):
            self.assertIn("venv", first.name.lower(), "第一个 Python 应为 venv")
            self.assertEqual(first.type, "python")

    def test_set_current_python_prefers_venv(self):
        """set_current('python') 应优先选择 venv Python"""
        result = self.svc.set_current("python")
        self.assertIsNotNone(result)
        self.assertEqual(result.type, "python")
        if os.path.exists(os.path.join(self.project_root, "venv", "Scripts", "python.exe")):
            self.assertIn("venv", result.name.lower())

    def test_get_shell_command_python(self):
        """Python 解释器命令构造为 [python, '-c', code]"""
        self.svc.set_current("python")
        cmd = self.svc.get_shell_command("print(1)")
        self.assertIsInstance(cmd, list)
        self.assertEqual(cmd[1], "-c")
        self.assertEqual(cmd[2], "print(1)")

    def test_get_shell_command_powershell(self):
        """PowerShell 命令构造为 [powershell, '-Command', command]"""
        found = self.svc.set_current("powershell")
        if not found:
            self.skipTest("未找到 PowerShell")
        cmd = self.svc.get_shell_command("Get-Location")
        self.assertIsInstance(cmd, list)
        self.assertEqual(cmd[1], "-Command")
        self.assertIn("Get-Location", cmd)

    def test_get_shell_command_cmd(self):
        """CMD 命令构造为 [cmd, '/c', command]"""
        found = self.svc.set_current("cmd")
        if not found:
            self.skipTest("未找到 CMD")
        cmd = self.svc.get_shell_command("echo hi")
        self.assertIsInstance(cmd, list)
        self.assertEqual(cmd[1], "/c")
        self.assertIn("echo hi", cmd)

    def test_get_prompt_prefix(self):
        """不同解释器返回对应提示符"""
        self.svc.set_current("python")
        self.assertEqual(self.svc.get_prompt_prefix(), ">>>")
        self.svc.set_current("powershell")
        self.assertEqual(self.svc.get_prompt_prefix(), "PS>")
        self.svc.set_current("cmd")
        self.assertEqual(self.svc.get_prompt_prefix(), ">")
        self.svc.set_current("git_bash")
        self.assertEqual(self.svc.get_prompt_prefix(), "$")

    def test_get_context_string_contains_current(self):
        """get_context_string 应包含当前解释器和可用解释器列表"""
        self.svc.set_current("python")
        ctx = self.svc.get_context_string()
        self.assertIn("当前终端环境", ctx)
        self.assertIn("当前解释器", ctx)
        self.assertIn("可用解释器", ctx)


if __name__ == "__main__":
    unittest.main()
