from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QGridLayout,
)

from gui.widgets.status_indicator import StatusIndicator
from gui.widgets.resource_bar import ResourceBar





class TargetGroup(QGroupBox):


    def __init__(self):

        super().__init__("OBJETIVO")

        self.setup_ui()






    def setup_ui(self):


        layout = QGridLayout()


        layout.setHorizontalSpacing(15)
        layout.setVerticalSpacing(6)





        # ==========================
        # Nombre
        # ==========================


        layout.addWidget(

            QLabel("NOMBRE"),

            0,

            0

        )


        self.target_name_label = QLabel(

            "Sin objetivo"

        )


        layout.addWidget(

            self.target_name_label,

            0,

            1

        )







        # ==========================
        # Nivel
        # ==========================


        layout.addWidget(

            QLabel("NIVEL"),

            1,

            0

        )


        self.level_label = QLabel(

            "-"

        )


        layout.addWidget(

            self.level_label,

            1,

            1

        )







        # ==========================
        # Estado
        # ==========================


        layout.addWidget(

            QLabel("ESTADO"),

            2,

            0

        )


        self.target_status_indicator = StatusIndicator()


        self.target_status_indicator.disconnected()


        layout.addWidget(

            self.target_status_indicator,

            2,

            1

        )







        # ==========================
        # Vida
        # ==========================


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


        target = state.target





        # ==========================
        # Sin objetivo
        # ==========================


        if not target.exists:


            self.target_name_label.setText(

                "Sin objetivo"

            )


            self.level_label.setText(

                "-"

            )


            self.hp_bar.update_value(

                0,

                100

            )


            self.target_status_indicator.disconnected()


            return







        # ==========================
        # Nombre
        # ==========================


        self.target_name_label.setText(

            target.name

            if target.name

            else

            "Desconocido"

        )







        # ==========================
        # Nivel
        # ==========================


        self.level_label.setText(

            str(target.level)

        )







        # ==========================
        # Estado
        # ==========================


        self.target_status_indicator.connected()






        # ==========================
        # Vida
        # ==========================


        self.hp_bar.update_value(

            target.hp_percent,

            100

        )