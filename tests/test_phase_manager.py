"""
Tests for agent_engine.phase_manager
"""
import unittest

from PySide6.QtCore import QCoreApplication

from agent_engine.phase_manager import PhaseManager, Phase, TaskItem


class TestPhaseManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Qt 信号需要 QCoreApplication
        cls.app = QCoreApplication([])

    def setUp(self):
        self.pm = PhaseManager()
        self.events = []
        self.pm.phase_changed.connect(lambda p, m: self.events.append(("phase_changed", p, m)))
        self.pm.analyze_required.connect(lambda u, m, c: self.events.append(("analyze_required", u, m, c)))
        self.pm.confirm_required.connect(lambda t: self.events.append(("confirm_required", len(t))))
        self.pm.execute_required.connect(lambda t: self.events.append(("execute_required", len(t))))
        self.pm.verify_required.connect(lambda r, m: self.events.append(("verify_required", len(r), m)))
        self.pm.archive_required.connect(lambda m: self.events.append(("archive_required", m)))
        self.pm.flow_finished.connect(lambda s, msg: self.events.append(("flow_finished", s, msg)))
        self.pm.error_occurred.connect(lambda c, d: self.events.append(("error_occurred", c, d)))

    def test_initial_state_is_idle(self):
        self.assertEqual(self.pm.current_phase(), "idle")

    def test_start_emits_analyze_required_for_ask(self):
        self.pm.start("hello", "ask", "ctx")
        self.assertEqual(self.pm.current_phase(), "analyze")
        self.assertIn(("analyze_required", "hello", "ask", "ctx"), self.events)

    def test_start_emits_analyze_required_for_plan(self):
        self.pm.start("plan something", "plan")
        self.assertEqual(self.pm.current_phase(), "analyze")

    def test_start_emits_analyze_required_for_craft(self):
        self.pm.start("do something", "craft")
        self.assertEqual(self.pm.current_phase(), "analyze")

    def test_ask_flow_analyze_to_archive(self):
        self.pm.start("hello", "ask")
        self.pm.on_analyze_complete([TaskItem("1", "say hi")])
        # Ask skips confirm/execute/verify, goes directly to archive
        self.assertEqual(self.pm.current_phase(), "idle")
        self.assertIn(("archive_required", "ask"), self.events)
        self.assertIn(("flow_finished", True, "工作流完成"), self.events)

    def test_plan_flow_requires_confirm(self):
        self.pm.start("plan it", "plan")
        self.pm.on_analyze_complete([TaskItem("1", "step 1")])
        self.assertEqual(self.pm.current_phase(), "confirm")
        self.assertIn(("confirm_required", 1), self.events)

    def test_plan_flow_confirm_to_archive(self):
        self.pm.start("plan it", "plan")
        self.pm.on_analyze_complete([TaskItem("1", "step 1")])
        self.pm.on_user_confirm(True)
        self.assertEqual(self.pm.current_phase(), "idle")
        self.assertIn(("archive_required", "plan"), self.events)

    def test_craft_flow_full_cycle(self):
        self.pm.start("do it", "craft")
        self.pm.on_analyze_complete([TaskItem("1", "step 1"), TaskItem("2", "step 2")])
        self.pm.on_user_confirm(True)
        self.assertEqual(self.pm.current_phase(), "execute")
        self.pm.on_execute_complete([{"task": "step 1", "result": "ok"}])
        self.assertEqual(self.pm.current_phase(), "verify")
        self.pm.on_verify_complete(True, "all good")
        self.assertEqual(self.pm.current_phase(), "idle")
        self.assertIn(("flow_finished", True, "工作流完成"), self.events)

    def test_craft_confirm_false_finishes_flow(self):
        self.pm.start("do it", "craft")
        self.pm.on_analyze_complete([TaskItem("1", "step 1")])
        self.pm.on_user_confirm(False)
        self.assertEqual(self.pm.current_phase(), "idle")
        self.assertIn(("flow_finished", False, "用户取消了任务执行"), self.events)

    def test_analyze_without_tasks_errors_for_plan(self):
        self.pm.start("plan it", "plan")
        self.pm.on_analyze_complete([])
        self.assertEqual(self.pm.current_phase(), "idle")
        self.assertIn(("error_occurred", "CHECKPOINT_HARD", "进入 CONFIRM 阶段前必须有 task list"), self.events)

    def test_parse_task_list_json(self):
        text = '[{"description": "read file"}, {"description": "write file"}]'
        tasks = PhaseManager.parse_task_list(text)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].description, "read file")

    def test_parse_task_list_markdown(self):
        text = "- read file\n- [ ] write file\n- [x] run test"
        tasks = PhaseManager.parse_task_list(text)
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].description, "read file")
        self.assertEqual(tasks[1].description, "write file")

    def test_parse_task_list_plain_text_fallback(self):
        text = "just some response without list"
        tasks = PhaseManager.parse_task_list(text)
        self.assertEqual(len(tasks), 0)

    def test_phase_matrix(self):
        self.assertEqual(PhaseManager.PHASE_FLOW["ask"], [Phase.ANALYZE, Phase.ARCHIVE])
        self.assertEqual(PhaseManager.PHASE_FLOW["plan"], [Phase.ANALYZE, Phase.CONFIRM, Phase.ARCHIVE])
        self.assertEqual(
            PhaseManager.PHASE_FLOW["craft"],
            [Phase.ANALYZE, Phase.CONFIRM, Phase.EXECUTE, Phase.VERIFY, Phase.ARCHIVE],
        )

    def test_reanalyze_resets_and_restarts(self):
        self.pm.start("do it", "craft")
        self.pm.on_analyze_complete([TaskItem("1", "step 1")])
        # Simulate reanalyze by reset + start
        user_text = self.pm.current_context().user_text
        mode = self.pm.current_context().mode
        self.pm.reset()
        self.pm.start(user_text, mode)
        self.assertEqual(self.pm.current_phase(), "analyze")


if __name__ == "__main__":
    unittest.main()
