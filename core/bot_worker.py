from PySide6.QtCore import QObject, QTimer, Qt, Signal, Slot


class BotWorker(QObject):
    finished = Signal()
    error = Signal(str)
    UPDATE_INTERVAL_MS = 25

    def __init__(self, bot_engine):
        super().__init__()
        self.bot_engine = bot_engine
        self.timer = None

    @Slot()
    def start(self):
        try:
            self.bot_engine.start()
        except Exception as error:
            self.error.emit(str(error))
            self.finished.emit()
            return

        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(self.UPDATE_INTERVAL_MS)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    @Slot()
    def update(self):
        try:
            self.bot_engine.update()
        except Exception as error:
            if self.timer:
                self.timer.stop()
                self.timer = None
            try:
                self.bot_engine.stop()
            except Exception:
                pass
            self.error.emit(str(error))
            self.finished.emit()

    @Slot()
    def stop(self):
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.bot_engine.stop()
        self.finished.emit()
