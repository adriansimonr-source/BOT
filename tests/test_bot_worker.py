import unittest

from core.bot_worker import BotWorker


class FailingEngine:

    @staticmethod
    def start():
        raise RuntimeError("capture failed")


class BotWorkerTests(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
