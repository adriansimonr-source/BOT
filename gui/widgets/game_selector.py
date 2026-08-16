from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget

from core.managers.game_profile_manager import GameProfileManager


class GameSelector(QWidget):
    game_changed = Signal(str)
    add_game_requested = Signal()
    update_game_requested = Signal()
    delete_game_requested = Signal()

    def __init__(self, manager=None):
        super().__init__()
        self.manager = manager or GameProfileManager()
        self._process_details = ""
        self.create_ui()
        self.connect_signals()
        self.load_games()

    def create_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(QLabel("GAME"))

        self.combo = QComboBox()
        self.combo.setMinimumWidth(180)
        self.combo.setToolTip("Selecciona el perfil de juego que utilizará el bot.")
        layout.addWidget(self.combo)

        self.status_label = QLabel("● Sin detectar")
        self.status_label.setMinimumWidth(100)
        self.status_label.setStyleSheet("color: #6B7280;")
        self.status_label.setToolTip("Estado del juego: Sin detectar.")
        layout.addWidget(self.status_label)

        self.add_button = QPushButton("+")
        self.refresh_button = QPushButton("↻")
        self.update_button = self.refresh_button
        self.delete_button = QPushButton("×")

        self.add_button.setToolTip("Agrega un nuevo perfil de juego.")
        self.refresh_button.setToolTip(
            "Busca y conecta el proceso del juego seleccionado."
        )
        self.delete_button.setToolTip("Elimina el perfil de juego seleccionado.")

        for button in (
            self.add_button,
            self.refresh_button,
            self.delete_button,
        ):
            button.setFixedSize(32, 28)
            layout.addWidget(button)

        layout.addStretch()

    def connect_signals(self):
        self.combo.currentIndexChanged.connect(self.on_game_changed)
        self.add_button.clicked.connect(self.add_game_requested.emit)
        self.refresh_button.clicked.connect(self.update_game_requested.emit)
        self.delete_button.clicked.connect(self.delete_game_requested.emit)

    def load_games(self, selected_game_id=None):
        selected_game_id = selected_game_id or self.get_selected_game()
        blocker = QSignalBlocker(self.combo)
        self.combo.clear()
        for game in self.manager.get_games():
            self.combo.addItem(game["name"], game["id"])

        if selected_game_id:
            index = self.combo.findData(selected_game_id)
            if index >= 0:
                self.combo.setCurrentIndex(index)
        del blocker

        has_games = self.combo.count() > 0
        self.combo.setEnabled(has_games)
        self.refresh_button.setEnabled(has_games)
        self.delete_button.setEnabled(has_games)
        if not has_games:
            self.set_process_status(False, "Sin juegos")

    def on_game_changed(self, _index):
        game_id = self.get_selected_game()
        if game_id:
            self.set_process_status(False, "Sin detectar")
            self.game_changed.emit(game_id)

    def get_selected_game(self):
        return self.combo.currentData()

    def get_selected_name(self):
        return self.combo.currentText()

    def refresh(self, selected_game_id=None):
        self.load_games(selected_game_id)

    def select_game(self, game_id, emit=False):
        index = self.combo.findData(game_id)
        if index < 0:
            return False

        if emit:
            self.combo.setCurrentIndex(index)
        else:
            blocker = QSignalBlocker(self.combo)
            self.combo.setCurrentIndex(index)
            del blocker
        return True

    def set_process_status(self, connected, text=None, details=None):
        if connected:
            label = text or "Conectado"
            color = "#16803C"
        else:
            label = text or "No encontrado"
            neutral_labels = {"Sin detectar", "Buscando...", "Sin juegos"}
            color = "#6B7280" if label in neutral_labels else "#B42318"

        self.status_label.setText(f"● {label}")
        self.status_label.setStyleSheet(f"color: {color};")
        if not connected:
            self._process_details = ""
        elif label == "Conectado" and details:
            self._process_details = details

        tooltip = details
        if not tooltip and connected and label == "Conectado":
            tooltip = self._process_details
        self.status_label.setToolTip(
            tooltip or f"Estado del juego: {label}."
        )

    def set_locked(self, locked):
        has_games = self.combo.count() > 0
        self.combo.setEnabled(has_games and not locked)
        self.add_button.setEnabled(not locked)
        self.refresh_button.setEnabled(has_games and not locked)
        self.delete_button.setEnabled(has_games and not locked)
