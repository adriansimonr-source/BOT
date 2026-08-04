import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from core.models.bot_settings import BotMode
from gui.main_window import MainWindow
from gui.right_panel import RightPanel
from gui.widgets.character_group import CharacterGroup


class RightPanelTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.panel = RightPanel()

    def tearDown(self):
        self.panel.deleteLater()
        self.app.processEvents()

    def test_auto_attack_has_an_editable_millisecond_interval(self):
        self.assertIsNotNone(self.panel.auto_attack.interval_spin)
        self.assertEqual(self.panel.auto_attack.interval(), 250)

        self.panel.auto_attack.interval_spin.setValue(725)

        self.assertEqual(self.panel.auto_attack.interval(), 725)

    def test_bot_radius_uses_compact_coordinate_ranges(self):
        group = CharacterGroup()
        try:
            self.assertEqual(
                [
                    group.mode_selector.itemText(index)
                    for index in range(group.mode_selector.count())
                ],
                ["FIJO (0)", "50", "100", "150", "SIN LÍMITE"],
            )
            self.assertEqual(
                [
                    group.mode_selector.itemData(index)
                    for index in range(group.mode_selector.count())
                ],
                [
                    BotMode.STATIC_POINT,
                    BotMode.STATIC_50,
                    BotMode.STATIC_100,
                    BotMode.STATIC_150,
                    BotMode.OFF,
                ],
            )
            self.assertEqual(group.get_bot_mode(), BotMode.STATIC_100)
        finally:
            group.deleteLater()

    def test_database_names_are_split_without_case_duplicates(self):
        self.panel.set_enemy_names(
            ["Baoku", "Bongbo", "bongbo"],
            ["BONGBO"],
        )

        available = self._items(self.panel.available_list)
        ignored = self._items(self.panel.ignored_list)
        self.assertEqual(available, ["Baoku"])
        self.assertEqual(len(ignored), 1)
        self.assertEqual(ignored[0].casefold(), "bongbo")

    def test_unique_target_uses_database_name_and_has_no_duplicates(self):
        self.panel.set_enemy_names(["Baoku", "Bongbo"], [])

        with patch(
            "gui.right_panel.QInputDialog.getMultiLineText",
            side_effect=[("bONgbo", True), ("BONGBO", True)],
        ):
            self.panel.add_unique_target()
            self.panel.add_unique_target()

        self.assertEqual(
            self._items(self.panel.unique_targets_list),
            ["Bongbo"],
        )

    def test_multiple_available_targets_can_be_added_and_removed_together(self):
        self.panel.set_enemy_names(["Alpha", "Beta", "Gamma"], [])
        self.panel.available_list.item(0).setSelected(True)
        self.panel.available_list.item(1).setSelected(True)

        self.panel.add_unique_target()

        self.assertEqual(
            self._items(self.panel.unique_targets_list),
            ["Alpha", "Beta"],
        )
        self.assertTrue(self.panel.unique_targets_checkbox.isEnabled())

        self.panel.unique_targets_checkbox.setChecked(True)
        for index in range(self.panel.unique_targets_list.count()):
            self.panel.unique_targets_list.item(index).setSelected(True)
        self.panel.remove_unique_target()

        self.assertEqual(self.panel.unique_targets_list.count(), 0)
        self.assertFalse(self.panel.unique_targets_checkbox.isChecked())
        self.assertFalse(self.panel.unique_targets_checkbox.isEnabled())

    def test_multiple_ignored_targets_move_as_one_batch_without_duplicates(self):
        self.panel.set_enemy_names(["Alpha", "Beta", "Gamma"], [])
        self.panel.available_list.item(0).setSelected(True)
        self.panel.available_list.item(1).setSelected(True)
        batches = []
        self.panel.enemy_ignores_changed.connect(
            lambda names, ignored: batches.append((list(names), ignored))
        )

        self.panel.move_to_ignored()

        self.assertEqual(self._items(self.panel.available_list), ["Gamma"])
        self.assertEqual(self._items(self.panel.ignored_list), ["Alpha", "Beta"])
        self.assertEqual(batches, [(["Alpha", "Beta"], True)])

        for index in range(self.panel.ignored_list.count()):
            self.panel.ignored_list.item(index).setSelected(True)
        self.panel.move_to_available()

        self.assertEqual(
            self._items(self.panel.available_list),
            ["Alpha", "Beta", "Gamma"],
        )
        self.assertEqual(self.panel.ignored_list.count(), 0)

    def test_database_refresh_never_populates_the_unique_list(self):
        self.panel.set_enemy_names(["OCR garbage", "Normal"], [])

        self.assertEqual(self.panel.unique_targets_list.count(), 0)

        with patch(
            "gui.right_panel.QInputDialog.getMultiLineText",
            return_value=("Boss A\nBoss B\nboss a", True),
        ):
            self.panel.add_unique_target()

        self.panel.set_enemy_names(
            ["OCR garbage", "Other garbage", "Normal"],
            [],
        )

        self.assertEqual(
            self._items(self.panel.unique_targets_list),
            ["Boss A", "Boss B"],
        )

    def test_ignored_target_is_removed_from_unique_targets(self):
        self.panel.set_enemy_names(["Bongbo"], [])
        self.panel.unique_targets_list.addItem("Bongbo")

        self.panel.set_enemy_names(["Bongbo"], ["Bongbo"])

        self.assertEqual(self.panel.unique_targets_list.count(), 0)

    def test_adding_an_ignored_target_to_unique_unignores_it(self):
        self.panel.set_enemy_names(["Alpha", "Beta"], ["Beta"])
        self.panel.ignored_list.item(0).setSelected(True)
        batches = []
        self.panel.enemy_ignores_changed.connect(
            lambda names, ignored: batches.append((list(names), ignored))
        )

        self.panel.add_unique_target()

        self.assertEqual(self._items(self.panel.unique_targets_list), ["Beta"])
        self.assertEqual(self._items(self.panel.available_list), ["Alpha", "Beta"])
        self.assertEqual(self.panel.ignored_list.count(), 0)
        self.assertEqual(batches, [(["Beta"], False)])

    def test_ignore_batch_persists_each_name_and_refreshes_once(self):
        calls = []
        refreshes = []
        window = SimpleNamespace(
            entity_database=SimpleNamespace(
                set_enemy_ignored=lambda name, ignored: calls.append(
                    (name, ignored)
                )
            ),
            refresh_enemy_lists=lambda force=False: refreshes.append(force),
        )

        MainWindow.set_enemies_ignored(
            window,
            ["Alpha", "alpha", "Beta"],
            True,
        )

        self.assertEqual(
            {(name.casefold(), ignored) for name, ignored in calls},
            {("alpha", True), ("beta", True)},
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(refreshes, [True])

    @staticmethod
    def _items(list_widget):
        return [
            list_widget.item(index).text()
            for index in range(list_widget.count())
        ]


if __name__ == "__main__":
    unittest.main()
