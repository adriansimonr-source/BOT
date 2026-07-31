from PySide6.QtWidgets import (
    QWidget,
    QProgressBar,
    QLabel,
    QHBoxLayout
)





class ResourceBar(QWidget):


    def __init__(self, name):

        super().__init__()


        self.name = name


        self.setup_ui()





    def setup_ui(self):


        layout = QHBoxLayout()


        self.label = QLabel(

            self.name

        )


        self.bar = QProgressBar()


        self.bar.setMinimum(

            0

        )


        self.bar.setMaximum(

            100

        )



        self.value_label = QLabel(

            "0%"

        )



        layout.addWidget(

            self.label

        )


        layout.addWidget(

            self.bar

        )


        layout.addWidget(

            self.value_label

        )


        layout.setContentsMargins(

            0,

            0,

            0,

            0

        )


        self.setLayout(

            layout

        )







    # =====================================
    # ACTUALIZAR PORCENTAJE
    # =====================================


    def update_percent(

        self,

        value

    ):


        if value < 0:

            value = 0


        if value > 100:

            value = 100



        self.bar.setValue(

            int(value)

        )


        self.value_label.setText(

            f"{int(value)}%"

        )





    # Compatibilidad
    # =====================================


    def update_value(

        self,

        current,

        maximum

    ):


        if maximum <= 0:

            self.update_percent(

                0

            )

            return



        percent = (

            current /

            maximum

        ) * 100



        self.update_percent(

            percent

        )