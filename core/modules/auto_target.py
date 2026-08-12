import time

from core.modules.base_module import BaseModule


class AutoTarget(BaseModule):

    BLOCKED_TIMEOUT_SECONDS = 10.0
    DAMAGE_PROGRESS_RATIO = 0.90
    SELECTION_SETTLE_SECONDS = 1.0
    HP_READING_MAX_AGE_SECONDS = 0.5
    MIN_TARGET_CHANGE_SECONDS = 4.0

    def __init__(self, input_manager, target_rules):
        super().__init__("Auto Target", interval_ms=50)
        self.input = input_manager
        self.target_rules = target_rules
        self.key = "E"
        self.target_interval = 250
        self.last_target = None
        self._tracked_identity = None
        self._selection_started_at = None
        self._progress_hp = None
        self._progress_started_at = None
        self._selection_request_pending = False
        self._requested_identity = None
        self._selection_requested_at = None

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
        self._tracked_identity = None
        self._selection_started_at = None
        self._progress_hp = None
        self._progress_started_at = None
        self._clear_selection_request()

    def update(self, state):
        now = time.perf_counter()
        target = state.target
        identity = self._target_identity(target)

        if self._selection_request_pending:
            if identity != self._requested_identity:
                self._clear_selection_request()
                self._start_tracking(identity, target, now)
            elif (
                now - self._selection_requested_at
                < self.SELECTION_SETTLE_SECONDS
            ):
                return False
            else:
                requested_at = self._selection_requested_at
                self._clear_selection_request()
                self._start_tracking(
                    identity,
                    target,
                    now,
                    selected_at=requested_at,
                )

        if identity != self._tracked_identity:
            self._start_tracking(identity, target, now)

        if not target.exists:
            return self._request_target(identity, now)

        if (
            self.target_rules.has_filters()
            and not self.target_rules.is_allowed(target)
        ):
            return self._request_target(identity, now)

        if not self._has_valid_hp(target, now):
            self._clear_progress_window()
            return False

        hp_percent = self._hp_percent(target)
        if hp_percent <= 0:
            return self._request_target(identity, now)

        if self._progress_hp is None:
            self._start_progress_window(hp_percent, now)
            return False

        if hp_percent < self._progress_hp * self.DAMAGE_PROGRESS_RATIO:
            self._start_progress_window(hp_percent, now)
            return False

        if now - self._progress_started_at >= self.BLOCKED_TIMEOUT_SECONDS:
            return self._request_target(identity, now)

        return False

    def _request_target(self, identity, now):
        if (
            self._selection_started_at is not None
            and now - self._selection_started_at
            < self.MIN_TARGET_CHANGE_SECONDS
        ):
            return False

        now_ms = now * 1000
        minimum_interval = max(
            self.target_interval,
            self.MIN_TARGET_CHANGE_SECONDS * 1000,
        )
        if (
            self.last_target is not None
            and now_ms - self.last_target < minimum_interval
        ):
            return False

        if not self.input.press(self.key):
            return False

        self.last_target = now_ms
        self._selection_request_pending = True
        self._requested_identity = identity
        self._selection_requested_at = now
        return True

    def _start_tracking(self, identity, target, now, selected_at=None):
        previous_identity = self._tracked_identity
        self._tracked_identity = identity
        if identity is not None:
            if selected_at is not None:
                self._selection_started_at = selected_at
            elif (
                previous_identity is None
                and self._selection_started_at is None
                and self.last_target is None
            ):
                self._selection_started_at = (
                    now - self.MIN_TARGET_CHANGE_SECONDS
                )
            else:
                self._selection_started_at = now
        elif previous_identity is None:
            self._selection_started_at = None

        hp_percent = self._hp_percent(target)
        if target.exists and self._has_valid_hp(target, now) and hp_percent > 0:
            self._start_progress_window(hp_percent, now)
        else:
            self._clear_progress_window()

    def _start_progress_window(self, hp_percent, now):
        self._progress_hp = hp_percent
        self._progress_started_at = now

    def _clear_progress_window(self):
        self._progress_hp = None
        self._progress_started_at = None

    def _clear_selection_request(self):
        self._selection_request_pending = False
        self._requested_identity = None
        self._selection_requested_at = None

    @staticmethod
    def _hp_percent(target):
        try:
            return float(getattr(target, "hp_percent", 0) or 0)
        except (TypeError, ValueError, OverflowError):
            return 0.0

    @classmethod
    def _has_valid_hp(cls, target, now):
        hp_valid = getattr(target, "hp_valid", None)
        if hp_valid is None:
            return True
        if not hp_valid:
            return False

        observed_at = getattr(target, "hp_observed_at", None)
        if observed_at is None:
            return False
        try:
            age = now - float(observed_at)
        except (TypeError, ValueError, OverflowError):
            return False
        return 0.0 <= age <= cls.HP_READING_MAX_AGE_SECONDS

    @staticmethod
    def _target_identity(target):
        if not getattr(target, "exists", False):
            return None

        try:
            selection_id = int(getattr(target, "selection_id", 0) or 0)
        except (TypeError, ValueError, OverflowError):
            selection_id = 0
        if selection_id:
            return "selection", selection_id

        return ("visible",)
