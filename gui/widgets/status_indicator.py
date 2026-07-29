from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget
from enum import Enum

class Status(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTED = "Connected"
    DETECTING = "Detecting"
    RUNNING = "Running"
    PAUSED = "Paused"

class StatusIndicator(QWidget):

    STATUS = {
        Status.DISCONNECTED: ("#d32f2f", "Desconectado"),
        Status.CONNECTED: ("#2e7d32", "Conectado" ),
        Status.DETECTING: ("#f9a825", "Detectando..."),
        Status.RUNNING: ("#1976d2", "Ejecutando"),
        Status.PAUSED: ("#ef6c00", "Pausado"),
    }

    def __init__(self):
        super().__init__()

        self.circle = QLabel()
        self.circle.setFixedSize(12,12)
        self.text = QLabel()

        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(8)

        layout.addWidget(self.circle)
        layout.addWidget(self.text)
        layout.addStretch()

        self.setLayout(layout)
        self.set_status(Status.DISCONNECTED)

    def set_status(self, status):

        if status not in self.STATUS:
            return

        color, text = self.STATUS[status]

        self.circle.setStyleSheet(f"""background-color: {color};
        border-radius: 6px;
        """)

        self.text.setText(text)

    def connected(self):
        self.set_status(Status.CONNECTED)
    def disconnected(self):
        self.set_status(Status.DISCONNECTED)
    def detecting(self):
        self.set_status(Status.DETECTING)
    def running(self):
        self.set_status(Status.RUNNING)
    def paused(self):
        self.set_status(Status.PAUSED)