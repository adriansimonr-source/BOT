from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
)



class ProcessTab(QWidget):

    def __init__(self):

        super().__init__()

        self.create_widgets()
        self.create_layout()



    def create_widgets(self):

        self.game_group = QGroupBox(
            "JUEGO"
        )


        self.game_label = QLabel(
            "-"
        )


        self.process_group = QGroupBox(
            "PROCESO"
        )


        self.status_label = QLabel(
            "Desconectado"
        )


        self.process_name = QLabel(
            "-"
        )


        self.pid_label = QLabel(
            "-"
        )


        self.window_label = QLabel(
            "-"
        )


        self.detect_button = QPushButton(
            "Detectar proceso"
        )



    def create_layout(self):

        main_layout = QVBoxLayout()


        game_layout = QVBoxLayout()

        game_layout.addWidget(
            QLabel(
                "Juego seleccionado:"
            )
        )


        game_layout.addWidget(
            self.game_label
        )


        self.game_group.setLayout(
            game_layout
        )



        process_layout = QVBoxLayout()


        process_layout.addWidget(
            QLabel("Estado:")
        )


        process_layout.addWidget(
            self.status_label
        )


        process_layout.addWidget(
            QLabel("Proceso:")
        )


        process_layout.addWidget(
            self.process_name
        )


        process_layout.addWidget(
            QLabel("PID:")
        )


        process_layout.addWidget(
            self.pid_label
        )


        process_layout.addWidget(
            QLabel("Ventana:")
        )


        process_layout.addWidget(
            self.window_label
        )


        process_layout.addWidget(
            self.detect_button
        )


        self.process_group.setLayout(
            process_layout
        )


        main_layout.addWidget(
            self.game_group
        )


        main_layout.addWidget(
            self.process_group
        )


        main_layout.addStretch()


        self.setLayout(
            main_layout
        )



    def set_game(self, name):

        self.game_label.setText(
            name
        )



    def connected(
        self,
        process,
        pid,
        window
    ):

        self.status_label.setText(
            "🟢 Conectado"
        )


        self.process_name.setText(
            process
        )


        self.pid_label.setText(
            str(pid)
        )


        self.window_label.setText(
            window
        )



    def disconnected(self):

        self.status_label.setText(
            "🔴 Desconectado"
        )


        self.process_name.setText(
            "-"
        )


        self.pid_label.setText(
            "-"
        )


        self.window_label.setText(
            "-"
        )