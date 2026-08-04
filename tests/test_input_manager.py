import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.input.input_manager import InputManager
from core.input.window_input_driver import KEY_MAP, WindowInputDriver


class FakeWindowDriver:

    def __init__(self):
        self.events = []
        self.key_up_event = threading.Event()

    def key_down(self, hwnd, key):
        self.events.append(("down", hwnd, key))
        return True

    def key_up(self, hwnd, key):
        self.events.append(("up", hwnd, key))
        self.key_up_event.set()
        return True


class InputManagerTests(unittest.TestCase):

    def setUp(self):
        process_manager = SimpleNamespace(get_window_handle=lambda: 1234)
        game_state_manager = SimpleNamespace(process_manager=process_manager)
        self.manager = InputManager(game_state_manager)
        self.driver = FakeWindowDriver()
        self.manager.window_driver = self.driver

    def tearDown(self):
        self.manager.close()

    def test_keydown_is_immediate_and_keyup_uses_independent_scheduler(self):
        started = time.perf_counter()
        self.assertTrue(self.manager.press("r", hold_ms=30))

        self.assertEqual(self.driver.events, [("down", 1234, "R")])
        self.manager.update()
        self.assertTrue(self.driver.key_up_event.wait(0.3))
        self.assertGreaterEqual(time.perf_counter() - started, 0.02)
        self.assertEqual(
            self.driver.events,
            [("down", 1234, "R"), ("up", 1234, "R")],
        )

    def test_same_key_cannot_overlap_but_can_run_after_release(self):
        self.assertTrue(self.manager.press("F8", hold_ms=20))
        self.assertFalse(self.manager.press("F8"))
        self.assertTrue(self.driver.key_up_event.wait(0.3))
        self.assertTrue(self.manager.press("F8"))

    def test_different_non_movement_actions_do_not_overlap(self):
        self.assertTrue(self.manager.press("R", hold_ms=20))
        self.assertFalse(self.manager.press("1"))
        self.assertTrue(self.driver.key_up_event.wait(0.3))
        self.assertTrue(self.manager.press("1"))

    def test_movement_does_not_block_an_action(self):
        self.assertTrue(self.manager.press("W", hold_ms=250))
        self.assertTrue(self.manager.press("1", hold_ms=20))
        self.assertTrue(self.driver.key_up_event.wait(0.3))
        self.assertTrue(self.manager.release("W"))
        self.assertEqual(
            self.driver.events,
            [
                ("down", 1234, "W"),
                ("down", 1234, "1"),
                ("up", 1234, "1"),
                ("up", 1234, "W"),
            ],
        )

    def test_release_only_releases_the_requested_key(self):
        self.assertTrue(self.manager.press("W", hold_ms=250))
        self.assertFalse(self.manager.release("A"))
        self.assertTrue(self.manager.release("W"))
        self.assertEqual(
            self.driver.events,
            [("down", 1234, "W"), ("up", 1234, "W")],
        )

    def test_disable_releases_held_key(self):
        self.assertTrue(self.manager.press("W", hold_ms=250))
        self.manager.disable()
        self.assertEqual(
            self.driver.events,
            [("down", 1234, "W"), ("up", 1234, "W")],
        )
        self.assertFalse(self.manager.press("W"))

    def test_numeric_and_function_key_mappings_are_complete(self):
        self.assertEqual(
            [KEY_MAP[str(number)] for number in range(1, 10)],
            list(range(0x31, 0x3A)),
        )
        self.assertEqual(
            [KEY_MAP[f"F{number}"] for number in range(1, 11)],
            list(range(0x70, 0x7A)),
        )

    def test_key_messages_include_scan_code_and_release_flags(self):
        with patch(
            "core.input.window_input_driver.win32api.MapVirtualKey",
            return_value=0x1E,
        ):
            down = WindowInputDriver._message_lparam(KEY_MAP["1"])
            up = WindowInputDriver._message_lparam(KEY_MAP["1"], released=True)

        self.assertEqual((down >> 16) & 0xFF, 0x1E)
        self.assertFalse(down & (1 << 31))
        self.assertTrue(up & (1 << 30))
        self.assertTrue(up & (1 << 31))


if __name__ == "__main__":
    unittest.main()
