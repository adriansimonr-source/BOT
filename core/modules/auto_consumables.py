import time

from core.modules.base_module import BaseModule


class AutoConsumables(BaseModule):

    def __init__(self, input_manager):
        super().__init__("Auto Consumables", interval_ms=50)
        self.input = input_manager
        self.pot1_enabled = False
        self.pot1_key = "F8"
        self.pot1_threshold = 40
        self.pot1_interval = 2000
        self.last_pot1_use = None
        self.mp_enabled = False
        self.mp_key = "F9"
        self.mp_threshold = 30
        self.mp_interval = 2000
        self.last_mp_use = None

    def configure(self, right_panel, center_panel):
        pot1_card = right_panel.auto_pot1
        self.pot1_enabled = pot1_card.is_enabled()
        self.pot1_key = pot1_card.key()
        self.pot1_threshold = pot1_card.threshold()
        self.pot1_interval = pot1_card.interval()

        mp_card = right_panel.auto_mp
        self.mp_enabled = mp_card.is_enabled()
        self.mp_key = mp_card.key()
        self.mp_threshold = mp_card.threshold()
        self.mp_interval = mp_card.interval()

    def is_enabled(self):
        return self.pot1_enabled or self.mp_enabled

    def on_start(self):
        super().on_start()
        self.last_pot1_use = None
        self.last_mp_use = None

    def update(self, state):
        player = state.player
        now = time.perf_counter() * 1000
        hp_percent = player.hp_percent
        mp_percent = player.mp_percent

        if (
            self.pot1_enabled
            and 0 < hp_percent <= self.pot1_threshold
            and (
                self.last_pot1_use is None
                or now - self.last_pot1_use >= self.pot1_interval
            )
        ):
            if self.input.press(self.pot1_key):
                self.last_pot1_use = now

        if (
            self.mp_enabled
            and 0 < mp_percent <= self.mp_threshold
            and (
                self.last_mp_use is None
                or now - self.last_mp_use >= self.mp_interval
            )
        ):
            if self.input.press(self.mp_key):
                self.last_mp_use = now
