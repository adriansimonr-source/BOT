from PySide6.QtCore import QObject, QTimer, Qt, Signal, Slot


class BotWorker(QObject):
    finished = Signal()
    started = Signal()
    error = Signal(str)
    config_error = Signal(str)
    config_applied = Signal(int)
    UPDATE_INTERVAL_MS = 25

    def __init__(self, bot_engine, initial_config=None):
        super().__init__()
        self.bot_engine = bot_engine
        self.initial_config = initial_config
        self._config_revision = -1
        self._finished_emitted = False
        self._last_stop_error = None
        self.timer = None
        self.stop_retry_timer = QTimer(self)
        self.stop_retry_timer.setSingleShot(True)
        self.stop_retry_timer.setInterval(50)
        self.stop_retry_timer.timeout.connect(self.stop)

    @Slot()
    def start(self):
        try:
            if self.initial_config is not None:
                try:
                    self._apply_config(self.initial_config)
                except Exception as error:
                    self.error.emit(str(error))
                    self._finish()
                    return
                self.initial_config = None
            if self.bot_engine.start() is False:
                self.stop()
                return
        except Exception as error:
            self.error.emit(str(error))
            if callable(getattr(self.bot_engine, "stop", None)):
                self.stop()
            else:
                self._finish()
            return

        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(self.UPDATE_INTERVAL_MS)
        self.timer.timeout.connect(self.update)
        self.timer.start()
        self.started.emit()

    @Slot(object)
    def apply_config(self, config):
        revision = int(getattr(config, "revision", 0))
        if revision <= self._config_revision:
            return False
        try:
            self._apply_config(config)
        except Exception as error:
            self.config_error.emit(str(error))
            return False
        return True

    def _apply_config(self, config):
        revision = int(getattr(config, "revision", 0))
        self.bot_engine.apply_config(config)
        self._config_revision = revision
        self.config_applied.emit(revision)

    @Slot()
    def refresh_player_position(self):
        self.bot_engine.refresh_player_position()

    @Slot()
    def lock_player_position(self):
        self.bot_engine.lock_player_position()

    @Slot()
    def unlock_player_position(self):
        self.bot_engine.unlock_player_position()

    @Slot()
    def update(self):
        try:
            self.bot_engine.update()
        except Exception as error:
            if self.timer:
                self.timer.stop()
                self.timer = None
            self.error.emit(str(error))
            self.stop()

    @Slot()
    def stop(self):
        if self._finished_emitted:
            return
        if self.timer:
            self.timer.stop()
            self.timer = None
        try:
            stopped = self.bot_engine.stop()
        except Exception as error:
            message = str(error)
            if message != self._last_stop_error:
                self.error.emit(message)
                self._last_stop_error = message
            stopped = False
        if stopped is False:
            self.stop_retry_timer.start()
            return
        self._finish()

    def _finish(self):
        if self._finished_emitted:
            return
        self.stop_retry_timer.stop()
        self._finished_emitted = True
        self.finished.emit()
