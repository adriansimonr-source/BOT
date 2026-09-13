import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMessageBox

from core.managers.config_manager import ConfigManager
from gui.main_window import MainWindow
from gui.tabs.bot_tab import BotTab
from gui.widgets.profile_selector import ProfileSelector


class AutomationProfilePersistenceTests(unittest.TestCase):
    def test_profiles_are_persisted_and_updated_case_insensitively(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(json.dumps({"active_game": None}), encoding="utf-8")
            manager = ConfigManager(str(path))

            self.assertEqual(
                manager.set_automation_profile(
                    "Combate",
                    {"version": 1, "ignore_enabled": False},
                ),
                "Combate",
            )
            self.assertEqual(manager.get_automation_profile_names(), ["Combate"])

            loaded = manager.get_automation_profile("combate")
            loaded["ignore_enabled"] = True
            self.assertFalse(
                manager.get_automation_profile("Combate")["ignore_enabled"]
            )

            self.assertEqual(
                manager.set_automation_profile(
                    "COMBATE",
                    {"version": 1, "ignore_enabled": True},
                ),
                "Combate",
            )
            restored = ConfigManager(str(path))
            self.assertEqual(restored.get_automation_profile_names(), ["Combate"])
            self.assertTrue(
                restored.get_automation_profile("combate")["ignore_enabled"]
            )
            self.assertTrue(restored.remove_automation_profile("COMBATE"))
            self.assertEqual(restored.get_automation_profile_names(), [])
            self.assertIsNone(restored.get_automation_profile("Combate"))
            self.assertFalse((path.parent / "config.json.tmp").exists())


class AutomationProfileGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_selector_starts_optional_and_accepts_a_new_name(self):
        selector = ProfileSelector()
        selected = []
        saves = []
        deletes = []
        selector.profile_selected.connect(selected.append)
        selector.save_requested.connect(saves.append)
        selector.delete_requested.connect(deletes.append)
        try:
            selector.set_profiles(["Soporte", "Combate"])
            self.assertEqual(selector.selected_name(), "")
            self.assertFalse(selector.delete_button.isEnabled())
            self.assertEqual(selector.save_button.text(), "")
            self.assertFalse(selector.save_button.icon().isNull())
            self.assertEqual(selector.save_button.size(), QSize(22, 20))

            selector.combo.setCurrentIndex(selector.combo.findData("Combate"))
            self.assertEqual(selected, ["Combate"])
            self.assertTrue(selector.delete_button.isEnabled())

            selector.combo.setCurrentIndex(0)
            self.assertEqual(selected, ["Combate", ""])
            self.assertFalse(selector.delete_button.isEnabled())

            selector.combo.setCurrentIndex(selector.combo.findData("Combate"))

            selector.combo.setEditText("Nuevo perfil")
            self.assertFalse(selector.delete_button.isEnabled())
            selector.save_button.click()
            self.assertEqual(saves, ["Nuevo perfil"])

            selector.combo.setCurrentIndex(selector.combo.findData("Combate"))
            selector.delete_button.click()
            self.assertEqual(deletes, ["Combate"])
        finally:
            selector.deleteLater()
            self.app.processEvents()

    def test_profile_round_trip_restores_checks_thresholds_and_times(self):
        tab = BotTab()
        try:
            defaults = tab.get_profile_settings()
            tab.auto_panel.auto_target.set_enabled(True)
            tab.auto_panel.auto_target.interval_spin.setValue(6500)
            tab.auto_panel.auto_attack.set_enabled(True)
            tab.auto_panel.auto_attack.interval_spin.setValue(750)
            tab.auto_panel.auto_pot1.set_enabled(True)
            tab.auto_panel.auto_pot1.threshold_spin.setValue(35)
            tab.auto_panel.auto_pot1.interval_spin.setValue(1800)
            tab.rotation_panel.number_skills[0].set_enabled(True)
            tab.rotation_panel.number_skills[0].time_spin.setValue(1500)
            tab.rotation_panel.function_skills[-1].set_enabled(True)
            tab.rotation_panel.function_skills[-1].time_spin.setValue(4000)
            tab.auto_panel.ignore_targets.setChecked(True)

            settings = tab.get_profile_settings()

            tab.auto_panel.auto_target.set_enabled(False)
            tab.auto_panel.auto_target.interval_spin.setValue(10000)
            tab.auto_panel.auto_attack.set_enabled(False)
            tab.auto_panel.auto_pot1.set_enabled(False)
            tab.auto_panel.auto_pot1.threshold_spin.setValue(80)
            tab.rotation_panel.number_skills[0].set_enabled(False)
            tab.rotation_panel.function_skills[-1].set_enabled(False)
            tab.auto_panel.ignore_targets.setChecked(False)

            self.assertTrue(tab.apply_profile_settings(settings))
            self.assertTrue(tab.auto_panel.auto_target.is_enabled())
            self.assertEqual(tab.auto_panel.auto_target.interval(), 6500)
            self.assertTrue(tab.auto_panel.auto_attack.is_enabled())
            self.assertEqual(tab.auto_panel.auto_attack.interval(), 750)
            self.assertTrue(tab.auto_panel.auto_pot1.is_enabled())
            self.assertEqual(tab.auto_panel.auto_pot1.threshold(), 35)
            self.assertEqual(tab.auto_panel.auto_pot1.interval(), 1800)
            self.assertTrue(tab.rotation_panel.number_skills[0].is_enabled())
            self.assertEqual(tab.rotation_panel.number_skills[0].time(), 1500)
            self.assertTrue(tab.rotation_panel.function_skills[-1].is_enabled())
            self.assertEqual(tab.rotation_panel.function_skills[-1].time(), 4000)
            self.assertTrue(tab.auto_panel.ignore_targets.isChecked())

            self.assertTrue(tab.reset_profile_settings())
            self.assertFalse(tab.auto_panel.auto_target.is_enabled())
            self.assertEqual(tab.auto_panel.auto_target.interval(), 10000)
            self.assertFalse(tab.auto_panel.auto_attack.is_enabled())
            self.assertEqual(tab.auto_panel.auto_attack.interval(), 250)
            self.assertFalse(tab.auto_panel.auto_pot1.is_enabled())
            self.assertEqual(tab.auto_panel.auto_pot1.threshold(), 40)
            self.assertEqual(tab.auto_panel.auto_pot1.interval(), 2000)
            self.assertFalse(tab.rotation_panel.number_skills[0].is_enabled())
            self.assertEqual(tab.rotation_panel.number_skills[0].time(), 500)
            self.assertFalse(tab.rotation_panel.function_skills[-1].is_enabled())
            self.assertEqual(tab.rotation_panel.function_skills[-1].time(), 500)
            self.assertFalse(tab.auto_panel.ignore_targets.isChecked())
            self.assertEqual(tab.get_profile_settings(), defaults)
        finally:
            tab.deleteLater()
            self.app.processEvents()

    def test_main_window_saves_and_loads_the_selected_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(json.dumps({}), encoding="utf-8")
            manager = ConfigManager(str(path))
            tab = BotTab()
            refreshed = []
            window = SimpleNamespace(
                process_manager=SimpleNamespace(config=manager),
                bot_tab=tab,
                refresh_automation_profiles=(
                    lambda selected=None: refreshed.append(selected)
                ),
            )
            try:
                tab.auto_panel.auto_attack.set_enabled(True)
                tab.auto_panel.auto_attack.interval_spin.setValue(950)

                self.assertTrue(
                    MainWindow.save_automation_profile(window, "Principal")
                )
                self.assertEqual(refreshed, ["Principal"])

                tab.auto_panel.auto_attack.set_enabled(False)
                tab.auto_panel.auto_attack.interval_spin.setValue(250)
                MainWindow.load_automation_profile(window, "Principal")

                self.assertTrue(tab.auto_panel.auto_attack.is_enabled())
                self.assertEqual(tab.auto_panel.auto_attack.interval(), 950)

                MainWindow.load_automation_profile(window, "")
                self.assertFalse(tab.auto_panel.auto_attack.is_enabled())
                self.assertEqual(tab.auto_panel.auto_attack.interval(), 250)

                with patch(
                    "gui.main_window.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ):
                    self.assertTrue(
                        MainWindow.delete_automation_profile(
                            window,
                            "Principal",
                        )
                    )
                self.assertEqual(manager.get_automation_profile_names(), [])
                self.assertEqual(refreshed, ["Principal", None])
            finally:
                tab.deleteLater()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
