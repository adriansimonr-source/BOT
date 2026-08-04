import threading
import time

from core.input.window_input_driver import WindowInputDriver


class InputManager:

    DEFAULT_HOLD_MS = 50
    MOVEMENT_KEYS = frozenset(("A", "D", "W"))

    def __init__(self, game_state_manager):
        self.enabled = True
        self.game_state_manager = game_state_manager
        self.window_driver = WindowInputDriver()
        self._condition = threading.Condition(threading.RLock())
        self._held_keys = {}
        self._shutdown = False
        self._scheduler = threading.Thread(
            target=self._release_loop,
            name="bot-key-release",
            daemon=True,
        )
        self._scheduler.start()

    def press(self, key, hold_ms=DEFAULT_HOLD_MS):
        try:
            hold_ms = max(1, int(hold_ms))
        except (TypeError, ValueError, OverflowError):
            return False

        hwnd = self.game_state_manager.process_manager.get_window_handle()
        if not hwnd:
            return False

        normalized_key = str(key).upper()
        with self._condition:
            if (
                not self.enabled
                or self._shutdown
                or not self._can_hold(normalized_key)
            ):
                return False
            if not self.window_driver.key_down(hwnd, normalized_key):
                return False

            self._held_keys[normalized_key] = (
                hwnd,
                time.perf_counter() + hold_ms / 1000,
            )
            self._condition.notify_all()
        return True

    def _can_hold(self, key):
        if key in self._held_keys:
            return False
        is_movement = key in self.MOVEMENT_KEYS
        return not any(
            (held_key in self.MOVEMENT_KEYS) == is_movement
            for held_key in self._held_keys
        )

    def _release_loop(self):
        while True:
            with self._condition:
                while not self._held_keys and not self._shutdown:
                    self._condition.wait()
                if self._shutdown:
                    return

                key, (hwnd, release_at) = min(
                    self._held_keys.items(),
                    key=lambda item: item[1][1],
                )
                remaining = release_at - time.perf_counter()
                if remaining > 0:
                    self._condition.wait(timeout=remaining)
                    continue

                self.window_driver.key_up(hwnd, key)
                self._held_keys.pop(key, None)
                self._condition.notify_all()

    def update(self):
        pass

    def release(self, key):
        normalized_key = str(key).upper()
        with self._condition:
            held = self._held_keys.get(normalized_key)
            if held is None:
                return False
            hwnd, _ = held
            self.window_driver.key_up(hwnd, normalized_key)
            self._held_keys.pop(normalized_key, None)
            self._condition.notify_all()
        return True

    def release_all(self):
        with self._condition:
            self._release_all_locked()

    def _release_all_locked(self):
        for key, (hwnd, _) in tuple(self._held_keys.items()):
            self.window_driver.key_up(hwnd, key)
        self._held_keys.clear()
        self._condition.notify_all()

    def enable(self):
        with self._condition:
            if not self._shutdown:
                self.enabled = True

    def disable(self):
        with self._condition:
            self.enabled = False
            self._release_all_locked()

    def close(self):
        self.disable()
        with self._condition:
            self._shutdown = True
            self._condition.notify_all()
        if threading.current_thread() is not self._scheduler:
            self._scheduler.join(timeout=0.2)

    def is_enabled(self):
        with self._condition:
            return self.enabled

    def is_held(self, key):
        normalized_key = str(key).upper()
        with self._condition:
            return normalized_key in self._held_keys
