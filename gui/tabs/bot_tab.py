from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
)
from PySide6.QtCore import QTimer, Signal

from gui.widgets.game_selector import GameSelector
from gui.widgets.character_group import CharacterGroup
from gui.widgets.target_group import TargetGroup

from gui.right_panel import RightPanel
from gui.center_panel import CenterPanel

from gui.widgets.bot_control_bar import BotControlBar
from core.models.automation_config import config_from_widgets





class BotTab(QWidget):

    configuration_changed = Signal(object)


    def __init__(self, game_profiles=None):

        super().__init__()

        self.game_profiles = game_profiles

        self._config_revision = 0

        self.create_widgets()

        self.create_layout()

        self.apply_style()

        self.create_config_updates()






    def create_widgets(self):


        self.game_selector = GameSelector(self.game_profiles)

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

    def create_config_updates(self):

        self.config_timer = QTimer(self)
        self.config_timer.setSingleShot(True)
        self.config_timer.setInterval(75)
        self.config_timer.timeout.connect(self.emit_configuration)

        for card in self.rotation_panel.skills:
            card.enabled_checkbox.toggled.connect(
                self.schedule_configuration
            )
            card.time_spin.valueChanged.connect(
                self.schedule_configuration
            )

        for card in (
            self.auto_panel.auto_target,
            self.auto_panel.auto_attack,
            self.auto_panel.auto_loot,
        ):
            card.checkbox.toggled.connect(self.schedule_configuration)
            if card.interval_spin is not None:
                card.interval_spin.valueChanged.connect(
                    self.schedule_configuration
                )

        for card in (
            self.auto_panel.auto_pot1,
            self.auto_panel.auto_mp,
            self.auto_panel.auto_heal,
        ):
            card.checkbox.toggled.connect(self.schedule_configuration)
            card.threshold_spin.valueChanged.connect(
                self.schedule_configuration
            )
            card.interval_spin.valueChanged.connect(
                self.schedule_configuration
            )

        self.auto_panel.ignore_targets.toggled.connect(
            self.schedule_configuration
        )
        self.auto_panel.enemy_ignores_changed.connect(
            self.schedule_configuration
        )
        self.character_group.mode_selector.currentIndexChanged.connect(
            self.schedule_configuration
        )
        self.character_group.quiet_seconds.valueChanged.connect(
            self.schedule_configuration
        )

    def schedule_configuration(self, *_args):

        self.config_timer.start()

    def build_configuration(self):

        self._config_revision += 1
        return config_from_widgets(
            self.auto_panel,
            self.rotation_panel,
            self.character_group,
            revision=self._config_revision,
        )

    def emit_configuration(self):

        self.configuration_changed.emit(self.build_configuration())









    def lock_controls(self):

        self.game_selector.set_locked(True)
        self.rotation_panel.lock_controls()






    def unlock_controls(self):

        self.game_selector.set_locked(False)
        self.rotation_panel.unlock_controls()
