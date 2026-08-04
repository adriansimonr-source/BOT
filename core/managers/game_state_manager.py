import time

from core.managers.vision_manager import VisionManager
from core.models.game_state import GameState


class GameStateManager:

    VISION_INTERVAL_SECONDS = 0.10

    def __init__(self, process_manager):
        self.process_manager = process_manager
        self.state = GameState()
        self.vision = None
        self.running = False
        self._last_vision_update = 0.0

    def start(self):
        if self.running:
            return

        if self.vision is None:
            active_game = self.process_manager.get_active_game() or {}
            window = self.process_manager.get_window_position() or {}
            capture_size = None
            if window.get("width") and window.get("height"):
                capture_size = (window["width"], window["height"])
            self.vision = VisionManager(
                active_game.get("id"),
                hwnd=self.process_manager.get_window_handle(),
                capture_size=capture_size,
            )

        self.vision.start()
        self._last_vision_update = 0.0
        self.running = True
        print("[GameStateManager] iniciado")

    def update(self):
        if not self.process_manager.is_connected():
            self.state.connected = False
            return

        self.state.connected = True
        if not self.running or not self.vision:
            return

        # Los resultados OCR terminados se aplican sin esperar al siguiente frame.
        self.vision.poll(self.state)
        now = time.perf_counter()
        if now - self._last_vision_update < self.VISION_INTERVAL_SECONDS:
            return

        self.vision.update(self.state)
        # Medir desde el final impide encadenar capturas si una operación se demora.
        self._last_vision_update = time.perf_counter()

    def update_auxiliary(self):
        if self.running and self.vision:
            self.vision.update_auxiliary(self.state)

    def lock_player_position(self):
        locked = self.state.player.lock_position()
        if locked:
            print(
                "[GameStateManager] posición inicial fijada",
                self.state.player.start_x,
                self.state.player.start_y,
            )
        return locked

    def unlock_player_position(self):
        self.state.player.unlock_position()
        print("[GameStateManager] posición inicial liberada")

    def refresh_player_position(self):
        self.state.player.invalidate_position()
        if self.vision:
            self.vision.reset_position_reader()
        print("[GameStateManager] refrescando posición")

    def refresh_player_name(self):
        self.state.player.name = ""
        if self.vision:
            self.vision.reset_player_name(self.state.player)
        print("[GameStateManager] refrescando nombre")

    def invalidate_vision(self):
        if self.running:
            return False
        self.vision = None
        return True

    def stop(self):
        if not self.running:
            return

        if self.vision:
            self.vision.stop()
        # La próxima ejecución debe usar el juego seleccionado en ese momento.
        self.vision = None
        self.running = False
        print("[GameStateManager] detenido")

    def get_state(self):
        return self.state
