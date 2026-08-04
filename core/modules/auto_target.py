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
        self._pending_identity = None
        self._locked_unique_identity = None
        self._accepted_identity = None

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
        self._pending_identity = None
        self._locked_unique_identity = None
        self._accepted_identity = None

    def update(self, state):
        target = state.target
        if self._is_locked_unique_target(target):
            self._unknown_target_since = None
            self._pending_identity = None
            self.last_target = None
            self._accepted_identity = self._locked_unique_identity
            self._publish_decision(target, TargetDecision.ALLOW)
            return False

        if self._locked_unique_identity is not None:
            self._locked_unique_identity = None

        decision = self.target_rules.evaluate(target)
        if decision is TargetDecision.PENDING:
            self._accepted_identity = None
            now = time.perf_counter()
            pending_identity = self._target_identity(target)
            if (
                self._unknown_target_since is None
                or pending_identity != self._pending_identity
            ):
                self._unknown_target_since = now
                self._pending_identity = pending_identity
                self._publish_decision(target, TargetDecision.PENDING)
                return False
            if (
                now - self._unknown_target_since
                < self.UNKNOWN_NAME_TIMEOUT_SECONDS
            ):
                self._publish_decision(target, TargetDecision.PENDING)
                return False
            decision = TargetDecision.REJECT
        else:
            self._unknown_target_since = None
            self._pending_identity = None

        if decision is TargetDecision.ALLOW:
            identity = self._target_identity(target)
            self._accepted_identity = identity
            if self.target_rules.unique_targets_enabled:
                self._locked_unique_identity = identity
            self.last_target = None
            self._publish_decision(target, TargetDecision.ALLOW)
            return False

        self._accepted_identity = None
        self._publish_decision(target, TargetDecision.REJECT)
        if decision is TargetDecision.REJECT:
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

    def _is_locked_unique_target(self, target):
        if (
            not self.target_rules.unique_targets_enabled
            or self._locked_unique_identity is None
            or not target.exists
        ):
            return False
        return self._target_identity(target) == self._locked_unique_identity

    def is_attack_ready(self, target):
        if not target.exists:
            return False
        if not self.is_enabled() or not self._has_selection_filters():
            return True
        identity = self._target_identity(target)
        return bool(
            identity is not None
            and identity == self._accepted_identity
        )

    def _has_selection_filters(self):
        return bool(
            self.target_rules.blacklist
            or self.target_rules.unique_targets_enabled
            or self.target_rules.min_level > 0
            or self.target_rules.max_level < 999
        )

    @staticmethod
    def _selection_id(target):
        try:
            return int(getattr(target, "selection_id", 0) or 0)
        except (TypeError, ValueError):
            return 0

    @classmethod
    def _target_identity(cls, target):
        selection_id = cls._selection_id(target)
        if selection_id:
            return "selection", selection_id

        signature = getattr(target, "selection_signature", None)
        if signature is not None:
            try:
                hash(signature)
                stable_signature = signature
            except TypeError:
                stable_signature = repr(signature)
            return "signature", stable_signature

        name = str(getattr(target, "name", "") or "").strip().casefold()
        return ("name", name) if name else None

    @classmethod
    def _publish_decision(cls, target, decision):
        target.auto_target_decision = decision
        target.auto_target_decision_selection_id = cls._selection_id(target)
