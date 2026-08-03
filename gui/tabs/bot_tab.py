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

        self.apply_style()






    def create_widgets(self):


        self.game_selector = GameSelector()

        self.character_group = CharacterGroup()

        self.target_group = TargetGroup()

        self.auto_panel = RightPanel()

        self.rotation_panel = CenterPanel()

        self.bot_controls = BotControlBar()






    def create_layout(self):


        main_layout = QVBoxLayout(self)


        main_layout.setContentsMargins(
            5,
            5,
            5,
            5
        )


        main_layout.setSpacing(
            6
        )



        main_layout.addWidget(
            self.game_selector
        )



        top_layout = QGridLayout()


        top_layout.setHorizontalSpacing(
            6
        )


        top_layout.setVerticalSpacing(
            6
        )


        top_layout.addWidget(
            self.character_group,
            0,
            0
        )


        top_layout.addWidget(
            self.target_group,
            0,
            1
        )


        top_layout.setColumnStretch(
            0,
            7
        )


        top_layout.setColumnStretch(
            1,
            3
        )


        main_layout.addLayout(
            top_layout
        )





        bottom_layout = QGridLayout()


        bottom_layout.setHorizontalSpacing(
            6
        )


        bottom_layout.setVerticalSpacing(
            6
        )


        bottom_layout.addWidget(
            self.auto_panel,
            0,
            0
        )


        bottom_layout.addWidget(
            self.rotation_panel,
            0,
            1
        )


        bottom_layout.setColumnStretch(
            0,
            7
        )


        bottom_layout.setColumnStretch(
            1,
            3
        )


        main_layout.addLayout(
            bottom_layout
        )



        main_layout.addWidget(
            self.bot_controls
        )








    def apply_style(self):


        card_style = """

        QWidget {

            background-color: white;

        }

        QGroupBox {

            border: 1px solid #D5E2F2;

            border-radius: 8px;

            margin-top: 2px;

            padding: 8px;

        }

        """



        for widget in (

            self.character_group,

            self.target_group,

            self.auto_panel,

            self.rotation_panel

        ):

            widget.setStyleSheet(
                card_style
            )









    def lock_controls(self):


        self.auto_panel.lock_controls()

        self.rotation_panel.lock_controls()






    def unlock_controls(self):


        self.auto_panel.unlock_controls()

        self.rotation_panel.unlock_controls()