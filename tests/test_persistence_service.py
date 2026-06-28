"""
PersistenceService 单元测试

验证 mode / model 持久化、启动回退、settings 变更回退等边界行为。
"""
import os
import tempfile
import unittest

from services.config_service import ConfigService
from services.persistence_service import PersistenceService


class TestPersistenceService(unittest.TestCase):
    def _make_service(self, config: dict = None):
        fd, path = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        self._temp_paths.append(path)
        cfg = ConfigService(path, writable_path=path)
        if cfg.config is None:
            cfg.config = {}
        if config:
            cfg.config.update(config)
            cfg.save()
            cfg.reload()
            if cfg.config is None:
                cfg.config = {}
        return PersistenceService(cfg), cfg

    def setUp(self):
        self._temp_paths = []

    def tearDown(self):
        for path in self._temp_paths:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def test_save_mode(self):
        svc, cfg = self._make_service()
        svc.save_mode("craft")
        self.assertEqual(cfg.get("app.last_mode"), "craft")

    def test_save_model(self):
        svc, cfg = self._make_service()
        svc.save_model("craft", "deepseek")
        self.assertEqual(cfg.get("app.last_model"), "deepseek")
        self.assertEqual(cfg.get("manual_modes.craft.current_model"), "deepseek")

    def test_resolve_start_mode_model_valid(self):
        svc, _ = self._make_service({
            "app": {"last_mode": "plan", "last_model": "deepseek"},
        })
        mode, model = svc.resolve_start_mode_model(
            ["ask", "plan", "craft"],
            ["tool-agent", "deepseek"],
        )
        self.assertEqual(mode, "plan")
        self.assertEqual(model, "deepseek")

    def test_resolve_start_mode_model_fallback(self):
        svc, _ = self._make_service({
            "app": {"last_mode": "invalid_mode", "last_model": "invalid_model"},
        })
        mode, model = svc.resolve_start_mode_model(
            ["ask", "plan", "craft"],
            ["tool-agent", "deepseek"],
        )
        self.assertEqual(mode, "ask")
        self.assertEqual(model, "tool-agent")

    def test_get_mode_model(self):
        svc, _ = self._make_service({
            "manual_modes": {
                "ask": {"current_model": "tool-agent"},
                "craft": {"current_model": "deepseek"},
            },
        })
        self.assertEqual(svc.get_mode_model("craft"), "deepseek")
        self.assertIsNone(svc.get_mode_model("plan"))

    def test_snapshot_app_state(self):
        svc, cfg = self._make_service()
        svc.snapshot_app_state({"last_mode": "ask", "last_model": "tool-agent"})
        self.assertEqual(cfg.get("app.last_mode"), "ask")
        self.assertEqual(cfg.get("app.last_model"), "tool-agent")

    def test_update_nested_preserves_siblings(self):
        svc, cfg = self._make_service({
            "ui": {"log_panel": {"visible": True, "max_lines": 500}},
        })
        svc.update_nested("ui.log_panel", {"visible": False})
        self.assertEqual(cfg.get("ui.log_panel.visible"), False)
        self.assertEqual(cfg.get("ui.log_panel.max_lines"), 500)

    def test_resolve_start_fallback_when_available_models_empty(self):
        """可用模型列表为空时，必须回退到 defaults[1]，不能抛异常。"""
        svc, _ = self._make_service({
            "app": {"last_mode": "ask", "last_model": "deepseek"},
        })
        mode, model = svc.resolve_start_mode_model(
            ["ask", "plan", "craft"],
            [],
            defaults=("ask", "tool-agent"),
        )
        self.assertEqual(mode, "ask")
        self.assertEqual(model, "tool-agent")

    def test_save_model_repairs_broken_mode_config(self):
        """manual_modes.<mode> 被误编辑为 string 时，save_model 应自动修复为 dict。"""
        svc, cfg = self._make_service({
            "manual_modes": {"craft": "broken"},
        })
        svc.save_model("craft", "deepseek")
        self.assertEqual(cfg.get("manual_modes.craft.current_model"), "deepseek")
        self.assertIsInstance(cfg.config["manual_modes"]["craft"], dict)

    def test_save_model_isolates_modes(self):
        """保存 craft 的模型不应覆盖 ask 的模型。"""
        svc, cfg = self._make_service({
            "manual_modes": {
                "ask": {"current_model": "tool-agent"},
                "craft": {"current_model": "deepseek"},
            },
        })
        svc.save_model("craft", "deepseek-pro")
        self.assertEqual(cfg.get("manual_modes.craft.current_model"), "deepseek-pro")
        self.assertEqual(cfg.get("manual_modes.ask.current_model"), "tool-agent")

    def test_resolve_start_with_empty_config_file(self):
        """config.yaml 为空文件时，ConfigService.config 为 None，启动回退应优雅处理。"""
        fd, path = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        self._temp_paths.append(path)

        cfg = ConfigService(path, writable_path=path)
        # 模拟空 YAML 导致 config 为 None 的真实场景
        self.assertIsNone(cfg.config)

        svc = PersistenceService(cfg)
        mode, model = svc.resolve_start_mode_model(
            ["ask", "plan", "craft"],
            ["tool-agent", "deepseek"],
            defaults=("ask", "tool-agent"),
        )
        self.assertEqual(mode, "ask")
        self.assertEqual(model, "tool-agent")
