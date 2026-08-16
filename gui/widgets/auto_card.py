from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QWidget,
)


class AutoCard(QWidget):

    def __init__(self, name, key, interval=250, show_interval=False):
        super().__init__()
        self._interval = interval
        self.interval_spin = None
        self.create_widgets(name, key, show_interval)
        self.create_layout()
        self.apply_style()

    def create_widgets(self, name, key, show_interval):
        self.checkbox = QCheckBox(name)
        self.checkbox.setToolTip(f"Activa o desactiva {name}.")
        self.key_button = QPushButton(key)
        self.key_button.setFixedSize(35, 25)
        self.key_button.setToolTip(
            f"Tecla {key} que el bot enviará cuando {name} esté activo."
        )

        if show_interval:
            self.interval_spin = QSpinBox()
            self.interval_spin.setRange(100, 600000)
            self.interval_spin.setSingleStep(100)
            self.interval_spin.setValue(self._interval)
            self.interval_spin.setSuffix(" ms")
            self.interval_spin.setFixedWidth(90)
            self.interval_spin.setToolTip(
                f"Intervalo mínimo entre ejecuciones de {name}."
            )

    def create_layout(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.key_button)

        if self.interval_spin:
            layout.addWidget(self.interval_spin)

        layout.addStretch()

    def apply_style(self):
        self.key_button.setStyleSheet(
            """
            QPushButton {
                background-color: #173B6D;
                color: white;
                border-radius: 6px;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #28558F; }
            QPushButton:pressed { background-color: #102A4D; }
            """
        )

    def is_enabled(self):
        return self.checkbox.isChecked()

    def interval(self):
        if self.interval_spin:
            return self.interval_spin.value()
        return self._interval

    def key(self):
        return self.key_button.text()

    def set_enabled(self, value):
        self.checkbox.setChecked(value)

    def lock(self):
        self.checkbox.setEnabled(False)
        self.key_button.setEnabled(False)
        if self.interval_spin:
            self.interval_spin.setEnabled(False)

    def unlock(self):
        self.checkbox.setEnabled(True)
        self.key_button.setEnabled(True)
        if self.interval_spin:
            self.interval_spin.setEnabled(True)
