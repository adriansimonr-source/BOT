import time

from core.modules.base_module import BaseModule


class AutoAttack(BaseModule):

    def __init__(self, input_manager, target_rules=None, auto_target=None):
        super().__init__("Auto Attack", interval_ms=50)
        self.input = input_manager
        self.auto_target = auto_target
        self.key = "R"
        self.attack_interval = 250
        self.last_attack = None
        self._active_target = None

    def configure(self, right_panel, center_panel):
        card = right_panel.auto_attack
        self.key = card.key()
        self.attack_interval = card.interval()

        if card.is_enabled():
            self.enable()
        else:
            self.disable()

    def on_start(self):
        super().on_start()
        self.last_attack = None
        self._active_target = None

    def update(self, state):
        target = state.target
        if not self._is_attack_ready(target):
            self._active_target = None
            return False

        selection_id = getattr(target, "selection_id", 0)
        target_name = str(target.name or "").strip().casefold()
        target_identity = (
            ("selection", selection_id)
            if selection_id
            else ("name", target_name or "<unknown>")
        )
        if target_identity != self._active_target:
            self._active_target = target_identity
            self.last_attack = None

        now = time.perf_counter() * 1000
        if (
            self.last_attack is not None
            and now - self.last_attack < self.attack_interval
        ):
            return False

        if self.input.press(self.key):
            self.last_attack = now
            return True
        return False

    def _is_attack_ready(self, target):
        if not target.exists:
            return False
        if self.auto_target is None:
            return True
        return self.auto_target.is_attack_ready(target)
