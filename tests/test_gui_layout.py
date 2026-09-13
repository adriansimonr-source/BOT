import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSizePolicy,
    QStyleFactory,
    QTabWidget,
)

from gui.main_window import MainWindow


class _GameProfiles:
    @staticmethod
    def get_games():
        return [{"id": "kathana", "name": "Kathana"}]


class AdaptiveGuiLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.previous_style = cls.app.style().objectName()
        if "windows11" in QStyleFactory.keys():
            cls.app.setStyle("windows11")

    @classmethod
    def tearDownClass(cls):
        cls.app.setStyle(cls.previous_style)

    def setUp(self):
        self.window = QMainWindow()
        MainWindow.configure_window(self.window)
        MainWindow.apply_style(self.window)
        self.window.game_profiles = _GameProfiles()
        MainWindow.create_ui(self.window)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_main_content_has_no_bot_or_log_tabs(self):
        self.assertIs(self.window.centralWidget(), self.window.bot_tab)
        self.assertEqual(self.window.findChildren(QTabWidget), [])
        self.assertFalse(hasattr(self.window, "tabs"))
        self.assertFalse(hasattr(self.window, "log_tab"))

    def test_window_is_resizable_and_layout_enforces_its_minimum(self):
        initial = self.window.size()
        minimum = self.window.minimumSizeHint()
        self.assertGreaterEqual(initial.width(), minimum.width())
        self.assertGreaterEqual(initial.height(), minimum.height())
        self.assertGreater(self.window.maximumWidth(), initial.width())
        self.assertGreater(self.window.maximumHeight(), initial.height())

        enlarged = QSize(initial.width() + 240, initial.height() + 160)
        self.window.resize(enlarged)
        self.app.processEvents()
        self.assertEqual(self.window.size(), enlarged)

        self.window.resize(100, 100)
        self.app.processEvents()
        self.assertGreaterEqual(
            self.window.width(), self.window.minimumSizeHint().width()
        )
        self.assertGreaterEqual(
            self.window.height(), self.window.minimumSizeHint().height()
        )

    def test_sections_remain_contained_at_minimum_and_large_sizes(self):
        minimum = self.window.minimumSizeHint()
        for size in (
            minimum,
            QSize(max(640, minimum.width()), max(360, minimum.height())),
            QSize(minimum.width() + 300, minimum.height() + 240),
        ):
            self.window.resize(size)
            self.app.processEvents()
            panel = self.window.bot_tab
            for widget in (
                panel.game_selector,
                panel.bot_controls,
                panel.character_group,
                panel.target_group,
                panel.profile_selector,
                panel.auto_panel,
                panel.rotation_panel,
            ):
                self._assert_inside(widget, panel)

            for widget in (
                panel.auto_panel.available_label,
                panel.auto_panel.ignored_label,
                panel.auto_panel.available_list,
                panel.auto_panel.ignored_list,
                panel.auto_panel.add_ignore_button,
                panel.auto_panel.remove_ignore_button,
            ):
                self._assert_inside(widget, panel.auto_panel)

            for skill in panel.rotation_panel.skills:
                self._assert_inside(skill, panel.rotation_panel)

    def test_start_button_stays_at_the_right_of_the_game_row(self):
        panel = self.window.bot_tab
        game = panel.game_selector.geometry()
        controls = panel.bot_controls.geometry()

        self.assertEqual(game.top(), controls.top())
        self.assertGreater(controls.left(), game.left())
        self.assertLess(controls.bottom(), panel.character_group.geometry().top())
        self._assert_inside(panel.bot_controls.start_button, panel.bot_controls)

    def test_target_lists_expand_without_overlapping(self):
        panel = self.window.bot_tab.auto_panel
        for list_widget in (panel.available_list, panel.ignored_list):
            self.assertEqual(list_widget.minimumSize(), QSize(92, 46))
            self.assertEqual(
                list_widget.sizePolicy().horizontalPolicy(),
                QSizePolicy.Policy.Expanding,
            )
            self.assertEqual(
                list_widget.sizePolicy().verticalPolicy(),
                QSizePolicy.Policy.Expanding,
            )

        initial_available = panel.available_list.size()
        initial_ignored = panel.ignored_list.size()
        self.window.resize(self.window.width() + 240, self.window.height() + 200)
        self.app.processEvents()

        self.assertGreater(panel.available_list.width(), initial_available.width())
        self.assertGreater(panel.available_list.height(), initial_available.height())
        self.assertGreater(panel.ignored_list.width(), initial_ignored.width())
        self.assertGreater(panel.ignored_list.height(), initial_ignored.height())
        self.assertLess(
            panel.available_list.geometry().right(),
            panel.ignored_list.geometry().left(),
        )

    def test_resource_bars_share_and_use_additional_width(self):
        panel = self.window.bot_tab
        character = panel.character_group
        initial_hp = character.hp_bar.width()
        initial_mp = character.mp_bar.width()
        initial_target_hp = panel.target_group.hp_bar.width()

        self.assertLessEqual(abs(initial_hp - initial_mp), 1)
        self.assertGreaterEqual(initial_hp, 120)
        self.assertGreaterEqual(initial_target_hp, 140)
        self.assertEqual(
            character.hp_bar.geometry().top(),
            character.mp_bar.geometry().top(),
        )

        self.window.resize(self.window.width() + 300, self.window.height())
        self.app.processEvents()

        self.assertLessEqual(
            abs(character.hp_bar.width() - character.mp_bar.width()),
            1,
        )
        self.assertGreater(character.hp_bar.width(), initial_hp)
        self.assertGreater(character.mp_bar.width(), initial_mp)
        self.assertGreater(panel.target_group.hp_bar.width(), initial_target_hp)

    def test_target_hp_is_adjacent_and_profile_stays_to_its_right(self):
        panel = self.window.bot_tab
        target_group = panel.target_group
        target_group.target_name_label.setText("TARGET: Mlecchas Karmana")
        self.app.processEvents()

        target = target_group.target_name_label.geometry()
        hp = target_group.hp_bar.geometry()
        spacing = target_group.layout().spacing()

        self.assertFalse(hasattr(target_group, "level_label"))
        self.assertEqual(hp.left() - target.right() - 1, spacing)
        self.assertLessEqual(
            target_group.target_name_label.fontMetrics().horizontalAdvance(
                target_group.target_name_label.text()
            ),
            target.width(),
        )
        self._assert_inside(target_group.hp_bar, target_group)
        self.assertLess(
            target_group.geometry().right(),
            panel.profile_selector.geometry().left(),
        )
        self._assert_inside(
            panel.profile_selector.combo,
            panel.profile_selector,
        )
        self._assert_inside(
            panel.profile_selector.save_button,
            panel.profile_selector,
        )
        self._assert_inside(
            panel.profile_selector.delete_button,
            panel.profile_selector,
        )
        self.assertTrue(
            panel.profile_selector.save_button.isVisibleTo(
                panel.profile_selector
            )
        )
        self.assertTrue(
            panel.profile_selector.delete_button.isVisibleTo(
                panel.profile_selector
            )
        )
        self.assertIn(
            "#173B6D",
            panel.profile_selector.save_button.styleSheet(),
        )

    def test_dynamic_status_and_spinbox_values_are_readable(self):
        panel = self.window.bot_tab
        panel.game_selector.set_process_status(False, "Ventana no encontrada")
        spins = (
            panel.auto_panel.auto_target.interval_spin,
            panel.auto_panel.auto_attack.interval_spin,
            panel.auto_panel.auto_loot.interval_spin,
            panel.auto_panel.auto_pot1.threshold_spin,
            panel.auto_panel.auto_pot1.interval_spin,
            panel.auto_panel.auto_mp.threshold_spin,
            panel.auto_panel.auto_mp.interval_spin,
            panel.auto_panel.auto_heal.threshold_spin,
            panel.auto_panel.auto_heal.interval_spin,
            *(skill.time_spin for skill in panel.rotation_panel.skills),
        )
        for spin in spins:
            spin.setValue(spin.maximum())
        self.app.processEvents()

        status = panel.game_selector.status_label
        self.assertGreaterEqual(
            status.contentsRect().width(),
            status.fontMetrics().horizontalAdvance(status.text()),
        )
        for spin in spins:
            editor = spin.lineEdit()
            self.assertGreaterEqual(
                editor.contentsRect().width(),
                editor.fontMetrics().horizontalAdvance(editor.text()),
                spin.objectName() or spin.text(),
            )

    def _assert_inside(self, widget, parent):
        geometry = widget.geometry()
        self.assertGreaterEqual(geometry.left(), 0, type(widget).__name__)
        self.assertGreaterEqual(geometry.top(), 0, type(widget).__name__)
        self.assertLess(geometry.right(), parent.width(), type(widget).__name__)
        self.assertLess(geometry.bottom(), parent.height(), type(widget).__name__)


if __name__ == "__main__":
    unittest.main()
