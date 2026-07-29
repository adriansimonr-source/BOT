from PySide6.QtWidgets import QVBoxLayout, QWidget, QPushButton
from gui.widgets.character_group import CharacterGroup
from gui.widgets.process_group import ProcessGroup
from gui.widgets.profile_group import ProfileGroup


class LeftPanel(QWidget):

    def __init__(self):
        super().__init__()

        self.setup_ui()

    def setup_ui(self):

        self.setMaximumWidth(190)

        layout = QVBoxLayout()

        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(10)

        self.character_group = CharacterGroup()
        self.process_group = ProcessGroup()
        self.profile_group = ProfileGroup()

        layout.addWidget(self.character_group)
        layout.addWidget(self.process_group)
        layout.addWidget(self.profile_group)

        layout.addStretch()
        self.startbutton = QPushButton ("INICIAR")
        layout.addWidget(self.startbutton)

        self.setLayout(layout)