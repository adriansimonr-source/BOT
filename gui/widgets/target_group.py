from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
)


from gui.widgets.resource_bar import ResourceBar





class TargetGroup(QWidget):


    def __init__(self):

        super().__init__()


        self.create_widgets()

        self.create_layout()







    # =====================================
    # WIDGETS
    # =====================================


    def create_widgets(self):


        # Nombre


        self.target_name_label = QLabel(

            "TARGET: ---"

        )



        # Nivel


        self.level_label = QLabel(

            "LVL: -"

        )



        # Vida


        self.hp_bar = ResourceBar(

            "HP"

        )









    # =====================================
    # LAYOUT
    # =====================================


    def create_layout(self):


        main_layout = QVBoxLayout()



        main_layout.setContentsMargins(

            6,

            6,

            6,

            6

        )


        main_layout.setSpacing(

            8

        )






        # -----------------------------
        # NAME + LEVEL
        # -----------------------------


        header_layout = QHBoxLayout()



        header_layout.addWidget(

            self.target_name_label

        )


        header_layout.addStretch()



        header_layout.addWidget(

            self.level_label

        )



        main_layout.addLayout(

            header_layout

        )








        # -----------------------------
        # HP
        # -----------------------------


        main_layout.addWidget(

            self.hp_bar

        )



        main_layout.addStretch()





        self.setLayout(

            main_layout

        )









    # =====================================
    # UPDATE STATE
    # =====================================


    def update_state(

        self,

        state

    ):


        target = state.target





        # Sin objetivo


        if not target.exists:


            self.target_name_label.setText(

                "TARGET: ---"

            )


            self.level_label.setText(

                "LVL: -"

            )


            self.hp_bar.update_percent(

                0

            )


            return







        # Nombre


        self.target_name_label.setText(

            f"TARGET: {target.name}"

            if target.name

            else

            "TARGET: ---"

        )







        # Nivel


        self.level_label.setText(

            f"LVL: {target.level}"

        )







        # Vida


        self.hp_bar.update_percent(

            target.hp_percent

        )