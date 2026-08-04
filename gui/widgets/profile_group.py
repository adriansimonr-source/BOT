from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QVBoxLayout,
)

from gui.widgets.mode_selector import ModeSelector

from core.models.bot_settings import BotMode


class ProfileGroup(QGroupBox):

    def __init__(self):

        super().__init__("PERFIL")

        self.setup_ui()


    # =====================================
    # UI
    # =====================================

    def setup_ui(self):

        layout = QVBoxLayout()


        # =========================
        # Personaje actual
        # =========================

        layout.addWidget(
            QLabel("PERSONAJE")
        )

        self.character_label = QLabel(
            "No seleccionado"
        )

        layout.addWidget(
            self.character_label
        )


        # =========================
        # Modo bot
        # =========================

        self.bot_mode_selector = ModeSelector(
            "MODO BOT"
        )


        self.bot_mode_selector.set_modes(
            [
                BotMode.STATIC_50,
                BotMode.STATIC_100,
                BotMode.STATIC_150,
                BotMode.OFF,
                BotMode.STATIC_POINT,
            ]
        )


        layout.addWidget(
            self.bot_mode_selector
        )


        self.setLayout(
            layout
        )


    # =====================================
    # API pública
    # =====================================

    def set_character(
        self,
        name: str
    ):

        self.character_label.setText(
            name
        )


    def get_bot_mode(self):

        return (
            self.bot_mode_selector
            .current_value()
        )


    # =====================================
    # Bloqueo durante ejecución
    # =====================================

    def lock(self):

        self.bot_mode_selector.previous_button.setEnabled(
            False
        )

        self.bot_mode_selector.next_button.setEnabled(
            False
        )


    def unlock(self):

        self.bot_mode_selector.previous_button.setEnabled(
            True
        )

        self.bot_mode_selector.next_button.setEnabled(
            True
        )

