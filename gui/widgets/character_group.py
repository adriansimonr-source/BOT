from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QComboBox,
)

from gui.widgets.status_indicator import StatusIndicator
from gui.widgets.resource_bar import ResourceBar



class CharacterGroup(QWidget):


    def __init__(self):

        super().__init__()

        self.create_widgets()
        self.create_layout()



    def create_widgets(self):

        self.character_name_label = QLabel(
            "NAME: ---"
        )


        self.refresh_name_button = QPushButton(
            "⟳"
        )


        self.level_label = QLabel(
            "LVL: -"
        )


        self.character_status_indicator = StatusIndicator()


        self.online_label = QLabel(
            "OFFLINE"
        )


        self.hp_bar = ResourceBar(
            "HP"
        )


        self.mp_bar = ResourceBar(
            "MP"
        )


        self.current_position_label = QLabel(
            "0 / 0"
        )


        self.start_position_label = QLabel(
            "0 / 0"
        )


        self.refresh_position_button = QPushButton(
            "⟳"
        )


        self.lock_position_button = QPushButton(
            "📌"
        )


        self.unlock_position_button = QPushButton(
            "🔓"
        )


        self.mode_selector = QComboBox()

        self.mode_selector.addItems(
            [
                "BOT STATIC",
                "100",
                "250",
                "500",
                "SIN LIMITES"
            ]
        )


        self.apply_button_style()





    def apply_button_style(self):

        buttons = [
            self.refresh_name_button,
            self.refresh_position_button,
            self.lock_position_button,
            self.unlock_position_button,
        ]


        for button in buttons:

            button.setFixedSize(
                30,
                24
            )


            button.setStyleSheet(
                """
                QPushButton {

                    background-color: #173B6D;
                    color: white;
                    border-radius: 6px;
                    border: none;
                    font-size: 13px;

                }

                QPushButton:hover {

                    background-color: #28558F;

                }

                QPushButton:pressed {

                    background-color: #102A4D;

                }
                """
            )






    def create_layout(self):


        main_layout = QVBoxLayout(
            self
        )


        main_layout.setContentsMargins(
            4,
            4,
            4,
            4
        )


        main_layout.setSpacing(
            4
        )



        header = QHBoxLayout()


        header.setSpacing(
            5
        )


        header.addWidget(
            self.character_name_label
        )


        header.addWidget(
            self.refresh_name_button
        )


        header.addWidget(
            self.level_label
        )


        header.addWidget(
            self.character_status_indicator
        )


        header.addWidget(
            self.online_label
        )


        header.addStretch()



        main_layout.addLayout(
            header
        )



        main_layout.addWidget(
            self.hp_bar
        )


        main_layout.addWidget(
            self.mp_bar
        )



        position = QHBoxLayout()


        position.setSpacing(
            5
        )


        position.addWidget(
            QLabel("X/Y ACTUAL")
        )


        position.addWidget(
            self.current_position_label
        )


        position.addWidget(
            self.refresh_position_button
        )


        position.addSpacing(
            10
        )


        position.addWidget(
            QLabel("X/Y INICIAL")
        )


        position.addWidget(
            self.start_position_label
        )


        position.addWidget(
            self.lock_position_button
        )


        position.addWidget(
            self.unlock_position_button
        )


        position.addStretch()



        main_layout.addLayout(
            position
        )



        mode = QHBoxLayout()


        mode.addWidget(
            QLabel("MODE")
        )


        mode.addWidget(
            self.mode_selector
        )


        mode.addStretch()



        main_layout.addLayout(
            mode
        )



        self.setLayout(
            main_layout
        )






    def update_state(self, state):


        player = state.player


        self.character_name_label.setText(
            f"NAME: {player.name}"
            if player.name
            else "NAME: ---"
        )


        self.level_label.setText(
            f"LVL: {player.level}"
        )



        if state.connected:

            self.character_status_indicator.connected()

            self.online_label.setText(
                "ONLINE"
            )

        else:

            self.character_status_indicator.disconnected()

            self.online_label.setText(
                "OFFLINE"
            )



        self.hp_bar.update_percent(
            player.hp_percent
        )


        self.mp_bar.update_percent(
            player.mp_percent
        )


        self.current_position_label.setText(
            f"{player.x} / {player.y}"
        )



        self.start_position_label.setText(
            f"{player.start_x} / {player.start_y}"
        )





    def set_name(self, name):

        self.character_name_label.setText(
            f"NAME: {name}"
        )



    def clear_name(self):

        self.character_name_label.setText(
            "NAME: ---"
        )



    def connected(self):

        self.character_status_indicator.connected()



    def disconnected(self):

        self.character_status_indicator.disconnected()