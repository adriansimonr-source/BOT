import time

from core.modules.base_module import BaseModule


class AutoLoot(BaseModule):

    NO_TARGET_DELAY_SECONDS = 5.0

    def __init__(self, input_manager):
        super().__init__("Auto Loot", interval_ms=25)
        self.input = input_manager
        self.key = "F"
        self.loot_interval = 500
        self.last_loot = None
        self._no_target_since = None
        self._target_seen = False
        self._post_kill_pending = False
        self._loot_window_active = False

    def configure(self, right_panel, center_panel):
        card = right_panel.auto_loot
        self.key = card.key()
        self.loot_interval = card.interval()

        if card.is_enabled():
            self.enable()
        else:
            self.disable()
            self._target_seen = False
            self._reset_pending()

    def on_start(self):
        super().on_start()
        self.last_loot = None
        self._target_seen = False
        self._reset_pending()

    def on_stop(self):
        self._target_seen = False
        self._reset_pending()

    def observe_target(self, state, now=None):
        if now is None:
            now = time.perf_counter()

        if state.target.exists:
            self._target_seen = True
            self.last_loot = None
            self._reset_pending()
            return False

        if self._post_kill_pending:
            return True

        if self._loot_window_active:
            return False

        if not self._target_seen:
            return False

        self._target_seen = False
        self._post_kill_pending = True
        self._loot_window_active = True
        self._no_target_since = now
        return True

    def is_waiting_for_loot(self):
        return self._post_kill_pending

    def update(self, state):
        now = time.perf_counter()
        self.observe_target(state, now)
        if not self._loot_window_active:
            return False

        if now - self._no_target_since < self.NO_TARGET_DELAY_SECONDS:
            return False

        now_ms = now * 1000
        if (
            self.last_loot is not None
            and now_ms - self.last_loot < self.loot_interval
        ):
            return False

        if self.input.press(self.key):
            self.last_loot = now_ms
            self._post_kill_pending = False
            return True
        return False

    def _reset_pending(self):
        self._no_target_since = None
        self._post_kill_pending = False
        self._loot_window_active = False
