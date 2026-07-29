from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout

from gui.widgets.status_indicator import StatusIndicator


class CharacterGroup(QGroupBox):

    def __init__(self):

        super().__init__("PERSONAJE")

        self.setup_ui()


    def setup_ui(self):

        layout = QVBoxLayout()


        # ============================
        # Nombre
        # ============================

        layout.addWidget(
            QLabel("NOMBRE")
        )

        self.character_name_label = QLabel(
            "No detectado"
        )

        layout.addWidget(
            self.character_name_label
        )


        # ============================
        # Estado
        # ============================

        layout.addWidget(
            QLabel("ESTADO")
        )

        self.character_status_indicator = StatusIndicator()

        self.character_status_indicator.disconnected()

        layout.addWidget(
            self.character_status_indicator
        )


        # ============================
        # Vida
        # ============================

        layout.addWidget(
            QLabel("VIDA")
        )

        self.hp_label = QLabel(
            "0 / 0"
        )

        layout.addWidget(
            self.hp_label
        )


        # ============================
        # Mana
        # ============================

        layout.addWidget(
            QLabel("MANA")
        )

        self.mp_label = QLabel(
            "0 / 0"
        )

        layout.addWidget(
            self.mp_label
        )


        # ============================
        # Posición
        # ============================

        layout.addWidget(
            QLabel("POSICIÓN")
        )

        self.position_label = QLabel(
            "X: 0  Y: 0"
        )

        layout.addWidget(
            self.position_label
        )


        self.setLayout(
            layout
        )


    # ==================================================
    # Actualización desde GameState
    # ==================================================

    def update_state(self, state):

        self.character_name_label.setText(
            state.character_name
            if state.character_name
            else "No detectado"
        )


        if state.connected:

            self.character_status_indicator.connected()

        else:

            self.character_status_indicator.disconnected()


        self.hp_label.setText(
            f"{state.hp} / {state.max_hp}"
        )


        self.mp_label.setText(
            f"{state.mp} / {state.max_mp}"
        )


        self.position_label.setText(
            f"X: {state.x}  Y: {state.y}"
        )


    # ==================================================
    # Compatibilidad anterior
    # ==================================================

    def set_name(self, name: str):

        self.character_name_label.setText(
            name
        )


    def clear_name(self):

        self.character_name_label.setText(
            "No detectado"
        )


    def connected(self):

        self.character_status_indicator.connected()


    def disconnected(self):

        self.character_status_indicator.disconnected()


    def detecting(self):

        self.character_status_indicator.detecting()


    def running(self):

        self.character_status_indicator.running()


    def paused(self):

        self.character_status_indicator.paused()