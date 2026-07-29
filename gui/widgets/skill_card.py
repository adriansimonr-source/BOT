from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QSpinBox,
)
from PySide6.QtCore import Qt


class SkillCard(QWidget):

    def __init__(self, skill_number: int):
        super().__init__()

        self.enabled_checkbox = QCheckBox()

        self.skill_label = QLabel(str(skill_number))
        self.skill_label.setAlignment(Qt.AlignCenter)
        self.skill_label.setFixedWidth(20)

        self.time_spin = QSpinBox()
        self.time_spin.setRange(50, 60000)
        self.time_spin.setValue(500)
        self.time_spin.setSuffix(" ms")
        self.time_spin.setFixedWidth(90)

        layout = QHBoxLayout()

        layout.addWidget(self.enabled_checkbox)
        layout.addWidget(self.skill_label)
        layout.addSpacing(10)
        layout.addWidget(self.time_spin)
        layout.addStretch()

        layout.setContentsMargins(5, 2, 5, 2)

        self.setLayout(layout)

    # -------------------------
    # API pública
    # -------------------------

    def is_enabled(self):
        return self.enabled_checkbox.isChecked()

    def set_enabled(self, enabled: bool):
        self.enabled_checkbox.setChecked(enabled)

    def time(self):
        return self.time_spin.value()

    def set_time(self, value: int):
        self.time_spin.setValue(value)