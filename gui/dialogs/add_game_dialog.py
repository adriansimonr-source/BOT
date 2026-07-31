from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QMessageBox
)





class AddGameDialog(QDialog):


    def __init__(self):

        super().__init__()


        self.setWindowTitle(

            "Añadir juego"

        )


        self.setMinimumWidth(

            350

        )


        self.create_widgets()


        self.create_layout()





    # =====================================
    # Crear widgets
    # =====================================


    def create_widgets(self):


        # ID interno


        self.id_input = QLineEdit()


        self.id_input.setPlaceholderText(

            "ejemplo: kathana"

        )





        # Nombre visible


        self.name_input = QLineEdit()


        self.name_input.setPlaceholderText(

            "Nombre del juego"

        )





        # Proceso


        self.process_input = QLineEdit()


        self.process_input.setPlaceholderText(

            "Juego.exe"

        )





        # Ventana


        self.window_input = QLineEdit()


        self.window_input.setPlaceholderText(

            "Título de la ventana"

        )





        # Resolución


        self.width_input = QSpinBox()


        self.width_input.setRange(

            640,

            7680

        )


        self.width_input.setValue(

            1920

        )





        self.height_input = QSpinBox()


        self.height_input.setRange(

            480,

            4320

        )


        self.height_input.setValue(

            1080

        )





        # Botones


        self.save_button = QPushButton(

            "Guardar"

        )


        self.cancel_button = QPushButton(

            "Cancelar"

        )



        self.save_button.clicked.connect(

            self.validate

        )


        self.cancel_button.clicked.connect(

            self.reject

        )









    # =====================================
    # Layout
    # =====================================


    def create_layout(self):


        layout = QVBoxLayout()





        layout.addWidget(

            QLabel("ID interno")

        )


        layout.addWidget(

            self.id_input

        )





        layout.addWidget(

            QLabel("Nombre")

        )


        layout.addWidget(

            self.name_input

        )





        layout.addWidget(

            QLabel("Proceso")

        )


        layout.addWidget(

            self.process_input

        )





        layout.addWidget(

            QLabel("Ventana")

        )


        layout.addWidget(

            self.window_input

        )







        resolution_layout = QHBoxLayout()



        resolution_layout.addWidget(

            QLabel("Ancho")

        )


        resolution_layout.addWidget(

            self.width_input

        )



        resolution_layout.addWidget(

            QLabel("Alto")

        )


        resolution_layout.addWidget(

            self.height_input

        )



        layout.addLayout(

            resolution_layout

        )







        buttons = QHBoxLayout()


        buttons.addWidget(

            self.save_button

        )


        buttons.addWidget(

            self.cancel_button

        )


        layout.addLayout(

            buttons

        )





        self.setLayout(

            layout

        )









    # =====================================
    # Validación
    # =====================================


    def validate(self):


        if not self.id_input.text():


            QMessageBox.warning(

                self,

                "Error",

                "El ID es obligatorio"

            )


            return





        if not self.name_input.text():


            QMessageBox.warning(

                self,

                "Error",

                "El nombre es obligatorio"

            )


            return





        if not self.process_input.text():


            QMessageBox.warning(

                self,

                "Error",

                "El proceso es obligatorio"

            )


            return





        self.accept()







    # =====================================
    # Obtener datos
    # =====================================


    def get_game_data(self):


        return {


            "id": self.id_input.text().strip(),


            "name": self.name_input.text().strip(),


            "process": self.process_input.text().strip(),


            "window": self.window_input.text().strip(),


            "width": self.width_input.value(),


            "height": self.height_input.value()

        }