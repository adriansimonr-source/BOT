from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QSpinBox,
)

from PySide6.QtCore import Qt





class SkillCard(QWidget):


    def __init__(self, skill_key):

        super().__init__()

        self.skill_key = str(skill_key)

        self.create_widgets()

        self.create_layout()





    def create_widgets(self):


        self.enabled_checkbox = QCheckBox()



        self.skill_label = QLabel(
            self.skill_key
        )


        self.skill_label.setAlignment(
            Qt.AlignCenter
        )


        self.skill_label.setFixedWidth(
            25
        )



        self.time_spin = QSpinBox()


        self.time_spin.setRange(
            500,
            6000000
        )


        self.time_spin.setValue(
            500
        )


        self.time_spin.setSingleStep(
            500
        )


        self.time_spin.setSuffix(
            " ms"
        )


        self.time_spin.setFixedWidth(
            75
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
            self.enabled_checkbox
        )


        layout.addWidget(
            self.skill_label
        )


        layout.addWidget(
            self.time_spin
        )








    def is_enabled(self):

        return self.enabled_checkbox.isChecked()





    def set_enabled(self, enabled):

        self.enabled_checkbox.setChecked(
            enabled
        )





    def time(self):

        return self.time_spin.value()





    def set_time(self, value):

        self.time_spin.setValue(
            value
        )





    def skill_number(self):

        return self.skill_key





    def lock(self):

        self.enabled_checkbox.setEnabled(
            False
        )

        self.time_spin.setEnabled(
            False
        )





    def unlock(self):

        self.enabled_checkbox.setEnabled(
            True
        )

        self.time_spin.setEnabled(
            True
        )