import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QListWidget,
    QMainWindow,
)

from gui.main_window import MainWindow
from gui.right_panel import RightPanel


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

    def test_auto_target_has_a_stalled_hp_interval(self):
        interval = self.panel.auto_target.interval_spin

        self.assertIsNotNone(interval)
        self.assertEqual(self.panel.auto_target.interval(), 10000)
        self.assertEqual(interval.minimum(), 4000)
        self.assertIn("bajada de vida", interval.toolTip())

    def test_main_window_stays_above_other_windows(self):
        window = QMainWindow()
        try:
            MainWindow.configure_window(window)

            self.assertTrue(
                window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
            )
            self.assertTrue(
                window.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint
            )
        finally:
            window.deleteLater()

    def test_target_selector_has_two_multiselect_lists_and_two_arrows(self):
        self.assertIsInstance(self.panel.available_list, QListWidget)
        self.assertIsInstance(self.panel.ignored_list, QListWidget)
        self.assertEqual(
            self.panel.available_list.selectionMode(),
            QAbstractItemView.SelectionMode.ExtendedSelection,
        )
        self.assertEqual(
            self.panel.ignored_list.selectionMode(),
            QAbstractItemView.SelectionMode.ExtendedSelection,
        )
        self.assertEqual(self.panel.add_ignore_button.text(), "→")
        self.assertEqual(self.panel.remove_ignore_button.text(), "←")

    def test_only_ignore_filter_controls_are_exposed(self):
        self.assertFalse(hasattr(self.panel, "unique_targets_checkbox"))
        self.assertFalse(hasattr(self.panel, "unique_targets_list"))
        self.assertFalse(hasattr(self.panel, "save_targets_button"))

    def test_database_names_are_split_without_case_duplicates(self):
        self.panel.set_enemy_names(
            ["Baoku", "Bongbo", "bongbo"],
            ["BONGBO"],
        )

        self.assertEqual(self._items(self.panel.available_list), ["Baoku"])
        ignored = self._items(self.panel.ignored_list)
        self.assertEqual(len(ignored), 1)
        self.assertEqual(ignored[0].casefold(), "bongbo")

    def test_multiple_targets_move_to_ignored_in_one_batch(self):
        self.panel.set_enemy_names(["Alpha", "Beta", "Gamma"], [])
        batches = []
        self.panel.enemy_ignores_changed.connect(
            lambda names, ignored: batches.append((list(names), ignored))
        )
        self._select_names(self.panel.available_list, "Alpha", "Beta")

        self.panel.add_ignore_button.click()

        self.assertEqual(self._items(self.panel.available_list), ["Gamma"])
        self.assertEqual(self._items(self.panel.ignored_list), ["Alpha", "Beta"])
        self.assertEqual(batches, [(["Alpha", "Beta"], True)])

    def test_multiple_ignored_targets_return_in_one_batch(self):
        self.panel.set_enemy_names(
            ["Alpha", "Beta", "Gamma"],
            ["Alpha", "Beta"],
        )
        batches = []
        self.panel.enemy_ignores_changed.connect(
            lambda names, ignored: batches.append((list(names), ignored))
        )
        self._select_names(self.panel.ignored_list, "Alpha", "Beta")

        self.panel.remove_ignore_button.click()

        self.assertEqual(
            self._items(self.panel.available_list),
            ["Alpha", "Beta", "Gamma"],
        )
        self.assertEqual(self._items(self.panel.ignored_list), [])
        self.assertEqual(batches, [(["Alpha", "Beta"], False)])

    def test_arrow_without_selection_does_not_emit_or_change_lists(self):
        self.panel.set_enemy_names(["Alpha"], [])
        batches = []
        self.panel.enemy_ignores_changed.connect(
            lambda names, ignored: batches.append((list(names), ignored))
        )

        self.panel.add_ignore_button.click()
        self.panel.remove_ignore_button.click()

        self.assertEqual(self._items(self.panel.available_list), ["Alpha"])
        self.assertEqual(self._items(self.panel.ignored_list), [])
        self.assertEqual(batches, [])

    def test_ignore_checkbox_requests_autosave_with_explicit_state(self):
        requests = []
        self.panel.target_filters_save_requested.connect(
            lambda: requests.append(self.panel.get_target_filter_state())
        )

        self.panel.ignore_targets.setChecked(True)

        self.assertEqual(requests, [{"ignore_enabled": True}])
        self.assertTrue(self.panel.has_unsaved_target_filters())

    def test_loading_ignore_filter_does_not_request_autosave(self):
        requests = []
        self.panel.target_filters_save_requested.connect(
            lambda: requests.append(True)
        )

        self.panel.set_target_filters(ignore_enabled=True)

        self.assertTrue(self.panel.ignore_targets.isChecked())
        self.assertFalse(self.panel.has_unsaved_target_filters())
        self.assertEqual(requests, [])

    def test_locking_panel_disables_target_filter_controls(self):
        self.panel.lock_controls()

        for widget in (
            self.panel.ignore_targets,
            self.panel.available_list,
            self.panel.ignored_list,
            self.panel.add_ignore_button,
            self.panel.remove_ignore_button,
        ):
            self.assertFalse(widget.isEnabled())

        self.panel.unlock_controls()

        for widget in (
            self.panel.ignore_targets,
            self.panel.available_list,
            self.panel.ignored_list,
            self.panel.add_ignore_button,
            self.panel.remove_ignore_button,
        ):
            self.assertTrue(widget.isEnabled())

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

    def test_save_persists_only_ignore_filter_for_active_game(self):
        config_calls = []
        saved = []
        panel = SimpleNamespace(
            get_target_filter_state=lambda: {"ignore_enabled": True},
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
            bot_tab=SimpleNamespace(auto_panel=panel),
        )

        result = MainWindow.save_target_filters(window)

        self.assertTrue(result)
        self.assertEqual(config_calls, [("game", True)])
        self.assertEqual(saved, [True])

    @staticmethod
    def _items(list_widget):
        return [
            list_widget.item(index).text()
            for index in range(list_widget.count())
        ]

    @staticmethod
    def _select_names(list_widget, *names):
        selected = set(names)
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            item.setSelected(item.text() in selected)


if __name__ == "__main__":
    unittest.main()
