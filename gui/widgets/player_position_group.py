from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
)



class PlayerPositionGroup(QWidget):


    def __init__(self):

        super().__init__()


        self.create_widgets()

        self.create_layout()





    # =====================================
    # WIDGETS
    # =====================================


    def create_widgets(self):


        self.group = QGroupBox(
            "POSICIÓN JUGADOR"
        )


        self.current_position = QLabel(
            "Actual:\nX: ---\nY: ---"
        )


        self.start_position = QLabel(
            "Inicial:\nNo fijada"
        )



        self.status = QLabel(
            "Estado:\nEsperando"
        )



        self.refresh_button = QPushButton(
            "Actualizar posición"
        )



        self.lock_button = QPushButton(
            "Fijar posición"
        )



        self.unlock_button = QPushButton(
            "Liberar posición"
        )





    # =====================================
    # LAYOUT
    # =====================================


    def create_layout(self):


        layout = QVBoxLayout()



        inner = QVBoxLayout()



        inner.addWidget(
            self.current_position
        )


        inner.addWidget(
            self.start_position
        )


        inner.addWidget(
            self.status
        )


        inner.addWidget(
            self.refresh_button
        )


        inner.addWidget(
            self.lock_button
        )


        inner.addWidget(
            self.unlock_button
        )



        self.group.setLayout(
            inner
        )



        layout.addWidget(
            self.group
        )


        self.setLayout(
            layout
        )









    # =====================================
    # UPDATE STATE
    # =====================================


    def update_state(

        self,

        state

    ):


        player = state.player



        # Posición OCR actual

        self.current_position.setText(

            f"Actual:\n"
            f"X: {player.x}\n"
            f"Y: {player.y}"

        )





        # Posición inicial

        if player.position_locked:


            self.start_position.setText(

                f"Inicial:\n"
                f"X: {player.start_x}\n"
                f"Y: {player.start_y}"

            )


            self.status.setText(

                "Estado:\n"
                "✓ Posición fijada"

            )


        else:


            self.start_position.setText(

                "Inicial:\n"
                "No fijada"

            )


            self.status.setText(

                "Estado:\n"
                "Esperando confirmación"

            )