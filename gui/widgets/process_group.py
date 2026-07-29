from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QPushButton

from gui.widgets.status_indicator import StatusIndicator


class ProcessGroup(QGroupBox):

    def __init__(self):
        super().__init__("PROCESO")
        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        # Estado
        layout.addWidget(QLabel("ESTADO"))

        self.process_status = StatusIndicator()
        layout.addWidget(self.process_status)

        # Nombre del proceso
        layout.addWidget(QLabel("PROCESO"))

        self.process_name = QLabel("Ningún proceso")
        layout.addWidget(self.process_name)

        # PID
        layout.addWidget(QLabel("PID"))

        self.process_pid = QLabel("-")
        layout.addWidget(self.process_pid)

        # Botón detectar
        self.detect_process_button = QPushButton("Detectar proceso")
        layout.addWidget(self.detect_process_button)

        self.setLayout(layout)

    # ==================================================
    # Información del proceso
    # ==================================================

    def set_process(self, process_name: str, pid: int):
        """Actualiza nombre y PID del proceso."""
        self.process_name.setText(process_name)
        self.process_pid.setText(str(pid))

    def clear_process(self):
        """Limpia la información del proceso."""
        self.process_name.setText("Ningún proceso")
        self.process_pid.setText("-")

    # ==================================================
    # Estado del proceso
    # ==================================================

    def connected(self):
        self.process_status.connected()

    def disconnected(self):
        self.process_status.disconnected()

    def detecting(self):
        self.process_status.detecting()

    def running(self):
        self.process_status.running()

    def paused(self):
        self.process_status.paused()