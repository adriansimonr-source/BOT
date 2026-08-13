import threading
import time

from core.managers.com_utils import initialize_com_thread, uninitialize_com_thread
from core.managers.vision_manager import VisionManager
from core.models.game_state import GameState
from core.models.vision_snapshot import VisionSnapshot


class GameStateManager:

    VISION_INTERVAL_SECONDS = 0.10
    VISION_LOOP_INTERVAL_SECONDS = 0.025
    VISION_HEARTBEAT_TIMEOUT_SECONDS = 0.75
    FRAME_TIMEOUT_SECONDS = 0.75
    UI_SNAPSHOT_INTERVAL_SECONDS = 0.10
    START_TIMEOUT_SECONDS = 10.0
    START_POLL_SECONDS = 0.05

    def __init__(self, process_manager):
        self.process_manager = process_manager
        self.state = GameState()
        self.vision = None
        self.running = False
        self._lock = threading.RLock()
        self._latest_snapshot = None
        self._ui_state = self._clone_state(self.state)
        self._vision_error = None
        self._vision_thread = None
        self._stop_event = None
        self._ready_event = None
        self._stop_requested = False
        self._navigation_active = False
        self._position_epoch = 0
        self._sequence = 0
        self._last_ui_publish = 0.0

    def start(self):
        if self.running:
            return True
        if self._vision_thread is not None and self._vision_thread.is_alive():
            raise RuntimeError("La capa de visión anterior sigue cerrándose")

        with self._lock:
            if self._stop_requested:
                return False

        active_game = self.process_manager.get_active_game() or {}
        window = self.process_manager.get_window_position() or {}
        capture_size = None
        if window.get("width") and window.get("height"):
            capture_size = (window["width"], window["height"])
        specification = (
            active_game.get("id"),
            self.process_manager.get_window_handle(),
            capture_size,
        )

        stop_event = threading.Event()
        ready_event = threading.Event()
        with self._lock:
            if self._stop_requested:
                return False
            self._stop_event = stop_event
            self._ready_event = ready_event
            self._latest_snapshot = None
            self._vision_error = None
            self._navigation_active = False
            self._sequence = 0
        self.running = True
        self._vision_thread = threading.Thread(
            target=self._vision_loop,
            args=(specification, stop_event, ready_event),
            name="bot-vision",
            daemon=True,
        )
        self._vision_thread.start()

        deadline = time.perf_counter() + self.START_TIMEOUT_SECONDS
        while not ready_event.wait(self.START_POLL_SECONDS):
            if stop_event.is_set():
                return False
            if time.perf_counter() >= deadline:
                self.request_stop()
                raise RuntimeError("La capa de visión no respondió al iniciar")
        if stop_event.is_set():
            return False
        with self._lock:
            error = self._vision_error
        if error is not None:
            self.request_stop()
            raise RuntimeError(str(error)) from error
        return True

    def _vision_loop(self, specification, stop_event, ready_event):
        vision = None
        com_initialized = False
        vision_state = GameState()
        local_position_epoch = self._position_epoch
        last_vision_update = 0.0
        try:
            initialize_com_thread()
            com_initialized = True
            game_id, hwnd, capture_size = specification
            vision = VisionManager(
                game_id,
                hwnd=hwnd,
                capture_size=capture_size,
            )
            with self._lock:
                self.vision = vision
            vision.start()
            ready_event.set()

            while not stop_event.is_set():
                cycle_started_at = time.perf_counter()
                with self._lock:
                    vision_state.navigation_active = self._navigation_active
                    requested_epoch = self._position_epoch
                if requested_epoch != local_position_epoch:
                    vision_state.player.invalidate_position()
                    vision.reset_position_reader()
                    local_position_epoch = requested_epoch

                connected = bool(self.process_manager.is_connected())
                vision_state.connected = connected
                if connected:
                    if (
                        cycle_started_at - last_vision_update
                        >= self.VISION_INTERVAL_SECONDS
                    ):
                        vision.update(vision_state)
                        last_vision_update = time.perf_counter()
                    vision.update_auxiliary(vision_state)
                else:
                    vision_state.target.reset()
                    vision_state.in_combat = False

                self._publish_vision_snapshot(
                    vision_state,
                    vision,
                    local_position_epoch,
                )
                elapsed = time.perf_counter() - cycle_started_at
                stop_event.wait(
                    max(0.0, self.VISION_LOOP_INTERVAL_SECONDS - elapsed)
                )
        except Exception as error:
            with self._lock:
                self._vision_error = error
            ready_event.set()
        finally:
            ready_event.set()
            if vision is not None:
                try:
                    vision.stop()
                except Exception:
                    pass
            with self._lock:
                if self.vision is vision:
                    self.vision = None
            if com_initialized:
                uninitialize_com_thread()

    def _publish_vision_snapshot(self, state, vision, position_epoch):
        published_at = time.perf_counter()
        with self._lock:
            self._sequence += 1
            self._latest_snapshot = VisionSnapshot.from_state(
                state,
                sequence=self._sequence,
                published_at=published_at,
                frame_observed_at=getattr(
                    vision,
                    "latest_image_observed_at",
                    0.0,
                ),
                position_epoch=position_epoch,
            )

    def update(self):
        with self._lock:
            error = self._vision_error
            snapshot = self._latest_snapshot
            position_epoch = self._position_epoch
        if error is not None:
            raise RuntimeError(f"Error en visión: {error}") from error

        now = time.perf_counter()
        heartbeat_fresh = bool(
            snapshot
            and now - snapshot.published_at
            <= self.VISION_HEARTBEAT_TIMEOUT_SECONDS
        )
        frame_fresh = bool(
            snapshot
            and snapshot.frame_observed_at > 0
            and now - snapshot.frame_observed_at <= self.FRAME_TIMEOUT_SECONDS
        )
        connected = bool(
            snapshot
            and snapshot.connected
            and heartbeat_fresh
            and frame_fresh
        )

        if snapshot is not None:
            self._apply_snapshot(snapshot, position_epoch)
        self.state.connected = connected
        if not connected:
            self.state.target.reset()
            self.state.in_combat = False

    def _apply_snapshot(self, snapshot, position_epoch):
        player = self.state.player
        observed_player = snapshot.player
        player.hp_percent = observed_player.hp_percent
        player.hp_valid = observed_player.hp_valid
        player.hp_updated_at = observed_player.hp_updated_at
        player.mp_percent = observed_player.mp_percent
        player.mp_valid = observed_player.mp_valid
        player.mp_updated_at = observed_player.mp_updated_at
        player.z = observed_player.z
        if snapshot.position_epoch == position_epoch:
            player.x = observed_player.x
            player.y = observed_player.y
            player.position_valid = observed_player.position_valid
            player.position_updated_at = observed_player.position_updated_at
            player.position_revision = observed_player.position_revision
            player.position_history = list(observed_player.position_history)
        player.minimap_heading_deg = observed_player.minimap_heading_deg
        player.minimap_heading_confidence = (
            observed_player.minimap_heading_confidence
        )
        player.minimap_heading_valid = observed_player.minimap_heading_valid
        player.minimap_heading_updated_at = (
            observed_player.minimap_heading_updated_at
        )
        player.minimap_heading_revision = (
            observed_player.minimap_heading_revision
        )

        target = self.state.target
        observed_target = snapshot.target
        target.selection_id = observed_target.selection_id
        target.exists = observed_target.exists
        target.name = observed_target.name
        target.level = observed_target.level
        target.hp_percent = observed_target.hp_percent
        target.hp_valid = observed_target.hp_valid
        target.hp_observed_at = observed_target.hp_observed_at
        target.visible = observed_target.visible
        target.targetable = observed_target.targetable
        target.identity_pending = observed_target.identity_pending
        target.auto_target_decision = observed_target.auto_target_decision
        target.auto_target_decision_selection_id = (
            observed_target.auto_target_decision_selection_id
        )
        self.state.in_combat = snapshot.in_combat

    def update_auxiliary(self):
        with self._lock:
            self._navigation_active = bool(self.state.navigation_active)
        self.publish_state()

    def lock_player_position(self):
        locked = self.state.player.lock_position()
        self.publish_state(force=True)
        return locked

    def unlock_player_position(self):
        self.state.player.unlock_position()
        self.publish_state(force=True)

    def refresh_player_position(self):
        with self._lock:
            self._position_epoch += 1
        self.state.player.invalidate_position()
        self.publish_state(force=True)

    def invalidate_vision(self):
        thread = self._vision_thread
        if self.running or (thread is not None and thread.is_alive()):
            return False
        with self._lock:
            self.vision = None
            self._latest_snapshot = None
        return True

    def request_stop(self):
        with self._lock:
            self._stop_requested = True
            stop_event = self._stop_event
        if stop_event is not None:
            stop_event.set()

    def stop(self):
        thread = self._vision_thread
        if not self.running and thread is None:
            with self._lock:
                self._stop_event = None
                self._ready_event = None
                self._stop_requested = False
            return True

        self.running = False
        self.request_stop()
        self.state.connected = False
        self.state.target.reset()
        self.state.in_combat = False
        self.publish_state(force=True)
        if thread is not None and thread.is_alive():
            return False

        self._vision_thread = None
        with self._lock:
            self.vision = None
            self._latest_snapshot = None
            self._vision_error = None
            self._stop_event = None
            self._ready_event = None
            self._stop_requested = False
        return True

    def publish_state(self, force=False):
        now = time.perf_counter()
        if (
            not force
            and now - self._last_ui_publish
            < self.UI_SNAPSHOT_INTERVAL_SECONDS
        ):
            return
        snapshot = self._clone_state(self.state)
        with self._lock:
            self._ui_state = snapshot
            self._last_ui_publish = now

    def get_state(self):
        return self.state

    def get_ui_state(self):
        with self._lock:
            return self._ui_state

    @staticmethod
    def _clone_state(source):
        clone = GameState()
        clone.connected = source.connected
        clone.in_combat = source.in_combat
        for attribute, value in vars(source.player).items():
            setattr(
                clone.player,
                attribute,
                list(value) if attribute == "position_history" else value,
            )
        for attribute, value in vars(source.target).items():
            setattr(clone.target, attribute, value)
        for attribute in (
            "navigation_active",
            "navigation_status",
            "navigation_reason",
            "navigation_distance",
            "navigation_key",
            "navigation_confidence",
        ):
            setattr(clone, attribute, getattr(source, attribute))
        return clone
