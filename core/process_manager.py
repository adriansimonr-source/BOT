import psutil

from core.managers.config_manager import ConfigManager
from core.managers.game_profile_manager import GameProfileManager
from core.managers.window_manager import WindowManager


class ProcessManager:
    def __init__(self, game_profiles=None, config=None):
        self.config = config or ConfigManager()
        self.game_profiles = game_profiles or GameProfileManager()
        self.window_manager = WindowManager()

        self.process = None
        self.pid = None
        self.name = None
        self.window_title = None
        self.last_error = None

        active_game = self.config.get("active_game")
        if active_game:
            self.game_profiles.set_active_game(active_game)

    def discover_windows(self, window_title):
        """Resolve visible windows to their owning PID and executable."""
        if not window_title or not window_title.strip():
            return []

        results = []
        for window in self.window_manager.list_windows(window_title):
            try:
                process = psutil.Process(window["pid"])
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

            results.append(
                {
                    **window,
                    "process": process_name,
                }
            )
        return results

    def find_process(self, process_name=None, window_title=None):
        self.disconnect()

        process_name = process_name or self.game_profiles.get_process()
        window_title = window_title or self.game_profiles.get_window()
        if not process_name or not window_title:
            self.last_error = "profile_incomplete"
            return False

        candidates = self.discover_windows(window_title)
        if not candidates:
            self.last_error = "window_not_found"
            return False

        expected_process = process_name.casefold()
        for candidate in candidates:
            if candidate["process"].casefold() != expected_process:
                continue

            try:
                process = psutil.Process(candidate["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

            self.process = process
            self.pid = candidate["pid"]
            self.name = candidate["process"]
            self.window_title = candidate["title"]
            self.window_manager.hwnd = candidate["hwnd"]
            self.last_error = None
            return True

        self.last_error = "process_mismatch"
        return False

    def set_game(self, game_id, persist=True):
        if not self.game_profiles.set_active_game(game_id):
            return False

        self.disconnect()
        if persist and self.config.get("active_game") != game_id:
            self.config.set("active_game", game_id)
            self.config.save()
        return True

    def clear_game(self, persist=True):
        self.disconnect()
        self.game_profiles.clear_active_game()
        if persist and self.config.get("active_game") is not None:
            self.config.set("active_game", None)
            self.config.save()

    def get_active_game(self):
        return self.game_profiles.get_active_game()

    def find_window_only(self, title=None):
        title = title or self.game_profiles.get_window()
        found = self.window_manager.find_window_by_title(title)
        self.window_title = self.window_manager.get_title() if found else None
        return found

    def is_connected(self):
        if self.process is None or not self.window_manager.is_valid():
            return False
        try:
            return self.process.is_running()
        except psutil.Error:
            return False

    def get_pid(self):
        return self.pid

    def get_name(self):
        return self.name

    def get_process(self):
        return self.process

    def has_window(self):
        return self.window_manager.is_valid()

    def get_window_position(self):
        return self.window_manager.get_position()

    def get_window_handle(self):
        return self.window_manager.hwnd

    def get_window_title(self):
        return self.window_title

    def get_configured_process(self):
        return self.game_profiles.get_process()

    def get_configured_window(self):
        return self.game_profiles.get_window()

    def get_available_games(self):
        return self.game_profiles.get_games()

    def disconnect(self):
        self.process = None
        self.pid = None
        self.name = None
        self.window_title = None
        self.window_manager.hwnd = None
