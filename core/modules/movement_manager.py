import math
import time
from enum import Enum

from core.modules.base_module import BaseModule


class MovementStatus(Enum):
    IDLE = "idle"
    RETURNING = "returning"
    RECOVERING = "recovering"
    PAUSED = "paused"
    COOLDOWN = "cooldown"
    FAILED = "failed"


class MovementManager(BaseModule):

    POSITION_MAX_AGE_SECONDS = 3.0
    POSITION_WAIT_SECONDS = 2.0
    POST_RELEASE_SETTLE_SECONDS = 0.20
    ARRIVAL_TOLERANCE = 2.0
    MOTION_EPSILON = 1.0
    RELIABLE_PROGRESS = 1.25
    MAX_REGRESSION = 5.0
    OUTSIDE_CONFIRMATIONS = 2
    INPUT_WAIT_SECONDS = 0.75
    NO_PROGRESS_SECONDS = 6.5
    MIN_ATTEMPT_SECONDS = 12.0
    MAX_ATTEMPT_SECONDS = 25.0
    COOLDOWN_SECONDS = 5.0
    MIN_ACTIONS = 10
    MAX_ACTIONS = 48
    MAX_ATTEMPTS = 2
    CALIBRATED_SPEED = 6.0
    MAX_DRIVE_HOLD_MS = 650
    MOVEMENT_KEYS = ("W", "A", "D")
    RECOVERY_KEYS = ("A", "W", "D", "D", "W")

    def __init__(self, input_manager, settings):
        super().__init__("MovementManager", interval_ms=100)
        self.input = input_manager
        self.settings = settings
        self.status = MovementStatus.IDLE
        self.reason = ""
        self._game_state = None
        self._origin = None
        self._last_revision = None
        self._last_position = None
        self._last_motion_at = None
        self._outside_samples = 0
        self._command = None
        self._search_keys = []
        self._search_index = 0
        self._preferred_key = None
        self._candidate_key = None
        self._no_progress_pulses = 0
        self._recovery_used = False
        self._forced_return = False
        self._return_pending = False
        self._pending_reason = ""
        self._resume_attempt = False
        self._attempt_started_at = None
        self._attempt_deadline = None
        self._last_progress_at = None
        self._best_distance = None
        self._action_count = 0
        self._action_limit = self.MIN_ACTIONS
        self._input_wait_started_at = None
        self._retry_not_before = 0.0
        self._attempts = 0

    def on_start(self):
        super().on_start()
        self._reset_runtime()

    def on_stop(self):
        self._release_movement()
        self._reset_runtime()

    def update(self, state):
        now = time.perf_counter()
        self._game_state = state
        player = state.player
        origin = self._player_origin(player)

        if origin != self._origin:
            self._release_movement()
            self._reset_runtime(keep_position=True)
            self._origin = origin

        distance = self._distance_to_start(player)
        self._publish(distance)
        radius = self.settings.get_movement_range()
        if not self._navigation_configured(state, player, radius):
            self._cancel_navigation(now)
            return False
        if not self._has_fresh_position(player):
            if self.is_navigating() or self._command is not None:
                self._enter_cooldown(now, "coordenadas_no_disponibles")
            return False

        is_new_sample = self._consume_position_sample(player, now)
        distance = self._distance_to_start(player)
        outside_radius = distance > radius
        if is_new_sample:
            self._outside_samples = (
                self._outside_samples + 1 if outside_radius else 0
            )
        self._publish(distance)

        if distance <= self.ARRIVAL_TOLERANCE:
            if self.is_navigating() or self._return_pending:
                self._finish_return(now)
            else:
                self._outside_samples = 0
                self._reset_episode()
            return False

        if not outside_radius and self.status == MovementStatus.FAILED:
            self._reset_episode()
            self._set_status(MovementStatus.IDLE)

        outside_confirmed = (
            outside_radius
            and self._outside_samples >= self.OUTSIDE_CONFIRMATIONS
        )

        if self.status == MovementStatus.COOLDOWN:
            return self._update_cooldown(
                state,
                player,
                distance,
                now,
                outside_confirmed,
            )

        if self.status == MovementStatus.FAILED:
            return False

        if self._target_blocks_navigation(state):
            pending = bool(
                self.is_navigating()
                or self._command is not None
                or self._return_pending
                or outside_confirmed
            )
            if pending:
                self._pause_for_combat(
                    now,
                    outside=outside_confirmed or self._forced_return,
                )
            return False

        if self.status == MovementStatus.PAUSED:
            pending_reason = self._pending_reason or "reanudar"
            force = self._forced_return or outside_confirmed
            resume_attempt = self._resume_attempt
            self._set_status(MovementStatus.IDLE)
            if self._return_pending:
                self._return_pending = False
                self._resume_attempt = False
                return self._start_return(
                    player,
                    distance,
                    now,
                    pending_reason,
                    force=force,
                    count_attempt=not resume_attempt,
                )

        if outside_confirmed and not self._forced_return:
            self._forced_return = True
            if self.is_navigating() or self._command is not None:
                self.reason = "fuera_de_radio"
                self._publish(distance)
            else:
                return self._start_return(
                    player,
                    distance,
                    now,
                    "fuera_de_radio",
                    force=True,
                )

        if self.is_navigating() and self._watchdog_expired(distance, now):
            self._enter_cooldown(now, "retorno_sin_progreso")
            return False

        if self._command is not None:
            if (
                is_new_sample
                and player.position_revision != self._command["revision"]
                and now >= self._command["observe_after"]
            ):
                return self._evaluate_command(player, distance, now)
            if now >= self._command["sample_deadline"]:
                self._enter_cooldown(now, "sin_coordenada_nueva")
            return False

        if self.is_navigating():
            return self._send_next_step(player, distance, now)

        quiet_seconds = max(3.0, float(self.settings.return_delay))
        if (
            self._last_motion_at is not None
            and now - self._last_motion_at >= quiet_seconds
        ):
            return self._start_return(player, distance, now, "quieto")

        return False

    def is_navigating(self):
        return self.status in (
            MovementStatus.RETURNING,
            MovementStatus.RECOVERING,
        )

    def _navigation_configured(self, state, player, radius):
        if hasattr(state, "connected") and not state.connected:
            return False
        if not self.settings.auto_return or radius is None:
            return False
        if not player.position_locked:
            return False
        return True

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
            or self._point_distance(self._last_position, position)
            >= self.MOTION_EPSILON
        ):
            self._last_motion_at = now

        self._last_position = position
        self._last_revision = revision
        if self._last_motion_at is None:
            self._last_motion_at = now
        return True

    def _start_return(
        self,
        player,
        distance,
        now,
        reason,
        force=False,
        count_attempt=True,
    ):
        if count_attempt:
            self._attempts += 1
        self._forced_return = force
        self._return_pending = False
        self._pending_reason = ""
        self._resume_attempt = False
        self._attempt_started_at = now
        travel_budget = distance / self.CALIBRATED_SPEED * 2.0 + 8.0
        self._attempt_deadline = now + min(
            self.MAX_ATTEMPT_SECONDS,
            max(self.MIN_ATTEMPT_SECONDS, travel_budget),
        )
        self._last_progress_at = now
        self._best_distance = distance
        self._action_count = 0
        pulse_distance = self.CALIBRATED_SPEED * self.MAX_DRIVE_HOLD_MS / 1000
        estimated_pulses = math.ceil(
            max(0.0, distance - self.ARRIVAL_TOLERANCE) / pulse_distance
        )
        self._action_limit = min(
            self.MAX_ACTIONS,
            max(self.MIN_ACTIONS, estimated_pulses * 2 + 6),
        )
        self._input_wait_started_at = None
        self._preferred_key = None
        self._candidate_key = None
        self._no_progress_pulses = 0
        self._recovery_used = False
        self._prepare_search()
        self._set_status(MovementStatus.RETURNING, reason)
        return self._send_next_step(player, distance, now)

    def _prepare_search(self, excluded_key=None):
        keys = list(self.MOVEMENT_KEYS)
        if excluded_key in keys:
            keys.remove(excluded_key)
            keys.append(excluded_key)
        self._search_keys = keys
        self._search_index = 0
        self._candidate_key = None

    def _send_next_step(self, player, distance, now):
        if self._action_count >= self._action_limit:
            self._enter_cooldown(now, "limite_de_movimientos")
            return False

        if self._candidate_key is not None:
            return self._send_command(
                player,
                distance,
                now,
                self._candidate_key,
                "confirm",
                self._probe_hold_ms(self._candidate_key),
            )

        if self._preferred_key is not None:
            hold_ms = self._dynamic_hold_ms(distance)
            if hold_ms <= 0:
                self._finish_return(now)
                return False
            return self._send_command(
                player,
                distance,
                now,
                self._preferred_key,
                "follow",
                hold_ms,
            )

        if self._search_index >= len(self._search_keys):
            if self._recovery_used:
                self._enter_cooldown(now, "sin_direccion_util")
                return False
            self._recovery_used = True
            self._search_keys = list(self.RECOVERY_KEYS)
            self._search_index = 0
            self._set_status(MovementStatus.RECOVERING, "buscando_ruta")

        key = self._search_keys[self._search_index]
        self._search_index += 1
        phase = (
            "recovery"
            if self.status == MovementStatus.RECOVERING
            else "probe"
        )
        return self._send_command(
            player,
            distance,
            now,
            key,
            phase,
            self._probe_hold_ms(key),
        )

    def _send_command(self, player, distance, now, key, phase, hold_ms):
        if not self.input.press(key, hold_ms=hold_ms):
            if self._input_wait_started_at is None:
                self._input_wait_started_at = now
            if now - self._input_wait_started_at >= self.INPUT_WAIT_SECONDS:
                self._enter_cooldown(now, "entrada_ocupada")
            else:
                self.reason = "esperando_entrada"
                self._publish(distance)
            return False

        self._input_wait_started_at = None
        self._action_count += 1
        release_at = now + hold_ms / 1000
        self._command = {
            "key": key,
            "phase": phase,
            "distance": distance,
            "position": (int(player.x), int(player.y)),
            "revision": player.position_revision,
            "release_at": release_at,
            "observe_after": release_at + self.POST_RELEASE_SETTLE_SECONDS,
            "sample_deadline": release_at + self.POSITION_WAIT_SECONDS,
        }
        self._publish(distance, key)
        return True

    def _evaluate_command(self, player, distance, now):
        command = self._command
        self._release_command_key(command, now)
        self._command = None

        if distance <= self.ARRIVAL_TOLERANCE:
            self._finish_return(now)
            return False

        improvement = command["distance"] - distance
        if self._best_distance is None or (
            self._best_distance - distance >= self.RELIABLE_PROGRESS
        ):
            self._best_distance = distance
            self._last_progress_at = now

        phase = command["phase"]
        key = command["key"]
        if phase == "confirm":
            self._candidate_key = None
            if improvement >= self.RELIABLE_PROGRESS:
                self._preferred_key = key
                self._no_progress_pulses = 0
                self._set_status(
                    MovementStatus.RETURNING,
                    "fuera_de_radio" if self._forced_return else "volviendo",
                )
            return self._send_next_step(player, distance, now)

        if phase in ("probe", "recovery"):
            if improvement >= self.RELIABLE_PROGRESS:
                self._candidate_key = key
                self.reason = "confirmando_direccion"
                self._publish(distance)
            return self._send_next_step(player, distance, now)

        if improvement >= self.RELIABLE_PROGRESS:
            self._no_progress_pulses = 0
            return self._send_next_step(player, distance, now)

        self._no_progress_pulses += 1
        if (
            improvement > -self.RELIABLE_PROGRESS
            and self._no_progress_pulses < 2
        ):
            self.reason = "confirmando_progreso"
            return self._send_next_step(player, distance, now)

        failed_key = self._preferred_key
        self._preferred_key = None
        self._no_progress_pulses = 0
        self._recovery_used = False
        self._prepare_search(excluded_key=failed_key)
        self._set_status(MovementStatus.RETURNING, "direccion_sin_progreso")
        return self._send_next_step(player, distance, now)

    def _probe_hold_ms(self, key):
        base = self._configured_hold_ms()
        if key == "W":
            return min(500, max(400, base))
        return min(350, max(250, base))

    def _dynamic_hold_ms(self, distance):
        travel_distance = max(0.0, distance - self.ARRIVAL_TOLERANCE)
        if travel_distance <= 0:
            return 0
        calibrated_ms = round(travel_distance / self.CALIBRATED_SPEED * 1000)
        return min(
            self.MAX_DRIVE_HOLD_MS,
            max(self._configured_hold_ms(), calibrated_ms),
        )

    def _configured_hold_ms(self):
        try:
            value = int(self.settings.movement_hold_ms)
        except (TypeError, ValueError, OverflowError):
            value = 250
        return min(self.MAX_DRIVE_HOLD_MS, max(100, value))

    def _watchdog_expired(self, distance, now):
        if self._attempt_started_at is None:
            return False
        if self._attempt_deadline is not None and now >= self._attempt_deadline:
            return True
        if now - self._last_progress_at >= self.NO_PROGRESS_SECONDS:
            return True
        return bool(
            self._best_distance is not None
            and distance - self._best_distance >= self.MAX_REGRESSION
        )

    def _update_cooldown(
        self,
        state,
        player,
        distance,
        now,
        outside_confirmed,
    ):
        self._publish(distance)
        if now < self._retry_not_before:
            return False
        if self._target_blocks_navigation(state):
            return False
        if self._attempts >= self.MAX_ATTEMPTS:
            self._set_status(MovementStatus.FAILED, "retorno_agotado")
            return False
        if outside_confirmed:
            return self._start_return(
                player,
                distance,
                now,
                "reintentando_retorno",
                force=True,
            )
        self._last_motion_at = now
        self._reset_episode()
        self._set_status(MovementStatus.IDLE)
        return False

    def _pause_for_combat(self, now, outside=False):
        was_active = self.is_navigating() or self._command is not None
        self._return_pending = was_active or self._return_pending or outside
        self._pending_reason = (
            "fuera_de_radio"
            if outside or self._forced_return
            else (self.reason or "reanudar")
        )
        self._resume_attempt = was_active and self._attempt_started_at is not None
        if was_active:
            self._release_movement()
        self._command = None
        self._preferred_key = None
        self._candidate_key = None
        self._set_status(MovementStatus.PAUSED, "objetivo_o_combate")
        self._last_motion_at = now

    def _enter_cooldown(self, now, reason):
        self._release_movement()
        self._command = None
        self._preferred_key = None
        self._candidate_key = None
        self._forced_return = False
        self._return_pending = False
        self._resume_attempt = False
        self._retry_not_before = now + self.COOLDOWN_SECONDS
        self._set_status(MovementStatus.COOLDOWN, reason)

    def _cancel_navigation(self, now):
        if self.is_navigating() or self._command is not None:
            self._release_movement()
        self._reset_episode()
        self._command = None
        self._outside_samples = 0
        self._last_motion_at = now
        self._set_status(MovementStatus.IDLE)

    def _finish_return(self, now):
        self._release_movement()
        self._command = None
        self._outside_samples = 0
        self._last_motion_at = now
        self._reset_episode()
        self._set_status(MovementStatus.IDLE, "en_posicion")

    def _release_key(self, key):
        release = getattr(self.input, "release", None)
        if callable(release):
            return release(key)
        release_all = getattr(self.input, "release_all", None)
        if callable(release_all):
            release_all()
            return True
        return False

    def _release_command_key(self, command, now):
        is_held = getattr(self.input, "is_held", None)
        if callable(is_held):
            if not is_held(command["key"]):
                return False
        elif now >= command["release_at"]:
            return False
        return self._release_key(command["key"])

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
        if key is None and self._command is not None:
            key = self._command["key"]
        self._game_state.navigation_active = self.is_navigating()
        self._game_state.navigation_status = self.status.value
        self._game_state.navigation_reason = self.reason
        self._game_state.navigation_distance = distance
        self._game_state.navigation_key = key

    @staticmethod
    def _player_origin(player):
        if not getattr(player, "position_locked", False):
            return None
        return int(player.start_x), int(player.start_y)

    @staticmethod
    def _distance_to_start(player):
        if not getattr(player, "position_locked", False):
            return None
        return math.hypot(player.x - player.start_x, player.y - player.start_y)

    @staticmethod
    def _point_distance(first, second):
        return math.hypot(first[0] - second[0], first[1] - second[1])

    def _reset_episode(self):
        self._forced_return = False
        self._return_pending = False
        self._pending_reason = ""
        self._resume_attempt = False
        self._attempt_started_at = None
        self._attempt_deadline = None
        self._last_progress_at = None
        self._best_distance = None
        self._action_count = 0
        self._action_limit = self.MIN_ACTIONS
        self._input_wait_started_at = None
        self._retry_not_before = 0.0
        self._attempts = 0
        self._preferred_key = None
        self._candidate_key = None
        self._no_progress_pulses = 0
        self._recovery_used = False
        self._search_keys = []
        self._search_index = 0

    def _reset_runtime(self, keep_position=False):
        if not keep_position:
            self._origin = None
            self._last_revision = None
            self._last_position = None
            self._last_motion_at = None
        self._outside_samples = 0
        self._command = None
        self._reset_episode()
        self._set_status(MovementStatus.IDLE)
