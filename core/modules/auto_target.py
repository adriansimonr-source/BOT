import math
import time

from core.modules.base_module import BaseModule


class AutoTarget(BaseModule):

    SELECTION_SETTLE_SECONDS = 1.0
    MIN_TARGET_CHANGE_SECONDS = 4.0
    HP_PROGRESS_EPSILON = 1.0

    def __init__(self, input_manager, target_rules):
        super().__init__("Auto Target", interval_ms=50)
        self.input = input_manager
        self.target_rules = target_rules
        self.key = "E"
        self.target_interval = 10000
        self.last_target = None
        self._tracked_identity = None
        self._selection_started_at = None
        self._stalled_target_started_at = None
        self._lowest_hp_observed = None
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
            self._reset_stall_tracking()

    def on_start(self):
        super().on_start()
        self.last_target = None
        self._tracked_identity = None
        self._selection_started_at = None
        self._reset_stall_tracking()
        self._clear_selection_request()

    def update(self, state):
        now = time.perf_counter()
        target = state.target
        identity = self._target_identity(target)

        if self._selection_request_pending:
            if identity != self._requested_identity:
                self._clear_selection_request()
                self._start_tracking(identity, now)
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
                    now,
                    selected_at=requested_at,
                )

        if identity != self._tracked_identity:
            self._start_tracking(identity, now)

        if not target.exists:
            return self._request_target(identity, now)

        if (
            self.target_rules.has_filters()
            and not self.target_rules.is_allowed(target)
        ):
            return self._request_target(identity, now)

        if self._stalled_target_timeout_expired(target, now):
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
        minimum_interval = self.MIN_TARGET_CHANGE_SECONDS * 1000
        if (
            self.last_target is not None
            and now_ms - self.last_target < minimum_interval
        ):
            return False

        if not self.input.press(self.key):
            return False

        self.last_target = now_ms
        if identity is not None:
            self._stalled_target_started_at = now
        self._selection_request_pending = True
        self._requested_identity = identity
        self._selection_requested_at = now
        return True

    def _start_tracking(self, identity, now, selected_at=None):
        previous_identity = self._tracked_identity
        self._tracked_identity = identity
        if identity != previous_identity:
            self._reset_stall_tracking(
                started_at=now if identity is not None else None,
            )
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

    def _stalled_target_timeout_expired(self, target, now):
        hp_percent = None
        if bool(getattr(target, "hp_valid", False)):
            try:
                hp_percent = float(getattr(target, "hp_percent", None))
            except (TypeError, ValueError, OverflowError):
                hp_percent = None

        if hp_percent is not None and math.isfinite(hp_percent):
            if self._lowest_hp_observed is None:
                self._lowest_hp_observed = hp_percent
            elif (
                hp_percent
                <= self._lowest_hp_observed - self.HP_PROGRESS_EPSILON
            ):
                self._stalled_target_started_at = None
                self._lowest_hp_observed = hp_percent

        if self._stalled_target_started_at is None:
            self._stalled_target_started_at = now
            return False

        return (
            now - self._stalled_target_started_at
            >= max(1, self.target_interval) / 1000
        )

    def _reset_stall_tracking(self, started_at=None):
        self._stalled_target_started_at = started_at
        self._lowest_hp_observed = None

    def _clear_selection_request(self):
        self._selection_request_pending = False
        self._requested_identity = None
        self._selection_requested_at = None

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
