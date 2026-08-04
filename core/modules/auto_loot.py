import time

from core.modules.base_module import BaseModule


class AutoLoot(BaseModule):

    NO_TARGET_DELAY_SECONDS = 5.0

    def __init__(self, input_manager):
        super().__init__("Auto Loot", interval_ms=50)
        self.input = input_manager
        self.key = "F"
        self.loot_interval = 500
        self.last_loot = None
        self._no_target_since = None

    def configure(self, right_panel, center_panel):
        card = right_panel.auto_loot
        self.key = card.key()
        self.loot_interval = card.interval()

        if card.is_enabled():
            self.enable()
        else:
            self.disable()

    def on_start(self):
        super().on_start()
        self.last_loot = None
        self._no_target_since = time.perf_counter()

    def update(self, state):
        now = time.perf_counter()

        if state.target.exists:
            self._no_target_since = None
            self.last_loot = None
            return False

        if self._no_target_since is None:
            self._no_target_since = now
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
            return True
        return False
