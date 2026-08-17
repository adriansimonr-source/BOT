import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core.bot_engine import BotEngine, BotState
from core.bot_worker import BotWorker
from core.models.automation_config import (
    AutomationConfig,
    SkillConfigValue,
)
from core.models.bot_settings import BotMode
from core.modules.rotation_manager import RotationManager, SkillConfig
from core.models.target_rules import TargetRules
from gui.tabs.bot_tab import BotTab


class BotTabConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tab = BotTab()

    def tearDown(self):
        self.tab.deleteLater()
        self.app.processEvents()

    def test_edits_emit_one_flat_snapshot_after_the_debounce(self):
        snapshots = []
        self.tab.configuration_changed.connect(snapshots.append)

        number_skill = self.tab.rotation_panel.number_skills[0]
        function_skill = self.tab.rotation_panel.function_skills[6]
        number_skill.set_enabled(True)
        number_skill.time_spin.setValue(700)
        function_skill.set_enabled(True)
        function_skill.time_spin.setValue(1900)
        self.tab.auto_panel.auto_attack.set_enabled(True)
        self.tab.auto_panel.auto_attack.interval_spin.setValue(900)
        self.tab.auto_panel.auto_target.set_enabled(True)
        self.tab.auto_panel.auto_target.interval_spin.setValue(12500)
        self.tab.auto_panel.ignored_list.addItem("Lobo")
        self.tab.auto_panel.ignore_targets.setChecked(True)
        self.tab.character_group.mode_selector.setCurrentIndex(
            self.tab.character_group.mode_selector.findData(BotMode.STATIC_10)
        )

        QTest.qWait(100)
        self.app.processEvents()

        self.assertEqual(len(snapshots), 1)
        config = snapshots[0]
        enabled_skills = {
            skill.key_value: skill.interval_ms
            for skill in config.skills
            if skill.enabled
        }
        self.assertEqual(enabled_skills, {"1": 700, "F7": 1900})
        self.assertTrue(config.auto_attack.enabled)
        self.assertEqual(config.auto_attack.interval_ms, 900)
        self.assertTrue(config.auto_target.enabled)
        self.assertEqual(config.auto_target.interval_ms, 12500)
        self.assertEqual(config.ignored_targets, ("Lobo",))
        self.assertTrue(config.ignore_enabled)
        self.assertEqual(config.bot_mode, BotMode.STATIC_10)

        number_skill.time_spin.setValue(1200)
        self.assertEqual(enabled_skills["1"], 700)

    def test_skills_are_locked_while_other_live_controls_remain_editable(self):
        self.tab.lock_controls()

        self.assertFalse(self.tab.game_selector.combo.isEnabled())
        number_skill = self.tab.rotation_panel.number_skills[0]
        function_skill = self.tab.rotation_panel.function_skills[0]
        self.assertFalse(number_skill.enabled_checkbox.isEnabled())
        self.assertFalse(number_skill.time_spin.isEnabled())
        self.assertFalse(function_skill.enabled_checkbox.isEnabled())
        self.assertFalse(function_skill.time_spin.isEnabled())
        self.assertTrue(self.tab.auto_panel.auto_attack.checkbox.isEnabled())
        self.assertTrue(self.tab.auto_panel.ignore_targets.isEnabled())
        self.assertTrue(self.tab.character_group.mode_selector.isEnabled())

        self.tab.unlock_controls()

        self.assertTrue(number_skill.enabled_checkbox.isEnabled())
        self.assertTrue(number_skill.time_spin.isEnabled())
        self.assertTrue(function_skill.enabled_checkbox.isEnabled())
        self.assertTrue(function_skill.time_spin.isEnabled())

    def test_function_skill_column_explains_its_priority(self):
        header = self.tab.rotation_panel.priority_header

        self.assertEqual(header.text(), "PRIORIDAD")
        self.assertFalse(hasattr(self.tab.rotation_panel, "number_header"))
        self.assertIn("se ejecutan antes", header.toolTip())
        self.assertIn("F1–F7", header.toolTip())
        self.assertIn("milisegundos", header.toolTip())

    def test_rotation_exposes_only_numeric_and_f1_to_f7_skills(self):
        panel = self.tab.rotation_panel

        self.assertEqual(
            [card.skill_number() for card in panel.number_skills],
            [str(number) for number in range(1, 10)],
        )
        self.assertEqual(
            [card.skill_number() for card in panel.function_skills],
            [f"F{number}" for number in range(1, 8)],
        )
        self.assertEqual(len(panel.skills), 16)


class LiveConfigurationApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_running_engine_merges_rotation_without_resetting_deadline(self):
        rotation = RotationManager(SimpleNamespace())
        rotation.skills = [SkillConfig(True, "1", 500, last_cast=1234)]

        engine = BotEngine.__new__(BotEngine)
        engine.state = BotState.RUNNING
        engine.movement_manager = MagicMock()
        engine.target_rules = TargetRules()
        engine.modules = [rotation]

        engine.apply_config(
            AutomationConfig(
                revision=2,
                skills=(
                    SkillConfigValue(True, "1", 900),
                    SkillConfigValue(False, "2", 500),
                ),
            )
        )

        self.assertEqual(len(rotation.skills), 1)
        self.assertEqual(rotation.skills[0].key, "1")
        self.assertEqual(rotation.skills[0].cooldown, 900)
        self.assertEqual(rotation.skills[0].last_cast, 1234)
        engine.movement_manager.set_learning_profile.assert_not_called()

    def test_paused_engine_also_preserves_rotation_deadlines(self):
        rotation = RotationManager(SimpleNamespace())
        rotation.skills = [SkillConfig(True, "1", 500, last_cast=1234)]
        engine = BotEngine.__new__(BotEngine)
        engine.state = BotState.PAUSED
        engine.movement_manager = MagicMock()
        engine.target_rules = TargetRules()
        engine.modules = [rotation]

        engine.apply_config(
            AutomationConfig(
                revision=2,
                skills=(SkillConfigValue(True, "1", 900),),
            )
        )

        self.assertEqual(rotation.skills[0].last_cast, 1234)
        engine.movement_manager.set_learning_profile.assert_not_called()

    def test_worker_applies_only_newer_revisions(self):
        engine = SimpleNamespace(apply_config=MagicMock())
        worker = BotWorker(engine)
        applied = []
        worker.config_applied.connect(applied.append)

        newest = AutomationConfig(revision=3)
        stale = AutomationConfig(revision=2)
        self.assertTrue(worker.apply_config(newest))
        self.assertFalse(worker.apply_config(stale))

        engine.apply_config.assert_called_once_with(newest)
        self.assertEqual(applied, [3])


if __name__ == "__main__":
    unittest.main()
