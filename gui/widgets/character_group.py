from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout
from gui.widgets.status_indicator import StatusIndicator

class CharacterGroup(QGroupBox):

    def __init__(self):
        super().__init__("PERSONAJE")
        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        layout.addWidget(QLabel("NOMBRE"))

        self.character_name_label = QLabel("No detectado")
        layout.addWidget(self.character_name_label)

        layout.addWidget(QLabel("ESTADO"))

        self.character_status_indicator = StatusIndicator()
        layout.addWidget(self.character_status_indicator)

        self.setLayout(layout)

    def set_name(self, name:str):
        self.character_name.setText(name)

    def clear_name(self):
        self.character_name.setText("No detectado")

    def connected(self):
        self.character_status.connected()

    def disconnected(self):
        self.character_status.disconnected()

    def detecting(self):
        self.character_status.detecting()

    def running(self):
        self.character_status.running()

    def paused(self):
        self.character_status.paused()      