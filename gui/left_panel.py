from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
)

from gui.widgets.character_group import CharacterGroup
from gui.widgets.target_group import TargetGroup
from gui.widgets.process_group import ProcessGroup
from gui.widgets.profile_group import ProfileGroup
from gui.widgets.status_indicator import StatusIndicator


class LeftPanel(QWidget):

    def __init__(self):

        super().__init__()

        self.create_widgets()
        self.create_layout()


    # =====================================
    # Crear widgets
    # =====================================

    def create_widgets(self):

        # Información personaje
        self.character_group = CharacterGroup()

        # Información objetivo
        self.target_group = TargetGroup()


        # Proceso
        self.process_group = ProcessGroup()


        # Perfil
        self.profile_group = ProfileGroup()


        # Estado bot

        self.bot_status = StatusIndicator()

        self.bot_status.paused()


        # Botón principal

        self.start_button = QPushButton(
            "INICIAR"
        )

        self.start_button.setMinimumHeight(
            40
        )

        self.start_button.setEnabled(
            False
        )


    # =====================================
    # Layout
    # =====================================

    def create_layout(self):

        layout = QVBoxLayout()


        # Personaje

        layout.addWidget(
            self.character_group
        )


        # Objetivo

        layout.addWidget(
            self.target_group
        )


        # Proceso

        layout.addWidget(
            self.process_group
        )


        # Perfil

        layout.addWidget(
            self.profile_group
        )


        layout.addSpacing(
            10
        )


        # Estado

        layout.addWidget(
            self.bot_status
        )


        # Botón

        layout.addWidget(
            self.start_button
        )


        layout.addStretch()


        self.setLayout(
            layout
        )


    # =====================================
    # Estados del bot
    # =====================================

    def set_running(self):

        self.bot_status.running()

        self.start_button.setText(
            "DETENER"
        )


    def set_stopped(self):

        self.bot_status.paused()

        self.start_button.setText(
            "INICIAR"
        )


    def enable_start_button(self):

        self.start_button.setEnabled(
            True
        )


    def disable_start_button(self):

        self.start_button.setEnabled(
            False
        )