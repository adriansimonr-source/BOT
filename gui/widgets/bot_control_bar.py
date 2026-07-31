from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel
)



class BotControlBar(QWidget):


    def __init__(self):

        super().__init__()


        self.create_widgets()

        self.create_layout()





    # =====================================
    # Crear widgets
    # =====================================


    def create_widgets(self):


        self.status_label = QLabel(
            "BOT DETENIDO"
        )


        self.start_button = QPushButton(
            "▶ INICIAR BOT"
        )


        self.start_button.setMinimumHeight(
            40
        )





    # =====================================
    # Layout
    # =====================================


    def create_layout(self):


        layout = QHBoxLayout()


        layout.addWidget(
            self.status_label
        )


        layout.addStretch()


        layout.addWidget(
            self.start_button
        )


        self.setLayout(
            layout
        )





    # =====================================
    # Estados
    # =====================================


    def set_running(self):


        self.status_label.setText(
            "BOT EJECUTANDO"
        )


        self.start_button.setText(
            "⏹ DETENER BOT"
        )





    def set_stopped(self):


        self.status_label.setText(
            "BOT DETENIDO"
        )


        self.start_button.setText(
            "▶ INICIAR BOT"
        )