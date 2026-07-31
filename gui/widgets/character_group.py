from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QGridLayout,
)

from gui.widgets.status_indicator import StatusIndicator
from gui.widgets.resource_bar import ResourceBar





class CharacterGroup(QGroupBox):


    def __init__(self):

        super().__init__("PERSONAJE")

        self.setup_ui()





    def setup_ui(self):


        layout = QGridLayout()

        layout.setHorizontalSpacing(15)

        layout.setVerticalSpacing(6)





        # ============================
        # Nombre
        # ============================


        layout.addWidget(

            QLabel("NOMBRE"),

            0,

            0

        )


        self.character_name_label = QLabel(

            "No detectado"

        )


        layout.addWidget(

            self.character_name_label,

            0,

            1

        )






        # ============================
        # Nivel
        # ============================


        layout.addWidget(

            QLabel("NIVEL"),

            1,

            0

        )


        self.level_label = QLabel(

            "0"

        )


        layout.addWidget(

            self.level_label,

            1,

            1

        )







        # ============================
        # Estado
        # ============================


        layout.addWidget(

            QLabel("ESTADO"),

            2,

            0

        )


        self.character_status_indicator = StatusIndicator()


        self.character_status_indicator.disconnected()



        layout.addWidget(

            self.character_status_indicator,

            2,

            1

        )







        # ============================
        # Vida
        # ============================


        self.hp_bar = ResourceBar(

            "VIDA"

        )


        layout.addWidget(

            self.hp_bar,

            3,

            0,

            1,

            2

        )







        # ============================
        # Mana
        # ============================


        self.mp_bar = ResourceBar(

            "MANA"

        )


        layout.addWidget(

            self.mp_bar,

            4,

            0,

            1,

            2

        )







        # ============================
        # Posición
        # ============================


        layout.addWidget(

            QLabel("POSICIÓN"),

            5,

            0

        )


        self.position_label = QLabel(

            "X: 0  Y: 0"

        )


        layout.addWidget(

            self.position_label,

            5,

            1

        )



        self.setLayout(

            layout

        )







    # ==================================================
    # Actualización desde GameState
    # ==================================================


    def update_state(

        self,

        state

    ):


        player = state.player






        # Nombre

        self.character_name_label.setText(

            player.name

            if player.name

            else "No detectado"

        )







        # Nivel

        self.level_label.setText(

            str(player.level)

        )







        # Estado

        if state.connected:

            self.character_status_indicator.connected()

        else:

            self.character_status_indicator.disconnected()







        # Recursos en porcentaje


        self.hp_bar.update_percent(

            player.hp_percent

        )


        self.mp_bar.update_percent(

            player.mp_percent

        )







        # Posición

        self.position_label.setText(

            f"X: {player.x}  Y: {player.y}"

        )







    # ==================================================
    # Compatibilidad anterior
    # ==================================================


    def set_name(

        self,

        name: str

    ):


        self.character_name_label.setText(

            name

        )





    def clear_name(self):


        self.character_name_label.setText(

            "No detectado"

        )





    def connected(self):


        self.character_status_indicator.connected()





    def disconnected(self):


        self.character_status_indicator.disconnected()





    def detecting(self):


        self.character_status_indicator.detecting()





    def running(self):


        self.character_status_indicator.running()





    def paused(self):


        self.character_status_indicator.paused()