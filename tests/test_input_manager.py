import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import call, patch

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

    def test_resource_keys_have_independent_action_lanes(self):
        self.assertTrue(self.manager.press("R", hold_ms=5000))
        self.assertTrue(self.manager.press("F8", hold_ms=5000))
        self.assertTrue(self.manager.press("F9", hold_ms=5000))
        self.assertTrue(self.manager.press("F10", hold_ms=5000))

        self.assertFalse(self.manager.press("1"))
        self.assertFalse(self.manager.press("F8"))
        self.assertEqual(
            [event[2] for event in self.driver.events if event[0] == "down"],
            ["R", "F8", "F9", "F10"],
        )

        self.manager.release_all()

    def test_successful_press_timestamp_is_exposed_by_key(self):
        self.assertIsNone(self.manager.last_press_at("f8"))

        self.assertTrue(self.manager.press("f8", hold_ms=20))

        self.assertIsInstance(self.manager.last_press_at("F8"), float)

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

    def test_long_movement_hold_does_not_delay_function_skills(self):
        self.assertTrue(self.manager.press("W", hold_ms=5000))
        self.assertTrue(self.manager.press("F1", hold_ms=20))
        self.assertTrue(self.driver.key_up_event.wait(0.3))
        self.driver.key_up_event.clear()

        self.assertTrue(self.manager.press("F9", hold_ms=20))
        self.assertTrue(self.driver.key_up_event.wait(0.3))
        self.assertTrue(self.manager.is_held("W"))
        self.assertTrue(self.manager.release("W"))

        self.assertEqual(
            [event[2] for event in self.driver.events if event[0] == "down"],
            ["W", "F1", "F9"],
        )

    def test_long_movement_hold_is_tracked_and_can_be_cancelled(self):
        self.assertTrue(self.manager.press("W", hold_ms=5000))
        self.assertTrue(self.manager.is_held("w"))
        self.assertEqual(self.driver.events, [("down", 1234, "W")])

        self.assertTrue(self.manager.release("W"))

        self.assertFalse(self.manager.is_held("W"))
        self.assertEqual(
            self.driver.events,
            [("down", 1234, "W"), ("up", 1234, "W")],
        )

    def test_invalid_hold_never_sends_key_down(self):
        for hold_ms in (None, "invalid", float("inf")):
            with self.subTest(hold_ms=hold_ms):
                self.assertFalse(self.manager.press("W", hold_ms=hold_ms))

        self.assertEqual(self.driver.events, [])

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

    def test_window_driver_delivers_keys_directly_with_a_short_timeout(self):
        driver = WindowInputDriver()
        with (
            patch(
                "core.input.window_input_driver.win32gui.IsWindow",
                return_value=True,
            ),
            patch(
                "core.input.window_input_driver.win32api.MapVirtualKey",
                return_value=0x13,
            ),
            patch(
                "core.input.window_input_driver.win32gui.SendMessageTimeout",
                return_value=(1, 0),
            ) as send,
            patch(
                "core.input.window_input_driver.win32gui.PostMessage"
            ) as post,
        ):
            self.assertTrue(driver.key_down(1234, "R"))
            self.assertTrue(driver.key_up(1234, "R"))

        self.assertEqual(
            send.call_args_list,
            [
                call(
                    1234,
                    0x0100,
                    KEY_MAP["R"],
                    1 | (0x13 << 16),
                    driver.MESSAGE_FLAGS,
                    driver.MESSAGE_TIMEOUT_MS,
                ),
                call(
                    1234,
                    0x0101,
                    KEY_MAP["R"],
                    1 | (0x13 << 16) | (1 << 30) | (1 << 31),
                    driver.MESSAGE_FLAGS,
                    driver.MESSAGE_TIMEOUT_MS,
                ),
            ],
        )
        post.assert_not_called()

    def test_window_driver_does_not_fallback_to_queued_text_on_timeout(self):
        driver = WindowInputDriver()
        with (
            patch(
                "core.input.window_input_driver.win32gui.IsWindow",
                return_value=True,
            ),
            patch(
                "core.input.window_input_driver.win32api.MapVirtualKey",
                return_value=0x13,
            ),
            patch(
                "core.input.window_input_driver.win32gui.SendMessageTimeout",
                return_value=(0, 0),
            ),
            patch(
                "core.input.window_input_driver.win32gui.PostMessage"
            ) as post,
        ):
            self.assertFalse(driver.key_down(1234, "R"))

        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
