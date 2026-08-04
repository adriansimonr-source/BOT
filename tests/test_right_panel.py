import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QListWidget

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
                ["FIJO (0)", "25", "50", "75", "100", "SIN LÍMITE"],
            )
            self.assertEqual(
                [
                    group.mode_selector.itemData(index)
                    for index in range(group.mode_selector.count())
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
            self.assertEqual(group.get_bot_mode(), BotMode.STATIC_100)
        finally:
            group.deleteLater()

    def test_database_names_are_split_without_case_duplicates(self):
        self.panel.set_enemy_names(
            ["Baoku", "Bongbo", "bongbo"],
            ["BONGBO"],
        )

        self.assertIsInstance(self.panel.available_combo, QComboBox)
        self.assertNotIsInstance(self.panel.available_combo, QListWidget)
        available = self._combo_items(self.panel.available_combo)
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
            self.panel.add_manual_unique_targets()
            self.panel.add_manual_unique_targets()

        self.assertEqual(
            self._items(self.panel.unique_targets_list),
            ["Bongbo"],
        )

    def test_multiple_available_targets_can_be_added_and_removed(self):
        self.panel.set_enemy_names(["Alpha", "Beta", "Gamma"], [])
        self.panel.available_combo.setCurrentText("Alpha")
        self.panel.add_unique_target()
        self.panel.available_combo.setCurrentText("Beta")
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
        batches = []
        self.panel.enemy_ignores_changed.connect(
            lambda names, ignored: batches.append((list(names), ignored))
        )

        self.panel.available_combo.setCurrentText("Alpha")
        self.panel.move_to_ignored()
        self.panel.available_combo.setCurrentText("Beta")
        self.panel.move_to_ignored()

        self.assertEqual(self._combo_items(self.panel.available_combo), ["Gamma"])
        self.assertEqual(self._items(self.panel.ignored_list), ["Alpha", "Beta"])
        self.assertEqual(
            batches,
            [(["Alpha"], True), (["Beta"], True)],
        )

        for index in range(self.panel.ignored_list.count()):
            self.panel.ignored_list.item(index).setSelected(True)
        self.panel.move_to_available()

        self.assertEqual(
            self._combo_items(self.panel.available_combo),
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
            self.panel.add_manual_unique_targets()

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
        batches = []
        self.panel.enemy_ignores_changed.connect(
            lambda names, ignored: batches.append((list(names), ignored))
        )

        with patch(
            "gui.right_panel.QInputDialog.getMultiLineText",
            return_value=("Beta", True),
        ):
            self.panel.add_manual_unique_targets()

        self.assertEqual(self._items(self.panel.unique_targets_list), ["Beta"])
        self.assertEqual(self._combo_items(self.panel.available_combo), ["Alpha"])
        self.assertEqual(self.panel.ignored_list.count(), 0)
        self.assertEqual(batches, [(["Beta"], False)])

    def test_save_is_visible_and_emits_only_explicit_user_state(self):
        self.panel.set_enemy_names(["Alpha", "Database garbage"], [])
        requests = []
        self.panel.target_filters_save_requested.connect(
            lambda: requests.append(self.panel.get_target_filter_state())
        )

        self.assertTrue(self.panel.save_targets_button.isVisibleTo(self.panel))
        self.assertFalse(self.panel.save_targets_button.isEnabled())

        self.panel.available_combo.setCurrentText("Alpha")
        self.panel.add_unique_target()
        self.panel.unique_targets_checkbox.setChecked(True)
        self.assertTrue(self.panel.save_targets_button.isEnabled())
        self.panel.save_targets_button.click()

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["unique_targets"], ["Alpha"])
        self.assertNotIn("Database garbage", requests[0]["unique_targets"])

    def test_explicit_persisted_unique_targets_can_be_restored(self):
        self.panel.set_enemy_names(["Alpha", "Database garbage"], [])

        self.panel.set_target_filters(
            ["Boss", "boss", "Alpha"],
            ignore_enabled=True,
            unique_enabled=True,
        )

        self.assertEqual(
            self._items(self.panel.unique_targets_list),
            ["Alpha", "Boss"],
        )
        self.assertTrue(self.panel.ignore_targets.isChecked())
        self.assertTrue(self.panel.unique_targets_checkbox.isChecked())
        self.assertFalse(self.panel.has_unsaved_target_filters())
        self.assertEqual(
            self._combo_items(self.panel.available_combo),
            ["Database garbage"],
        )

    def test_ignore_batch_persists_each_name_and_refreshes_once(self):
        calls = []
        refreshes = []
        window = SimpleNamespace(
            entity_database=SimpleNamespace(
                set_enemies_ignored=lambda names, ignored: calls.append(
                    (list(names), ignored)
                )
            ),
            refresh_enemy_lists=lambda force=False: refreshes.append(force),
        )

        MainWindow.set_enemies_ignored(
            window,
            ["Alpha", "alpha", "Beta"],
            True,
        )

        self.assertEqual(len(calls), 1)
        names, ignored = calls[0]
        self.assertEqual({name.casefold() for name in names}, {"alpha", "beta"})
        self.assertTrue(ignored)
        self.assertEqual(refreshes, [True])

    def test_save_persists_ignored_snapshot_and_unique_game_filters(self):
        ignored_calls = []
        config_calls = []
        saved = []
        refreshes = []
        panel = SimpleNamespace(
            get_target_filter_state=lambda: {
                "ignored_targets": ["Beta"],
                "unique_targets": ["Boss A", "Boss B"],
                "ignore_enabled": True,
                "unique_enabled": True,
            },
            mark_target_filters_saved=lambda: saved.append(True),
        )
        config = SimpleNamespace(
            set_game_target_filters=lambda *args: config_calls.append(args)
        )
        window = SimpleNamespace(
            process_manager=SimpleNamespace(
                get_active_game=lambda: {"id": "game"},
                config=config,
            ),
            entity_database=SimpleNamespace(
                get_ignored_enemy_names=lambda: ["Alpha"],
                set_enemies_ignored=lambda names, ignored: ignored_calls.append(
                    (list(names), ignored)
                ),
            ),
            bot_tab=SimpleNamespace(auto_panel=panel),
            refresh_enemy_lists=lambda force=False: refreshes.append(force),
        )

        result = MainWindow.save_target_filters(window)

        self.assertTrue(result)
        self.assertEqual(
            ignored_calls,
            [(["Alpha"], False), (["Beta"], True)],
        )
        self.assertEqual(
            config_calls,
            [("game", ["Boss A", "Boss B"], True, True)],
        )
        self.assertEqual(refreshes, [True])
        self.assertEqual(saved, [True])

    @staticmethod
    def _items(list_widget):
        return [
            list_widget.item(index).text()
            for index in range(list_widget.count())
        ]

    @staticmethod
    def _combo_items(combo):
        return [combo.itemText(index) for index in range(combo.count())]


if __name__ == "__main__":
    unittest.main()
