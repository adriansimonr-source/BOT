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

    def test_stop_finishes_only_after_engine_confirms_shutdown(self):
        engine = SimpleNamespace(
            stop=MagicMock(side_effect=(RuntimeError("stop failed"), True)),
        )
        worker = BotWorker(engine)
        errors = []
        finished = []
        worker.error.connect(errors.append)
        worker.finished.connect(lambda: finished.append(True))

        worker.stop()

        self.assertEqual(errors, ["stop failed"])
        self.assertEqual(finished, [])

        worker.stop()

        self.assertEqual(errors, ["stop failed"])
        self.assertEqual(finished, [True])

    def test_pending_shutdown_keeps_worker_alive_until_retry_succeeds(self):
        engine = SimpleNamespace(stop=MagicMock(side_effect=(False, True)))
        worker = BotWorker(engine)
        finished = []
        worker.finished.connect(lambda: finished.append(True))

        worker.stop()

        self.assertEqual(finished, [])
        self.assertTrue(worker.stop_retry_timer.isActive())

        worker.stop()

        self.assertEqual(finished, [True])
        self.assertFalse(worker.stop_retry_timer.isActive())

    def test_live_configuration_error_has_its_own_signal(self):
        engine = SimpleNamespace(
            apply_config=MagicMock(side_effect=ValueError("bad config")),
        )
        worker = BotWorker(engine)
        runtime_errors = []
        config_errors = []
        worker.error.connect(runtime_errors.append)
        worker.config_error.connect(config_errors.append)

        self.assertFalse(worker.apply_config(SimpleNamespace(revision=1)))

        self.assertEqual(runtime_errors, [])
        self.assertEqual(config_errors, ["bad config"])


if __name__ == "__main__":
    unittest.main()
