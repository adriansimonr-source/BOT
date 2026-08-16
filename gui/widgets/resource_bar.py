from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget


class ResourceBar(QWidget):
    def __init__(self, name):
        super().__init__()
        self.label = QLabel(name)
        self.bar = QProgressBar()
        self.value_label = QLabel("0%")
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.label.setFixedWidth(25)
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(12)
        self.bar.setFixedWidth(350)
        self.value_label.setFixedWidth(35)
        layout.addWidget(self.label)
        layout.addWidget(self.bar)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def update_percent(self, value):
        if value is None:
            self.bar.setValue(0)
            self.value_label.setText("--")
            return
        value = max(0, min(100, int(value)))
        self.bar.setValue(value)
        self.value_label.setText(f"{value}%")
