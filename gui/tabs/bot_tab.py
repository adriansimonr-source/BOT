from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
)
from PySide6.QtCore import QTimer, Signal

from gui.widgets.game_selector import GameSelector
from gui.widgets.character_group import CharacterGroup
from gui.widgets.target_group import TargetGroup
from gui.widgets.profile_selector import ProfileSelector

from gui.right_panel import RightPanel
from gui.center_panel import CenterPanel

from gui.widgets.bot_control_bar import BotControlBar
from core.models.automation_config import config_from_widgets





class BotTab(QWidget):

    configuration_changed = Signal(object)

    PROFILE_VERSION = 1


    def __init__(self, game_profiles=None):

        super().__init__()

        self.game_profiles = game_profiles

        self._config_revision = 0

        self.create_widgets()

        self.create_layout()

        self.apply_style()

        self.create_config_updates()

        self._default_profile_settings = self.get_profile_settings()






    def create_widgets(self):


        self.game_selector = GameSelector(self.game_profiles)

        self.character_group = CharacterGroup()

        self.target_group = TargetGroup()

        self.profile_selector = ProfileSelector()

        self.auto_panel = RightPanel()

        self.rotation_panel = CenterPanel()

        self.bot_controls = BotControlBar()






    def create_layout(self):


        main_layout = QVBoxLayout(self)


        main_layout.setContentsMargins(
            2,
            2,
            2,
            2
        )


        main_layout.setSpacing(
            3
        )

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(3)
        header_layout.addWidget(self.game_selector, 1)
        header_layout.addWidget(self.bot_controls)
        main_layout.addLayout(header_layout)



        main_layout.addWidget(self.character_group)
        target_layout = QHBoxLayout()
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.setSpacing(3)
        target_layout.addWidget(self.target_group, 3)
        target_layout.addWidget(self.profile_selector, 2)
        main_layout.addLayout(target_layout)





        bottom_layout = QGridLayout()


        bottom_layout.setHorizontalSpacing(
            3
        )


        bottom_layout.setVerticalSpacing(
            3
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
            51
        )


        bottom_layout.setColumnStretch(
            1,
            49
        )


        main_layout.addLayout(
            bottom_layout
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

            self.profile_selector,

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

    def get_profile_settings(self):
        action_cards = {
            "auto_target": self.auto_panel.auto_target,
            "auto_attack": self.auto_panel.auto_attack,
            "auto_loot": self.auto_panel.auto_loot,
        }
        resource_cards = {
            "auto_pot1": self.auto_panel.auto_pot1,
            "auto_mp": self.auto_panel.auto_mp,
            "auto_heal": self.auto_panel.auto_heal,
        }
        return {
            "version": self.PROFILE_VERSION,
            "actions": {
                name: {
                    "enabled": card.is_enabled(),
                    "interval_ms": card.interval(),
                }
                for name, card in action_cards.items()
            },
            "resources": {
                name: {
                    "enabled": card.is_enabled(),
                    "threshold_percent": card.threshold(),
                    "interval_ms": card.interval(),
                }
                for name, card in resource_cards.items()
            },
            "skills": {
                card.skill_number(): {
                    "enabled": card.is_enabled(),
                    "interval_ms": card.time(),
                }
                for card in self.rotation_panel.skills
            },
            "ignore_enabled": self.auto_panel.ignore_targets.isChecked(),
        }

    def apply_profile_settings(self, settings):
        if not isinstance(settings, dict):
            return False

        applied = False
        actions = settings.get("actions")
        if isinstance(actions, dict):
            for name in ("auto_target", "auto_attack", "auto_loot"):
                values = actions.get(name)
                card = getattr(self.auto_panel, name)
                if isinstance(values, dict):
                    applied |= self._apply_checkbox(
                        card.checkbox,
                        values.get("enabled"),
                    )
                    applied |= self._apply_spinbox(
                        card.interval_spin,
                        values.get("interval_ms"),
                    )

        resources = settings.get("resources")
        if isinstance(resources, dict):
            for name in ("auto_pot1", "auto_mp", "auto_heal"):
                values = resources.get(name)
                card = getattr(self.auto_panel, name)
                if isinstance(values, dict):
                    applied |= self._apply_checkbox(
                        card.checkbox,
                        values.get("enabled"),
                    )
                    applied |= self._apply_spinbox(
                        card.threshold_spin,
                        values.get("threshold_percent"),
                    )
                    applied |= self._apply_spinbox(
                        card.interval_spin,
                        values.get("interval_ms"),
                    )

        skills = settings.get("skills")
        if isinstance(skills, dict):
            for card in self.rotation_panel.skills:
                values = skills.get(card.skill_number())
                if isinstance(values, dict):
                    applied |= self._apply_checkbox(
                        card.enabled_checkbox,
                        values.get("enabled"),
                    )
                    applied |= self._apply_spinbox(
                        card.time_spin,
                        values.get("interval_ms"),
                    )

        applied |= self._apply_checkbox(
            self.auto_panel.ignore_targets,
            settings.get("ignore_enabled"),
        )
        if applied:
            self.schedule_configuration()
        return applied

    def reset_profile_settings(self):
        return self.apply_profile_settings(self._default_profile_settings)

    @staticmethod
    def _apply_checkbox(checkbox, value):
        if not isinstance(value, bool):
            return False
        checkbox.setChecked(value)
        return True

    @staticmethod
    def _apply_spinbox(spinbox, value):
        if value is None or isinstance(value, bool):
            return False
        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            return False
        spinbox.setValue(numeric_value)
        return True









    def lock_controls(self):

        self.game_selector.set_locked(True)
        self.rotation_panel.lock_controls()
        self.profile_selector.set_locked(True)






    def unlock_controls(self):

        self.game_selector.set_locked(False)
        self.rotation_panel.unlock_controls()
        self.profile_selector.set_locked(False)
