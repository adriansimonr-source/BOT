import math
import time
from enum import Enum

from core.modules.base_module import BaseModule


class MovementStatus(Enum):
    IDLE = "idle"
    RETURNING = "returning"
    RECOVERING = "recovering"
    PAUSED = "paused"
    FAILED = "failed"


class MovementManager(BaseModule):

    POSITION_MAX_AGE_SECONDS = 3.0
    POSITION_WAIT_SECONDS = 2.75
    ARRIVAL_TOLERANCE = 2.0
    MOTION_EPSILON = 1.0
    MIN_PROGRESS = 0.5
    OUTSIDE_CONFIRMATIONS = 1
    MAX_RECOVERY_ROUNDS = 3
    MOVEMENT_KEYS = ("W", "A", "D")
    RECOVERY_KEYS = ("A", "D", "W")

    def __init__(self, input_manager, settings):
        super().__init__("MovementManager", interval_ms=100)
        self.input = input_manager
        self.settings = settings
        self.status = MovementStatus.IDLE
        self.reason = ""
        self._game_state = None
        self._last_revision = None
        self._last_position = None
        self._last_motion_at = None
        self._outside_samples = 0
        self._preferred_key = None
        self._probe_keys = []
        self._probe_index = 0
        self._recovery_index = 0
        self._recovery_rounds = 0
        self._command = None
        self._failed_position = None
        self._forced_return = False

    def on_start(self):
        super().on_start()
        self._reset_runtime()

    def on_stop(self):
        self._release_movement()
        self._set_status(MovementStatus.IDLE)
        self._reset_runtime(keep_status=True)

    def update(self, state):
        now = time.perf_counter()
        self._game_state = state
        player = state.player
        distance = self._distance_to_start(player)
        self._publish(distance)

        radius = self.settings.get_movement_range()
        if not self._navigation_available(state, player, radius):
            self._cancel_navigation(now)
            return False

        is_new_sample = self._consume_position_sample(player, now)
        distance = self._distance_to_start(player)
        self._publish(distance)

        if self.status == MovementStatus.FAILED:
            if self._failed_position is None or not is_new_sample:
                return False
            if self._point_distance(self._failed_position, self._last_position) < 2:
                return False
            self._set_status(MovementStatus.IDLE)
            self._outside_samples = 0
            self._last_motion_at = now

        outside_radius = distance > radius
        if is_new_sample:
            self._outside_samples = (
                self._outside_samples + 1
                if outside_radius
                else 0
            )

        outside_confirmed = (
            outside_radius
            and self._outside_samples >= self.OUTSIDE_CONFIRMATIONS
        )
        if outside_confirmed and not self._forced_return:
            self._forced_return = True
            if self.is_navigating() or self._command is not None:
                self.reason = "fuera_de_radio"
                self._publish(distance)
            else:
                return self._start_return(
                    state,
                    player,
                    distance,
                    now,
                    "fuera_de_radio",
                    force=True,
                )

        if self._target_blocks_navigation(state) and not self._forced_return:
            self._pause_for_combat(now)
            return False

        if self.status == MovementStatus.PAUSED:
            self._set_status(MovementStatus.IDLE)
            self._last_motion_at = now
            self._outside_samples = 0

        if self._command is not None:
            if is_new_sample and player.position_revision != self._command["revision"]:
                return self._evaluate_command(state, player, distance, now)
            if now - self._command["sent_at"] >= self.POSITION_WAIT_SECONDS:
                self._release_movement()
                self._command = None
                self._forced_return = False
                self._outside_samples = 0
                self._last_motion_at = now
                self._set_status(MovementStatus.IDLE, "sin_coordenada_nueva")
            return False

        if distance <= self.ARRIVAL_TOLERANCE:
            if self.is_navigating():
                self._finish_return(now)
            else:
                self._outside_samples = 0
            return False

        if self.status in (MovementStatus.RETURNING, MovementStatus.RECOVERING):
            return self._send_next_step(state, player, distance, now)

        quiet_seconds = max(3.0, float(self.settings.return_delay))
        if (
            self._last_motion_at is not None
            and now - self._last_motion_at >= quiet_seconds
        ):
            return self._start_return(state, player, distance, now, "quieto")

        return False

    def is_navigating(self):
        return self.status in (
            MovementStatus.RETURNING,
            MovementStatus.RECOVERING,
        )

    def _navigation_available(self, state, player, radius):
        if hasattr(state, "connected") and not state.connected:
            return False
        if not self.settings.auto_return or radius is None:
            return False
        if not player.position_locked:
            return False
        return self._has_fresh_position(player)

    def _has_fresh_position(self, player):
        checker = getattr(player, "has_fresh_position", None)
        if callable(checker):
            return checker(self.POSITION_MAX_AGE_SECONDS)
        if not getattr(player, "position_valid", False):
            return False
        updated_at = getattr(player, "position_updated_at", 0.0)
        return time.perf_counter() - updated_at <= self.POSITION_MAX_AGE_SECONDS

    @staticmethod
    def _target_blocks_navigation(state):
        target = getattr(state, "target", None)
        return bool(
            getattr(state, "in_combat", False)
            or getattr(target, "exists", False)
        )

    def _consume_position_sample(self, player, now):
        revision = getattr(player, "position_revision", 0)
        if revision == self._last_revision:
            return False

        position = (int(player.x), int(player.y))
        if (
            self._last_position is None
            or self._point_distance(self._last_position, position) >= self.MOTION_EPSILON
        ):
            self._last_motion_at = now

        self._last_position = position
        self._last_revision = revision
        if self._last_motion_at is None:
            self._last_motion_at = now
        return True

    def _start_return(self, state, player, distance, now, reason, force=False):
        self._forced_return = force
        self._preferred_key = None
        self._prepare_probes()
        self._recovery_index = 0
        self._recovery_rounds = 0
        self._set_status(MovementStatus.RETURNING, reason)
        return self._send_next_step(state, player, distance, now)

    def _prepare_probes(self):
        if self._preferred_key in self.MOVEMENT_KEYS:
            self._probe_keys = [
                self._preferred_key,
                *(key for key in self.MOVEMENT_KEYS if key != self._preferred_key),
            ]
        else:
            self._probe_keys = list(self.MOVEMENT_KEYS)
        self._probe_index = 0

    def _send_next_step(self, state, player, distance, now):
        if self.status == MovementStatus.RECOVERING:
            key = self.RECOVERY_KEYS[self._recovery_index]
            hold_ms = max(300, int(self.settings.movement_hold_ms))
            phase = "recovery"
        else:
            if self._probe_index >= len(self._probe_keys):
                self._set_status(MovementStatus.RECOVERING, "bloqueado")
                self._recovery_index = 0
                return self._send_next_step(state, player, distance, now)
            key = self._probe_keys[self._probe_index]
            hold_ms = int(self.settings.movement_hold_ms)
            phase = "probe"

        if not self.input.press(key, hold_ms=hold_ms):
            self.reason = "esperando_entrada"
            self._publish(distance)
            return False

        self._command = {
            "key": key,
            "phase": phase,
            "distance": distance,
            "revision": player.position_revision,
            "sent_at": now,
        }
        self._publish(distance, key)
        return True

    def _evaluate_command(self, state, player, distance, now):
        command = self._command
        self._command = None

        if distance <= self.ARRIVAL_TOLERANCE:
            self._finish_return(now)
            return False

        improvement = command["distance"] - distance
        if improvement >= self.MIN_PROGRESS:
            self._preferred_key = command["key"]
            self._prepare_probes()
            self._recovery_index = 0
            self._recovery_rounds = 0
            self._set_status(
                MovementStatus.RETURNING,
                "fuera_de_radio" if self._forced_return else "volviendo",
            )
            return self._send_next_step(state, player, distance, now)

        if command["phase"] == "probe":
            self._probe_index += 1
            return self._send_next_step(state, player, distance, now)

        self._recovery_index += 1
        if self._recovery_index < len(self.RECOVERY_KEYS):
            return self._send_next_step(state, player, distance, now)

        self._recovery_rounds += 1
        if self._recovery_rounds >= self.MAX_RECOVERY_ROUNDS:
            self._failed_position = self._last_position
            self._fail("recuperacion_agotada")
            return False

        self._recovery_index = 0
        return self._send_next_step(state, player, distance, now)

    def _pause_for_combat(self, now):
        was_moving = self.is_navigating() or self._command is not None
        was_active = was_moving or self.status == MovementStatus.PAUSED
        if was_moving:
            self._release_movement()
        self._command = None
        self._forced_return = False
        self._outside_samples = 0
        self._last_motion_at = now
        self._set_status(
            MovementStatus.PAUSED if was_active else MovementStatus.IDLE,
            "objetivo_o_combate" if was_active else "",
        )

    def _cancel_navigation(self, now):
        if self.is_navigating() or self._command is not None:
            self._release_movement()
        self._command = None
        self._forced_return = False
        self._outside_samples = 0
        self._last_motion_at = now
        self._set_status(MovementStatus.IDLE)

    def _finish_return(self, now):
        self._release_movement()
        self._command = None
        self._forced_return = False
        self._outside_samples = 0
        self._last_motion_at = now
        self._set_status(MovementStatus.IDLE, "en_posicion")

    def _fail(self, reason):
        self._release_movement()
        self._command = None
        self._forced_return = False
        self._set_status(MovementStatus.FAILED, reason)

    def _release_movement(self):
        release = getattr(self.input, "release", None)
        if callable(release):
            for key in self.MOVEMENT_KEYS:
                release(key)
            return
        release_all = getattr(self.input, "release_all", None)
        if callable(release_all):
            release_all()

    def _set_status(self, status, reason=""):
        self.status = status
        self.reason = reason
        self.settings.returning = self.is_navigating()
        self._publish()

    def _publish(self, distance=None, key=None):
        if self._game_state is None:
            return
        if distance is None:
            distance = self._distance_to_start(self._game_state.player)
        self._game_state.navigation_active = self.is_navigating()
        self._game_state.navigation_status = self.status.value
        self._game_state.navigation_reason = self.reason
        self._game_state.navigation_distance = distance
        self._game_state.navigation_key = key

    @staticmethod
    def _distance_to_start(player):
        if not getattr(player, "position_locked", False):
            return None
        return math.hypot(player.x - player.start_x, player.y - player.start_y)

    @staticmethod
    def _point_distance(first, second):
        return math.hypot(first[0] - second[0], first[1] - second[1])

    def _reset_runtime(self, keep_status=False):
        self._last_revision = None
        self._last_position = None
        self._last_motion_at = None
        self._outside_samples = 0
        self._preferred_key = None
        self._probe_keys = []
        self._probe_index = 0
        self._recovery_index = 0
        self._recovery_rounds = 0
        self._command = None
        self._failed_position = None
        self._forced_return = False
        if not keep_status:
            self._set_status(MovementStatus.IDLE)
