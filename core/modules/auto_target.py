import time

from core.modules.base_module import BaseModule
from core.models.target_rules import TargetDecision


class AutoTarget(BaseModule):

    UNKNOWN_NAME_TIMEOUT_SECONDS = 2.0

    def __init__(self, input_manager, target_rules):
        super().__init__("Auto Target", interval_ms=50)
        self.input = input_manager
        self.target_rules = target_rules
        self.key = "E"
        self.target_interval = 250
        self.last_target = None
        self._unknown_target_since = None

    def configure(self, right_panel, center_panel):
        card = right_panel.auto_target
        self.key = card.key()
        self.target_interval = card.interval()

        if card.is_enabled():
            self.enable()
        else:
            self.disable()

    def on_start(self):
        super().on_start()
        self.last_target = None
        self._unknown_target_since = None

    def update(self, state):
        target = state.target
        decision = self.target_rules.evaluate(target)
        if decision is TargetDecision.PENDING:
            now = time.perf_counter()
            if self._unknown_target_since is None:
                self._unknown_target_since = now
                return False
            if (
                now - self._unknown_target_since
                < self.UNKNOWN_NAME_TIMEOUT_SECONDS
            ):
                return False
        else:
            self._unknown_target_since = None

        if decision is not TargetDecision.ALLOW:
            now_ms = time.perf_counter() * 1000
            if (
                self.last_target is not None
                and now_ms - self.last_target < self.target_interval
            ):
                return False
            if self.input.press(self.key):
                self.last_target = now_ms
                return True
        return False
