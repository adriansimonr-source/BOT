import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.managers.config_manager import ConfigManager
from core.managers.game_profile_manager import GameProfileManager
from core.process_manager import ProcessManager


class FakeProcess:

    def __init__(self, pid, name):
        self.pid = pid
        self._name = name

    def name(self):
        return self._name

    def is_running(self):
        return True


class FakeWindowManager:

    def __init__(self, windows):
        self.windows = windows
        self.hwnd = None

    def list_windows(self, title=None):
        title = str(title or "").casefold()
        return [
            window
            for window in self.windows
            if title in window["title"].casefold()
        ]

    def is_valid(self):
        return self.hwnd is not None


class GameManagementTests(unittest.TestCase):

    def test_profiles_generate_unique_ids_and_persist(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "games.json"
            manager = GameProfileManager(str(path))

            first_id = manager.create_game_id("Juego único")
            self.assertEqual(first_id, "juego-unico")
            self.assertTrue(
                manager.add_game(
                    first_id,
                    "Juego único",
                    "Game.exe",
                    "Game Window",
                    1280,
                    720,
                )
            )
            self.assertEqual(manager.create_game_id("Juego único"), "juego-unico-2")
            self.assertFalse(
                manager.add_game(
                    first_id,
                    "Duplicado",
                    "Other.exe",
                    "Other Window",
                )
            )

            loaded = GameProfileManager(str(path))
            self.assertEqual(loaded.get_game(first_id)["process"], "Game.exe")

    def test_detection_uses_the_process_that_owns_the_matching_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            games_path = root / "games.json"
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps({"active_game": None}),
                encoding="utf-8",
            )
            profiles = GameProfileManager(str(games_path))
            profiles.add_game(
                "game",
                "Game",
                "Game.exe",
                "Game Window",
            )
            config = ConfigManager(str(config_path))
            manager = ProcessManager(profiles, config)
            manager.set_game("game", persist=False)
            manager.window_manager = FakeWindowManager(
                [
                    {
                        "hwnd": 111,
                        "pid": 10,
                        "title": "Game Window - launcher",
                        "width": 1280,
                        "height": 720,
                        "rect": (0, 0, 1280, 720),
                    },
                    {
                        "hwnd": 222,
                        "pid": 20,
                        "title": "Game Window",
                        "width": 1920,
                        "height": 1080,
                        "rect": (0, 0, 1920, 1080),
                    },
                ]
            )
            processes = {
                10: FakeProcess(10, "Launcher.exe"),
                20: FakeProcess(20, "game.EXE"),
            }

            with patch(
                "core.process_manager.psutil.Process",
                side_effect=lambda pid: processes[pid],
            ):
                self.assertTrue(manager.find_process())

            self.assertEqual(manager.get_pid(), 20)
            self.assertEqual(manager.get_window_handle(), 222)
            self.assertEqual(manager.get_window_title(), "Game Window")

    def test_selected_game_is_saved_in_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            games_path = root / "games.json"
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps({"active_game": None}),
                encoding="utf-8",
            )
            profiles = GameProfileManager(str(games_path))
            profiles.add_game("game", "Game", "Game.exe", "Game Window")
            manager = ProcessManager(
                profiles,
                ConfigManager(str(config_path)),
            )

            self.assertTrue(manager.set_game("game"))
            self.assertEqual(
                ConfigManager(str(config_path)).get("active_game"),
                "game",
            )

    def test_unique_target_filters_are_atomic_and_scoped_per_game(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path = Path(temporary) / "config.json"
            config_path.write_text(
                json.dumps({"active_game": "game-a"}),
                encoding="utf-8",
            )
            config = ConfigManager(str(config_path))

            self.assertTrue(
                config.set_game_target_filters(
                    "game-a",
                    ["Boss", "boss", "Elite"],
                    ignore_enabled=True,
                    unique_enabled=True,
                )
            )
            self.assertTrue(
                config.set_game_target_filters(
                    "game-b",
                    ["Other"],
                    unique_enabled=False,
                )
            )

            loaded = ConfigManager(str(config_path))
            self.assertEqual(
                loaded.get_game_target_filters("game-a"),
                {
                    "unique_targets": ["Boss", "Elite"],
                    "ignore_enabled": True,
                    "unique_enabled": True,
                },
            )
            self.assertEqual(
                loaded.get_game_target_filters("game-b")["unique_targets"],
                ["Other"],
            )
            self.assertEqual(
                loaded.get_game_target_filters("missing")["unique_targets"],
                [],
            )
            self.assertFalse((config_path.parent / "config.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
