import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from gui.main_window import MainWindow


class _GameProfiles:
    @staticmethod
    def get_games():
        return [{"id": "kathana", "name": "Kathana"}]


class CompactGuiLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

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

    def test_window_and_content_fit_the_compact_geometry(self):
        self.assertEqual(self.window.size(), QSize(480, 320))
        self.assertLess(self.window.width(), 500)
        self.assertLess(self.window.height(), 400)
        panel = self.window.bot_tab
        self.assertLessEqual(panel.minimumSizeHint().width(), panel.width())
        self.assertLessEqual(panel.minimumSizeHint().height(), panel.height())

        for widget in (
            panel.game_selector,
            panel.bot_controls,
            panel.character_group,
            panel.target_group,
            panel.auto_panel,
            panel.rotation_panel,
        ):
            geometry = widget.geometry()
            self.assertGreaterEqual(geometry.left(), 0)
            self.assertGreaterEqual(geometry.top(), 0)
            self.assertLess(geometry.right(), panel.width())
            self.assertLess(geometry.bottom(), panel.height())

    def test_start_button_is_at_the_right_of_the_game_row(self):
        panel = self.window.bot_tab
        game_geometry = panel.game_selector.geometry()
        controls_geometry = panel.bot_controls.geometry()

        self.assertEqual(game_geometry.top(), controls_geometry.top())
        self.assertGreater(controls_geometry.left(), game_geometry.left())
        self.assertLess(controls_geometry.bottom(), panel.character_group.geometry().top())
        self.assertEqual(panel.bot_controls.start_button.size(), QSize(130, 24))

    def test_target_lists_are_narrow_and_do_not_overlap(self):
        panel = self.window.bot_tab.auto_panel
        available = panel.available_list.geometry()
        ignored = panel.ignored_list.geometry()

        self.assertEqual(available.size(), QSize(92, 46))
        self.assertEqual(ignored.size(), QSize(92, 46))
        self.assertLess(available.right(), ignored.left())

    def test_resources_and_status_sections_use_compact_rows(self):
        panel = self.window.bot_tab
        character = panel.character_group
        self.assertEqual(character.hp_bar.width(), 120)
        self.assertEqual(character.mp_bar.width(), 120)
        self.assertEqual(character.hp_bar.geometry().top(), character.mp_bar.geometry().top())
        self.assertLess(character.geometry().bottom(), panel.target_group.geometry().top())
        self.assertLess(panel.target_group.geometry().bottom(), panel.auto_panel.geometry().top())
        self.assertLess(panel.auto_panel.geometry().right(), panel.rotation_panel.geometry().left())

    def test_target_level_and_enemy_hp_are_adjacent(self):
        target_group = self.window.bot_tab.target_group
        target_group.target_name_label.setText("TARGET: Mlecchas Karmana")
        target_group.level_label.setText("LVL: 999")
        self.app.processEvents()

        target = target_group.target_name_label.geometry()
        level = target_group.level_label.geometry()
        hp = target_group.hp_bar.geometry()

        self.assertEqual(level.left() - target.right() - 1, 4)
        self.assertEqual(hp.left() - level.right() - 1, 4)
        self.assertLessEqual(
            target_group.target_name_label.fontMetrics().horizontalAdvance(
                target_group.target_name_label.text()
            ),
            target.width(),
        )
        self.assertLessEqual(
            target_group.level_label.fontMetrics().horizontalAdvance(
                target_group.level_label.text()
            ),
            level.width(),
        )
        self.assertLess(hp.right(), target_group.width())


if __name__ == "__main__":
    unittest.main()
