from PySide6.QtCore import (
    QObject,
    Signal,
    QTimer
)





class BotWorker(QObject):


    finished = Signal()



    def __init__(

        self,

        bot_engine

    ):


        super().__init__()



        self.bot_engine = bot_engine


        self.timer = None







    # =====================================
    # INICIO THREAD
    # =====================================


    def start(self):


        print(

            "[BOT WORKER] iniciado"

        )



        # Ahora estamos dentro del hilo correcto

        self.bot_engine.start()



        self.timer = QTimer()



        self.timer.setInterval(

            250

        )



        self.timer.timeout.connect(

            self.update

        )



        self.timer.start()







    # =====================================
    # UPDATE
    # =====================================


    def update(self):


        self.bot_engine.update()







    # =====================================
    # STOP
    # =====================================


    def stop(self):


        print(

            "[BOT WORKER] detenido"

        )



        if self.timer:


            self.timer.stop()



        self.bot_engine.stop()



        self.finished.emit()