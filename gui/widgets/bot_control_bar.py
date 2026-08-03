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







    # =====================================
    # Crear widgets
    # =====================================


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








    # =====================================
    # Layout
    # =====================================


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









    # =====================================
    # Estados
    # =====================================


    def set_running(self):


        self.start_button.setText(

            "⏹ DETENER BOT"

        )





    def set_stopped(self):


        self.start_button.setText(

            "▶ INICIAR BOT"

        )