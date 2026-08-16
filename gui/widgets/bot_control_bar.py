from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
)

class BotControlBar(QWidget):

    def __init__(self):

        super().__init__()

        self.create_widgets()

        self.create_layout()

    def create_widgets(self):

        self.start_button = QPushButton(

            "▶ INICIAR BOT"

        )

        self.start_button.setMinimumHeight(

            36

        )

        self.start_button.setMinimumWidth(

            180

        )

        self.start_button.setToolTip(

            "Inicia la automatización con la configuración actual."

        )

    def create_layout(self):

        layout = QHBoxLayout()

        layout.setContentsMargins(

            5,

            5,

            5,

            5

        )

        layout.addStretch()

        layout.addWidget(

            self.start_button

        )

        layout.addStretch()

        self.setLayout(

            layout

        )

    def set_running(self):

        self.start_button.setText(

            "⏹ DETENER BOT"

        )

        self.start_button.setToolTip(

            "Detiene la automatización de forma segura."

        )

    def set_starting(self):

        self.start_button.setText(

            "INICIANDO... / DETENER"

        )

        self.start_button.setToolTip(

            "El bot se está iniciando; pulsa para cancelar y detenerlo."

        )

    def set_stopping(self):

        self.start_button.setText(

            "DETENIENDO..."

        )

        self.start_button.setEnabled(False)

        self.start_button.setToolTip(

            "Espera mientras el bot termina las acciones pendientes."

        )

    def set_stopped(self):

        self.start_button.setText(

            "▶ INICIAR BOT"

        )

        self.start_button.setToolTip(

            "Inicia la automatización con la configuración actual."

        )
