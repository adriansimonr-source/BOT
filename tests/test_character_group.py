import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from core.models.bot_settings import BotMode
from gui.widgets.character_group import CharacterGroup


class CharacterGroupTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.group = CharacterGroup()

    def tearDown(self):
        self.group.deleteLater()
        self.app.processEvents()

    def test_only_personaje_title_remains_from_identity_header(self):
        self.assertEqual(self.group.title_label.text(), "PERSONAJE")
        for attribute in (
            "character_name_label",
            "level_label",
            "online_label",
            "character_status_indicator",
            "refresh_name_button",
        ):
            self.assertFalse(hasattr(self.group, attribute), attribute)

        texts = [label.text() for label in self.group.findChildren(QLabel)]
        for removed_text in ("NAME:", "LVL:", "ONLINE", "OFFLINE"):
            self.assertFalse(
                any(removed_text in text for text in texts),
                removed_text,
            )

    def test_update_state_keeps_hp_mp_and_coordinate_feedback(self):
        state = SimpleNamespace(
            player=SimpleNamespace(
                hp_percent=73.8,
                mp_percent=41.2,
                x=123,
                y=456,
                position_valid=True,
                start_x=120,
                start_y=450,
                position_locked=True,
            )
        )

        self.group.update_state(state)

        self.assertEqual(self.group.hp_bar.bar.value(), 73)
        self.assertEqual(self.group.hp_bar.value_label.text(), "73%")
        self.assertEqual(self.group.mp_bar.bar.value(), 41)
        self.assertEqual(self.group.mp_bar.value_label.text(), "41%")
        self.assertEqual(self.group.current_position_label.text(), "123 / 456")
        self.assertEqual(self.group.start_position_label.text(), "120 / 450")

        state.player.position_valid = False
        state.player.position_locked = False
        self.group.update_state(state)

        self.assertEqual(self.group.current_position_label.text(), "--- / ---")
        self.assertEqual(self.group.start_position_label.text(), "--- / ---")

    def test_radio_and_quiet_settings_keep_their_contract(self):
        self.assertEqual(
            [
                self.group.mode_selector.itemText(index)
                for index in range(self.group.mode_selector.count())
            ],
            ["FIJO (0)", "25", "50", "75", "100", "SIN LÍMITE"],
        )
        self.assertEqual(
            [
                self.group.mode_selector.itemData(index)
                for index in range(self.group.mode_selector.count())
            ],
            [
                BotMode.STATIC_POINT,
                BotMode.STATIC_25,
                BotMode.STATIC_50,
                BotMode.STATIC_75,
                BotMode.STATIC_100,
                BotMode.OFF,
            ],
        )
        self.assertEqual(self.group.get_bot_mode(), BotMode.STATIC_100)
        self.assertEqual(self.group.quiet_seconds.minimum(), 3)
        self.assertEqual(self.group.quiet_seconds.maximum(), 120)
        self.assertEqual(self.group.get_quiet_seconds(), 10)

    def test_lock_settings_only_locks_editable_bot_settings(self):
        self.group.lock_settings()

        self.assertFalse(self.group.mode_selector.isEnabled())
        self.assertFalse(self.group.quiet_seconds.isEnabled())
        self.assertTrue(self.group.refresh_position_button.isEnabled())
        self.assertTrue(self.group.lock_position_button.isEnabled())
        self.assertTrue(self.group.unlock_position_button.isEnabled())

        self.group.unlock_settings()

        self.assertTrue(self.group.mode_selector.isEnabled())
        self.assertTrue(self.group.quiet_seconds.isEnabled())


if __name__ == "__main__":
    unittest.main()
