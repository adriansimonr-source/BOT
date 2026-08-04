from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.process_manager import ProcessManager


class AddGameDialog(QDialog):
    def __init__(self, process_manager=None, parent=None):
        super().__init__(parent)
        self.process_manager = process_manager or ProcessManager()
        self.setWindowTitle("Agregar juego")
        self.setMinimumWidth(440)
        self.create_ui()
        self.connect_signals()

    def create_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre visible del juego")
        form.addRow("Nombre:", self.name_input)

        window_row = QHBoxLayout()
        self.window_input = QLineEdit()
        self.window_input.setPlaceholderText("Título o parte estable del título")
        self.detect_button = QPushButton("Detectar proceso")
        window_row.addWidget(self.window_input, 1)
        window_row.addWidget(self.detect_button)
        form.addRow("Ventana:", window_row)

        self.detected_combo = QComboBox()
        self.detected_combo.setEnabled(False)
        form.addRow("Proceso:", self.detected_combo)
        layout.addLayout(form)

        self.status_label = QLabel(
            "Escribe el título de la ventana y pulsa Detectar proceso."
        )
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #6B7280;")
        layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancel_button = QPushButton("Cancelar")
        self.add_button = QPushButton("Agregar")
        self.add_button.setEnabled(False)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.add_button)
        layout.addLayout(buttons)

    def connect_signals(self):
        self.detect_button.clicked.connect(self.detect_process)
        self.window_input.textChanged.connect(self.invalidate_detection)
        self.detected_combo.currentIndexChanged.connect(self.update_add_state)
        self.cancel_button.clicked.connect(self.reject)
        self.add_button.clicked.connect(self.validate)

    def invalidate_detection(self, _text=None):
        self.detected_combo.clear()
        self.detected_combo.setEnabled(False)
        self.add_button.setEnabled(False)
        self.status_label.setText("Pulsa Detectar proceso para validar la ventana.")
        self.status_label.setStyleSheet("color: #6B7280;")

    def detect_process(self):
        window_title = self.window_input.text().strip()
        if not window_title:
            QMessageBox.warning(self, "Ventana requerida", "Introduce el título de la ventana.")
            return

        matches = self.process_manager.discover_windows(window_title)
        self.detected_combo.clear()
        for match in matches:
            label = (
                f'{match["process"]} · PID {match["pid"]} · '
                f'{match["title"]}'
            )
            self.detected_combo.addItem(label, match)

        found = bool(matches)
        self.detected_combo.setEnabled(found)
        self.add_button.setEnabled(found)
        if found:
            self.status_label.setText(
                "Proceso detectado. Si hay varios resultados, selecciona el correcto."
            )
            self.status_label.setStyleSheet("color: #16803C;")
        else:
            self.status_label.setText("No se encontró una ventana compatible con ese título.")
            self.status_label.setStyleSheet("color: #B42318;")

    def update_add_state(self, _index):
        self.add_button.setEnabled(self.detected_combo.currentData() is not None)

    def validate(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Nombre requerido", "Introduce el nombre del juego.")
            return
        if not self.window_input.text().strip():
            QMessageBox.warning(self, "Ventana requerida", "Introduce el título de la ventana.")
            return
        if self.detected_combo.currentData() is None:
            QMessageBox.warning(self, "Proceso requerido", "Detecta primero el proceso del juego.")
            return
        self.accept()

    def get_game_data(self):
        detected = self.detected_combo.currentData()
        name = self.name_input.text().strip()
        return {
            "id": self.process_manager.game_profiles.create_game_id(name),
            "name": name,
            "process": detected["process"],
            "window": self.window_input.text().strip(),
            "width": detected["width"],
            "height": detected["height"],
        }
