from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
)

from gui.widgets.character_group import CharacterGroup
from gui.widgets.process_group import ProcessGroup
from gui.widgets.profile_group import ProfileGroup
from gui.widgets.status_indicator import StatusIndicator


class LeftPanel(QWidget):

    def __init__(self):
        super().__init__()

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):

        self.character_group = CharacterGroup()
        self.process_group = ProcessGroup()
        self.profile_group = ProfileGroup()

        # Estado del bot
        self.bot_status = StatusIndicator()
        self.bot_status.paused()

        # Botón principal
        self.start_button = QPushButton("INICIAR")
        self.start_button.setMinimumHeight(40)

    def create_layout(self):

        layout = QVBoxLayout()

        layout.addWidget(self.character_group)
        layout.addWidget(self.process_group)
        layout.addWidget(self.profile_group)

        layout.addSpacing(10)

        layout.addWidget(self.bot_status)

        layout.addWidget(self.start_button)

        layout.addStretch()

        self.setLayout(layout)

    # ---------------------------------
    # Estados del botón
    # ---------------------------------

    def set_running(self):

        self.bot_status.running()
        self.start_button.setText("DETENER")

    def set_stopped(self):

        self.bot_status.paused()
        self.start_button.setText("INICIAR")