from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
)


from core.managers.game_profile_manager import GameProfileManager






class GameSelector(QWidget):


    game_changed = Signal(str)


    add_game_requested = Signal()

    update_game_requested = Signal()

    delete_game_requested = Signal()






    def __init__(self):

        super().__init__()



        self.manager = GameProfileManager()



        self.create_ui()

        self.load_games()

        self.connect_signals()







    # =====================================
    # UI
    # =====================================


    def create_ui(self):


        layout = QHBoxLayout()



        layout.setContentsMargins(

            0,

            0,

            0,

            0

        )


        layout.setSpacing(

            6

        )







        # LABEL


        layout.addWidget(

            QLabel(

                "GAME"

            )

        )








        # SELECTOR


        self.combo = QComboBox()


        self.combo.setMinimumWidth(

            190

        )


        layout.addWidget(

            self.combo

        )









        # ===============================
        # ICON BUTTONS
        # ===============================


        self.add_button = QPushButton(

            "➕"

        )


        self.update_button = QPushButton(

            "🔄"

        )


        self.delete_button = QPushButton(

            "🗑"

        )



        for button in [

            self.add_button,

            self.update_button,

            self.delete_button

        ]:


            button.setFixedSize(

                36,

                28

            )



        layout.addWidget(

            self.add_button

        )


        layout.addWidget(

            self.update_button

        )


        layout.addWidget(

            self.delete_button

        )



        layout.addStretch()





        self.setLayout(

            layout

        )









    # =====================================
    # SIGNALS
    # =====================================


    def connect_signals(self):


        self.combo.currentIndexChanged.connect(

            self.on_game_changed

        )



        self.add_button.clicked.connect(

            self.add_game_requested.emit

        )


        self.update_button.clicked.connect(

            self.update_game_requested.emit

        )


        self.delete_button.clicked.connect(

            self.delete_game_requested.emit

        )









    # =====================================
    # LOAD GAMES
    # =====================================


    def load_games(self):


        self.combo.clear()



        for game in self.manager.get_games():


            self.combo.addItem(

                game["name"],

                game["id"]

            )









    # =====================================
    # CHANGE
    # =====================================


    def on_game_changed(self):


        game_id = self.get_selected_game()



        if game_id:


            self.game_changed.emit(

                game_id

            )









    # =====================================
    # ACCESS
    # =====================================


    def get_selected_game(self):


        return self.combo.currentData()








    def get_selected_name(self):


        return self.combo.currentText()









    # =====================================
    # REFRESH
    # =====================================


    def refresh(self):


        current = self.get_selected_game()



        self.load_games()



        if current:


            index = self.combo.findData(

                current

            )


            if index >= 0:


                self.combo.setCurrentIndex(

                    index

                )