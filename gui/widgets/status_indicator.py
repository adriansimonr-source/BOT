from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
)

from enum import Enum





class Status(Enum):

    DISCONNECTED = "Disconnected"
    CONNECTED = "Connected"
    DETECTING = "Detecting"
    RUNNING = "Running"
    PAUSED = "Paused"







class StatusIndicator(QWidget):


    STATUS = {

        Status.DISCONNECTED: "#d32f2f",

        Status.CONNECTED: "#2e7d32",

        Status.DETECTING: "#f9a825",

        Status.RUNNING: "#1976d2",

        Status.PAUSED: "#ef6c00",

    }






    def __init__(self):

        super().__init__()



        self.circle = QLabel()


        self.circle.setFixedSize(

            12,

            12

        )



        layout = QHBoxLayout()


        layout.setContentsMargins(

            0,

            0,

            0,

            0

        )



        layout.addWidget(

            self.circle

        )



        self.setLayout(

            layout

        )



        self.set_status(

            Status.DISCONNECTED

        )







    def set_status(

        self,

        status

    ):


        if status not in self.STATUS:

            return



        color = self.STATUS[status]



        self.circle.setStyleSheet(

            f"""

            background-color: {color};

            border-radius: 6px;

            """

        )








    def connected(self):

        self.set_status(

            Status.CONNECTED

        )





    def disconnected(self):

        self.set_status(

            Status.DISCONNECTED

        )





    def detecting(self):

        self.set_status(

            Status.DETECTING

        )





    def running(self):

        self.set_status(

            Status.RUNNING

        )





    def paused(self):

        self.set_status(

            Status.PAUSED

        )