from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QCheckBox,QVBoxLayout, QGridLayout, QGroupBox, QLabel, QPushButton, QSpinBox

class FeatureCard(QGroupBox):

    def __init__(self, title: str, default_interval: int, default_key: str | None = None):

        super().__init__()

        self.title = title
        self.default_key = default_key
        self.default_interval = default_interval

        self.setup_ui()

    def setup_ui(self):

        layout = QGridLayout()

        layout.setContentsMargins(10,10,10,10)
        layout.setHorizontalSpacing(15)
        layout.setSpacing(8)

        self.enabled_checkbox = QCheckBox(self.title)

        font = self.enabled_checkbox.font()
        font.setBold(True)
        self.enabled_checkbox.setFont(font)

        layout.addWidget(self.enabled_checkbox, 0, 0, 1, 2)

        self.key_label = QLabel("Tecla")
        self.key_button = QPushButton(self.default_key)
        self.key_button.setFixedSize(30,25)

        layout.addWidget(self.key_label, 1, 0)
        layout.addWidget(self.key_button,1,1,alignment=Qt.AlignmentFlag.AlignRight,)

        self.interval_label = QLabel("Intervalo")

        self.interval_spinbox = QSpinBox()

        self.interval_spinbox.setMinimum(500)
        self.interval_spinbox.setMaximum(3000000)
        self.interval_spinbox.setSingleStep(500)
        self.interval_spinbox.setSuffix(" ms")
        self.interval_spinbox.setFixedSize(100,20)
        self.interval_spinbox.setValue(self.default_interval)

        layout.addWidget(self.interval_label, 2, 0)
        layout.addWidget(self.interval_spinbox,2,1,alignment=Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

        def is_enabled(self) -> bool:
            return self.enabled_checkbox.isChecked()

        def set_enabled(self, enabled: bool):
            self.enabled_checkbox.setChecked(enabled)

        def key(self) -> str:
            return self.key_button.text()

        def set_key(self, key:str):
            self.key_button.setText(key)

        def interval(self):
            self.interval_spinbox.value()

        def set_interval(self, interval: int):
            self.interval_spinbox.setValue(interval)
