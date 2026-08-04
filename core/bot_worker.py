from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
    QTimer
)





class BotWorker(QObject):


    finished = Signal()

    error = Signal(str)

    UPDATE_INTERVAL_MS = 50



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


    @Slot()
    def start(self):


        print(

            "[BOT WORKER] iniciado"

        )



        # Ahora estamos dentro del hilo correcto

        try:

            self.bot_engine.start()

        except Exception as error:

            self.error.emit(str(error))

            self.finished.emit()

            return



        self.timer = QTimer(self)



        self.timer.setInterval(

            self.UPDATE_INTERVAL_MS

        )



        self.timer.timeout.connect(

            self.update

        )



        self.timer.start()







    # =====================================
    # UPDATE
    # =====================================


    @Slot()
    def update(self):


        self.bot_engine.update()







    # =====================================
    # STOP
    # =====================================


    @Slot()
    def stop(self):


        print(

            "[BOT WORKER] detenido"

        )



        if self.timer:


            self.timer.stop()



        self.bot_engine.stop()



        self.finished.emit()
