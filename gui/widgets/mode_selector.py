from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QPushButton,
)


class ModeSelector(QWidget):

    def __init__(self, title="MODO BOT"):

        super().__init__()

        self.modes = []

        self.current_index = 0

        self.setup_ui(title)


    def setup_ui(self, title):

        layout = QHBoxLayout()

        self.title_label = QLabel(
            title
        )

        self.value_label = QLabel(
            "-"
        )


        self.previous_button = QPushButton(
            "◀"
        )

        self.next_button = QPushButton(
            "▶"
        )


        self.previous_button.clicked.connect(
            self.previous
        )

        self.next_button.clicked.connect(
            self.next
        )


        layout.addWidget(
            self.title_label
        )

        layout.addStretch()

        layout.addWidget(
            self.previous_button
        )

        layout.addWidget(
            self.value_label
        )

        layout.addWidget(
            self.next_button
        )


        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )


        self.setLayout(
            layout
        )


    # =====================================
    # Configuración
    # =====================================

    def set_modes(self, modes):

        self.modes = modes

        self.current_index = 0

        self.refresh()


    def refresh(self):

        if not self.modes:
            return

        self.value_label.setText(
            self.modes[self.current_index].name
        )


    # =====================================
    # Navegación
    # =====================================

    def previous(self):

        if not self.modes:
            return

        self.current_index -= 1

        if self.current_index < 0:
            self.current_index = len(self.modes)-1

        self.refresh()


    def next(self):

        if not self.modes:
            return

        self.current_index += 1

        if self.current_index >= len(self.modes):
            self.current_index = 0

        self.refresh()


    # =====================================
    # Obtener valor
    # =====================================

    def current_value(self):

        if not self.modes:
            return None

        return self.modes[
            self.current_index
        ]