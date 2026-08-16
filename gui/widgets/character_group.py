from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.models.bot_settings import BotMode
from core.models.player_state import PlayerState
from gui.widgets.resource_bar import ResourceBar


class CharacterGroup(QWidget):
    def __init__(self):
        super().__init__()
        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.title_label = QLabel("PERSONAJE")
        self.title_label.setStyleSheet("font-weight: bold;")
        self.hp_bar = ResourceBar("HP")
        self.mp_bar = ResourceBar("MP")
        self.current_position_label = QLabel("--- / ---")
        self.start_position_label = QLabel("--- / ---")
        self.refresh_position_button = QPushButton("⟳")
        self.lock_position_button = QPushButton("📌")
        self.unlock_position_button = QPushButton("🔓")
        self.refresh_position_button.setToolTip(
            "Vuelve a leer las coordenadas actuales del personaje."
        )
        self.lock_position_button.setToolTip(
            "Fija las coordenadas actuales como posición inicial del bot."
        )
        self.unlock_position_button.setToolTip(
            "Libera la posición inicial para poder fijar una nueva."
        )
        self.current_position_label.setToolTip(
            "Últimas coordenadas válidas detectadas en el minimapa."
        )
        self.start_position_label.setToolTip(
            "Coordenadas de origen usadas para controlar el radio del bot."
        )

        self.mode_selector = QComboBox()
        self.mode_selector.addItem("FIJO (0)", BotMode.STATIC_POINT)
        self.mode_selector.addItem("25", BotMode.STATIC_25)
        self.mode_selector.addItem("50", BotMode.STATIC_50)
        self.mode_selector.addItem("75", BotMode.STATIC_75)
        self.mode_selector.addItem("100", BotMode.STATIC_100)
        self.mode_selector.addItem("SIN LÍMITE", BotMode.OFF)
        self.mode_selector.setCurrentIndex(
            self.mode_selector.findData(BotMode.STATIC_100)
        )
        self.mode_selector.setToolTip(
            "Distancia máxima permitida respecto a la posición inicial."
        )

        self.quiet_seconds = QSpinBox()
        self.quiet_seconds.setRange(3, 120)
        self.quiet_seconds.setValue(10)
        self.quiet_seconds.setSuffix(" s")
        self.quiet_seconds.setToolTip(
            "Tiempo sin desplazamiento antes de intentar regresar al origen."
        )
        self.apply_button_style()

    def apply_button_style(self):
        style = """
        QPushButton {
            background-color: #173B6D;
            color: white;
            border-radius: 6px;
            border: none;
            font-size: 13px;
        }
        QPushButton:hover { background-color: #28558F; }
        QPushButton:pressed { background-color: #102A4D; }
        """
        for button in (
            self.refresh_position_button,
            self.lock_position_button,
            self.unlock_position_button,
        ):
            button.setFixedSize(30, 24)
            button.setStyleSheet(style)

    def create_layout(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.hp_bar)
        main_layout.addWidget(self.mp_bar)

        position = QHBoxLayout()
        position.setSpacing(5)
        position.addWidget(QLabel("X/Y ACTUAL"))
        position.addWidget(self.current_position_label)
        position.addWidget(self.refresh_position_button)
        position.addSpacing(10)
        position.addWidget(QLabel("X/Y INICIAL"))
        position.addWidget(self.start_position_label)
        position.addWidget(self.lock_position_button)
        position.addWidget(self.unlock_position_button)
        position.addStretch()
        main_layout.addLayout(position)

        mode = QHBoxLayout()
        mode.addWidget(QLabel("RADIO BOT"))
        mode.addWidget(self.mode_selector)
        mode.addSpacing(10)
        mode.addWidget(QLabel("QUIETO"))
        mode.addWidget(self.quiet_seconds)
        mode.addStretch()
        main_layout.addLayout(mode)

    def update_state(self, state):
        player = state.player
        self.hp_bar.update_percent(self._resource_value(player, "hp"))
        self.mp_bar.update_percent(self._resource_value(player, "mp"))
        self.current_position_label.setText(
            f"{player.x} / {player.y}"
            if getattr(player, "position_valid", False)
            else "--- / ---"
        )
        self.start_position_label.setText(
            f"{player.start_x} / {player.start_y}"
            if player.position_locked
            else "--- / ---"
        )

    @staticmethod
    def _resource_value(player, resource):
        if not hasattr(player, f"{resource}_valid"):
            return getattr(player, f"{resource}_percent", None)
        if not PlayerState.resource_is_fresh(player, resource):
            return None
        return getattr(player, f"{resource}_percent", None)

    def get_bot_mode(self):
        return self.mode_selector.currentData()

    def get_quiet_seconds(self):
        return self.quiet_seconds.value()

    def lock_settings(self):
        self.mode_selector.setEnabled(False)
        self.quiet_seconds.setEnabled(False)

    def unlock_settings(self):
        self.mode_selector.setEnabled(True)
        self.quiet_seconds.setEnabled(True)
