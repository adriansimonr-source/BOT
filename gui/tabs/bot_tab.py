from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
)

from gui.widgets.game_selector import GameSelector

from gui.widgets.character_group import CharacterGroup
from gui.widgets.target_group import TargetGroup

from gui.right_panel import RightPanel
from gui.center_panel import CenterPanel

from gui.widgets.bot_control_bar import BotControlBar



class BotTab(QWidget):

    def __init__(self):

        super().__init__()

        self.create_widgets()
        self.create_layout()


    def create_widgets(self):

        self.game_selector = GameSelector()

        self.character_group = CharacterGroup()

        self.target_group = TargetGroup()

        self.auto_panel = RightPanel()

        self.rotation_panel = CenterPanel()

        self.bot_controls = BotControlBar()



    def create_layout(self):

        main_layout = QVBoxLayout()


        main_layout.addWidget(
            self.game_selector
        )


        grid = QGridLayout()

        grid.setHorizontalSpacing(
            10
        )

        grid.setVerticalSpacing(
            10
        )


        grid.addWidget(
            self.character_group,
            0,
            0
        )


        grid.addWidget(
            self.target_group,
            0,
            1
        )


        grid.addWidget(
            self.auto_panel,
            1,
            0
        )


        grid.addWidget(
            self.rotation_panel,
            1,
            1
        )


        main_layout.addLayout(
            grid
        )


        main_layout.addWidget(
            self.bot_controls
        )


        self.setLayout(
            main_layout
        )



    def lock_controls(self):

        self.auto_panel.lock_controls()

        self.rotation_panel.lock_controls()



    def unlock_controls(self):

        self.auto_panel.unlock_controls()

        self.rotation_panel.unlock_controls()