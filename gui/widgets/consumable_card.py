from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QSpinBox,
)

class ConsumableCard(QWidget):

    def __init__(
        self,
        name,
        key,
        threshold=40,
        interval=2000
    ):

        super().__init__()

        self._key = key

        self.create_widgets(
            name,
            threshold,
            interval
        )

        self.create_layout()

    def create_widgets(
        self,
        name,
        threshold,
        interval
    ):

        self.checkbox = QCheckBox(
            name
        )

        self.checkbox.setToolTip(
            f"Activa o desactiva {name}."
        )

        self.threshold_spin = QSpinBox()

        self.threshold_spin.setRange(
            0,
            100
        )

        self.threshold_spin.setValue(
            threshold
        )

        self.threshold_spin.setSuffix(
            " %"
        )

        self.threshold_spin.setFixedWidth(
            52
        )

        resource = "MP" if "MP" in name.upper() else "HP"
        self.threshold_spin.setToolTip(
            f"Usar {self._key} cuando el {resource} sea igual o inferior "
            "a este porcentaje."
        )

        self.interval_spin = QSpinBox()

        self.interval_spin.setRange(
            100,
            600000
        )

        self.interval_spin.setSingleStep(
            100
        )

        self.interval_spin.setValue(
            interval
        )

        self.interval_spin.setSuffix(
            " ms"
        )

        self.interval_spin.setFixedWidth(
            74
        )

        self.interval_spin.setToolTip(
            f"Tiempo mínimo antes de reintentar la tecla {self._key}."
        )

    def create_layout(self):

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            3
        )

        layout.addWidget(
            self.checkbox
        )

        layout.addWidget(
            self.threshold_spin
        )

        layout.addWidget(
            self.interval_spin
        )

        layout.addStretch()

    def is_enabled(self):

        return self.checkbox.isChecked()

    def key(self):

        return self._key

    def threshold(self):

        return self.threshold_spin.value()

    def interval(self):

        return self.interval_spin.value()

    def set_enabled(
        self,
        value
    ):

        self.checkbox.setChecked(
            value
        )

    def lock(self):

        self.checkbox.setEnabled(
            False
        )

        self.threshold_spin.setEnabled(
            False
        )

        self.interval_spin.setEnabled(
            False
        )

    def unlock(self):

        self.checkbox.setEnabled(
            True
        )

        self.threshold_spin.setEnabled(
            True
        )

        self.interval_spin.setEnabled(
            True
        )
