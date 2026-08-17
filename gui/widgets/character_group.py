from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
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
        self.current_position_title = QLabel("ACT")
        self.start_position_title = QLabel("INI")
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
        for label in (
            self.current_position_title,
            self.start_position_title,
            self.current_position_label,
            self.start_position_label,
        ):
            label.setStyleSheet("font-size: 10px;")
        self.current_position_label.setFixedWidth(65)
        self.start_position_label.setFixedWidth(65)

        self.mode_selector = QComboBox()
        self.mode_selector.addItem("FIJO", BotMode.STATIC_POINT)
        self.mode_selector.addItem("SIN LÍMITE", BotMode.OFF)
        self.mode_selector.addItem("10", BotMode.STATIC_10)
        self.mode_selector.addItem("20", BotMode.STATIC_20)
        self.mode_selector.addItem("30", BotMode.STATIC_30)
        self.mode_selector.addItem("40", BotMode.STATIC_40)
        self.mode_selector.setCurrentIndex(
            self.mode_selector.findData(BotMode.STATIC_40)
        )
        self.mode_selector.setToolTip(
            "Distancia máxima permitida respecto a la posición inicial."
        )
        self.mode_selector.setFixedWidth(90)
        self.mode_selector.setStyleSheet("font-size: 10px;")

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
            button.setFixedSize(22, 20)
            button.setStyleSheet(style)

    def create_layout(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        resources = QHBoxLayout()
        resources.setSpacing(4)
        resources.addWidget(self.title_label)
        self.hp_bar.setFixedWidth(120)
        self.mp_bar.setFixedWidth(120)
        resources.addWidget(self.hp_bar)
        resources.addWidget(self.mp_bar)
        resources.addStretch()
        main_layout.addLayout(resources)

        position = QHBoxLayout()
        position.setSpacing(2)
        position.addWidget(self.current_position_title)
        position.addWidget(self.current_position_label)
        position.addWidget(self.refresh_position_button)
        position.addWidget(self.start_position_title)
        position.addWidget(self.start_position_label)
        position.addWidget(self.lock_position_button)
        position.addWidget(self.unlock_position_button)
        self.radio_label = QLabel("RADIO")
        self.radio_label.setStyleSheet("font-size: 10px;")
        position.addWidget(self.radio_label)
        position.addWidget(self.mode_selector)
        position.addStretch()
        main_layout.addLayout(position)

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

    def lock_settings(self):
        self.mode_selector.setEnabled(False)

    def unlock_settings(self):
        self.mode_selector.setEnabled(True)
