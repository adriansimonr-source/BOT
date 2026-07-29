from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout,QPushButton
from gui.widgets.status_indicator import StatusIndicator

class ProcessGroup(QGroupBox):

    def __init__(self):
        super().__init__("PROCESO")
        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        layout.addWidget(QLabel("ESTADO"))
        self.process_status = StatusIndicator()
        layout.addWidget(self.process_status)
       
        layout.addWidget(QLabel("PROCESO"))
        self.process_name = QLabel("Ningun proceso")
        layout.addWidget(self.process_name)

        self.detect_process_button = QPushButton("Detectar proceso")
        layout.addWidget(self.detect_process_button)

        self.setLayout(layout)
       
        def set_process_name(self, process_name:str):
            self.process_name.setText(process_name)
       
        def clear_process_name(self):
            self.process_name.setText("Ningun proceso detectad")
       
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