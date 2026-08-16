import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.dialogs.add_game_dialog import AddGameDialog
from gui.right_panel import RightPanel
from gui.widgets.bot_control_bar import BotControlBar
from gui.widgets.character_group import CharacterGroup
from gui.widgets.game_selector import GameSelector
from gui.widgets.skill_card import SkillCard


class _EmptyGameProfiles:
    @staticmethod
    def get_games():
        return []


class _ExistingGameProfiles:
    @staticmethod
    def get_games():
        return [{"id": "kathana", "name": "Kathana"}]


class GuiTooltipTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_action_buttons_explain_their_effect(self):
        control_bar = BotControlBar()
        character = CharacterGroup()
        panel = RightPanel()
        selector = GameSelector(_EmptyGameProfiles())
        dialog = AddGameDialog(SimpleNamespace())
        try:
            buttons = (
                control_bar.start_button,
                character.refresh_position_button,
                character.lock_position_button,
                character.unlock_position_button,
                panel.auto_target.key_button,
                panel.auto_attack.key_button,
                panel.auto_loot.key_button,
                panel.add_ignore_button,
                panel.remove_ignore_button,
                selector.add_button,
                selector.refresh_button,
                selector.delete_button,
                dialog.detect_button,
                dialog.cancel_button,
                dialog.add_button,
            )
            for button in buttons:
                self.assertTrue(button.toolTip().strip(), button.text())
        finally:
            for widget in (control_bar, character, panel, selector, dialog):
                widget.deleteLater()
            self.app.processEvents()

    def test_compact_skill_controls_explain_activation_and_timing(self):
        skill = SkillCard("F3")
        try:
            self.assertIn("F3", skill.enabled_checkbox.toolTip())
            self.assertIn("F3", skill.skill_label.toolTip())
            self.assertIn("F3", skill.time_spin.toolTip())
        finally:
            skill.deleteLater()
            self.app.processEvents()

    def test_start_button_help_tracks_the_bot_state(self):
        control_bar = BotControlBar()
        try:
            self.assertIn("Inicia", control_bar.start_button.toolTip())

            control_bar.set_running()
            self.assertIn("Detiene", control_bar.start_button.toolTip())

            control_bar.set_stopping()
            self.assertIn("Espera", control_bar.start_button.toolTip())

            control_bar.set_stopped()
            self.assertIn("Inicia", control_bar.start_button.toolTip())
        finally:
            control_bar.deleteLater()
            self.app.processEvents()

    def test_game_status_always_has_contextual_help(self):
        selector = GameSelector(_EmptyGameProfiles())
        existing_selector = GameSelector(_ExistingGameProfiles())
        try:
            self.assertIn("Sin juegos", selector.status_label.toolTip())
            self.assertIn(
                "Sin detectar",
                existing_selector.status_label.toolTip(),
            )

            selector.set_process_status(
                True,
                "Conectado",
                "Proceso: Kathana.exe\nPID: 42",
            )

            self.assertEqual(
                selector.status_label.toolTip(),
                "Proceso: Kathana.exe\nPID: 42",
            )
            selector.set_process_status(True, "Conectado")
            self.assertEqual(
                selector.status_label.toolTip(),
                "Proceso: Kathana.exe\nPID: 42",
            )
        finally:
            selector.deleteLater()
            existing_selector.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
