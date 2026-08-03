from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
)


class AutoCard(QWidget):


    def __init__(self, name, key):

        super().__init__()

        self.create_widgets(
            name,
            key
        )

        self.create_layout()

        self.apply_style()






    def create_widgets(self, name, key):


        self.checkbox = QCheckBox(
            name
        )


        self.key_button = QPushButton(
            key
        )


        self.key_button.setFixedSize(
            35,
            25
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
            6
        )


        layout.addWidget(
            self.checkbox
        )


        layout.addWidget(
            self.key_button
        )





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


            QPushButton:hover {

                background-color: #28558F;

            }


            QPushButton:pressed {

                background-color: #102A4D;

            }

            """
        )







    def is_enabled(self):

        return self.checkbox.isChecked()






    def interval(self):

        return 500






    def key(self):

        return self.key_button.text()






    def set_enabled(self, value):

        self.checkbox.setChecked(
            value
        )







    def lock(self):

        self.checkbox.setEnabled(
            False
        )


        self.key_button.setEnabled(
            False
        )







    def unlock(self):

        self.checkbox.setEnabled(
            True
        )


        self.key_button.setEnabled(
            True
        )