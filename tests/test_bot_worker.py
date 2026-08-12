import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from core.bot_worker import BotWorker


class FailingEngine:

    @staticmethod
    def start():
        raise RuntimeError("capture failed")


class FailingUpdateEngine:
    def __init__(self):
        self.stop = MagicMock()

    @staticmethod
    def update():
        raise RuntimeError("update failed")


class BotWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_start_uses_a_precise_25_ms_timer(self):
        engine = SimpleNamespace(
            start=MagicMock(),
            update=MagicMock(),
            stop=MagicMock(),
        )
        worker = BotWorker(engine)

        worker.start()

        self.assertEqual(worker.timer.interval(), 25)
        self.assertEqual(worker.timer.timerType(), Qt.TimerType.PreciseTimer)
        worker.stop()
        self.app.processEvents()

    def test_start_failure_reports_error_and_finishes_thread(self):
        worker = BotWorker(FailingEngine())
        errors = []
        finished = []
        worker.error.connect(errors.append)
        worker.finished.connect(lambda: finished.append(True))

        worker.start()

        self.assertEqual(errors, ["capture failed"])
        self.assertEqual(finished, [True])
        self.assertIsNone(worker.timer)

    def test_update_failure_stops_engine_and_finishes_thread(self):
        engine = FailingUpdateEngine()
        worker = BotWorker(engine)
        timer = SimpleNamespace(stop=MagicMock())
        worker.timer = timer
        errors = []
        finished = []
        worker.error.connect(errors.append)
        worker.finished.connect(lambda: finished.append(True))

        worker.update()

        timer.stop.assert_called_once_with()
        engine.stop.assert_called_once_with()
        self.assertEqual(errors, ["update failed"])
        self.assertEqual(finished, [True])
        self.assertIsNone(worker.timer)


if __name__ == "__main__":
    unittest.main()
