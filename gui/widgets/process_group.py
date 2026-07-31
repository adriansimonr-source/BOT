from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QHBoxLayout,
    QMessageBox
)


from gui.widgets.status_indicator import StatusIndicator

from gui.dialogs.add_game_dialog import AddGameDialog

from core.managers.game_profile_manager import GameProfileManager





class ProcessGroup(QGroupBox):


    def __init__(self):

        super().__init__("PROCESO")


        # =====================================
        # MANAGER JUEGOS
        # =====================================


        self.game_manager = GameProfileManager()



        self.setup_ui()


        self.load_games()







    # =====================================
    # CREAR UI
    # =====================================


    def setup_ui(self):


        layout = QVBoxLayout()






        # =====================================
        # JUEGO ACTIVO
        # =====================================


        layout.addWidget(

            QLabel("JUEGO")

        )



        self.game_selector = QComboBox()


        layout.addWidget(

            self.game_selector

        )





        # Botones juegos


        game_buttons = QHBoxLayout()



        self.add_game_button = QPushButton(

            "+ Añadir juego"

        )


        self.refresh_games_button = QPushButton(

            "Actualizar"

        )



        game_buttons.addWidget(

            self.add_game_button

        )


        game_buttons.addWidget(

            self.refresh_games_button

        )



        layout.addLayout(

            game_buttons

        )



        self.add_game_button.clicked.connect(

            self.add_game

        )


        self.refresh_games_button.clicked.connect(

            self.load_games

        )











        # =====================================
        # ESTADO
        # =====================================


        layout.addWidget(

            QLabel("ESTADO")

        )


        self.process_status = StatusIndicator()


        layout.addWidget(

            self.process_status

        )








        # =====================================
        # PROCESO
        # =====================================


        layout.addWidget(

            QLabel("PROCESO")

        )


        self.process_name = QLabel(

            "Ningún proceso"

        )


        layout.addWidget(

            self.process_name

        )









        # =====================================
        # PID
        # =====================================


        layout.addWidget(

            QLabel("PID")

        )


        self.process_pid = QLabel(

            "-"

        )


        layout.addWidget(

            self.process_pid

        )










        # =====================================
        # DETECTAR
        # =====================================


        self.detect_process_button = QPushButton(

            "Detectar proceso"

        )


        layout.addWidget(

            self.detect_process_button

        )





        self.setLayout(

            layout

        )











    # =====================================
    # CARGAR JUEGOS
    # =====================================


    def load_games(self):


        current = self.game_selector.currentData()



        self.game_selector.clear()



        games = self.game_manager.get_games()



        for game in games:


            self.game_selector.addItem(

                game["name"],

                game["id"]

            )




        # Recuperar selección


        if current:


            index = self.game_selector.findData(

                current

            )


            if index >= 0:


                self.game_selector.setCurrentIndex(

                    index

                )











    # =====================================
    # JUEGO SELECCIONADO
    # =====================================


    def get_selected_game(self):


        return self.game_selector.currentData()







    def get_selected_game_name(self):


        return self.game_selector.currentText()










    # =====================================
    # AÑADIR JUEGO
    # =====================================


    def add_game(self):


        dialog = AddGameDialog()



        if dialog.exec():


            data = dialog.get_game_data()





            if self.game_manager.get_game(

                data["id"]

            ):


                QMessageBox.warning(

                    self,

                    "Error",

                    "Ya existe un juego con ese ID"

                )


                return






            self.game_manager.add_game(

                data["id"],

                data["name"],

                data["process"],

                data["window"],

                data["width"],

                data["height"]

            )



            self.load_games()










    # =====================================
    # INFORMACIÓN PROCESO
    # =====================================


    def set_process(

        self,

        process_name: str,

        pid: int

    ):


        self.process_name.setText(

            process_name

        )


        self.process_pid.setText(

            str(pid)

        )








    def clear_process(self):


        self.process_name.setText(

            "Ningún proceso"

        )


        self.process_pid.setText(

            "-"

        )









    # =====================================
    # ESTADOS
    # =====================================


    def connected(self):

        self.process_status.connected()





    def disconnected(self):

        self.process_status.disconnected()





    def detecting(self):

        self.process_status.detecting()





    def running(self):

        self.process_status.running()





    def paused(self):

        self.process_status.paused()