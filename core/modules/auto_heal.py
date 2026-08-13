import time

from core.models.player_state import PlayerState
from core.modules.base_module import BaseModule


class AutoHeal(BaseModule):

    def __init__(self, input_manager):
        super().__init__("Auto Heal", interval_ms=50)
        self.input = input_manager
        self.key = "F10"
        self.threshold = 40
        self.interval = 2000
        self.last_use = None

    def configure(self, right_panel, center_panel):
        card = right_panel.auto_heal
        self.key = card.key()
        self.threshold = card.threshold()
        self.interval = card.interval()

        if card.is_enabled():
            self.enable()
        else:
            self.disable()

    def on_start(self):
        super().on_start()
        self.last_use = None

    def update(self, state):
        player = state.player
        observed_now = time.perf_counter()
        if not PlayerState.resource_is_fresh(player, "hp", now=observed_now):
            return

        hp_percent = player.hp_percent
        now = observed_now * 1000

        if not 0 < hp_percent <= self.threshold:
            return

        if self.last_use is not None and now - self.last_use < self.interval:
            return

        if self.input.press(self.key):
            self.last_use = now
