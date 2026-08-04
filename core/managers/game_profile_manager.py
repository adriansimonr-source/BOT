import json
import os
import re
import unicodedata


class GameProfileManager:
    def __init__(self, path="data/games.json"):
        self.path = path
        self.games = {}
        self.active_game_id = None
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self.games = {}
            return

        with open(self.path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.games = {
            game["id"]: game
            for game in data.get("games", [])
            if isinstance(game, dict) and game.get("id")
        }
        if self.active_game_id not in self.games:
            self.active_game_id = None

    def save(self):
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        temporary_path = f"{self.path}.tmp"
        try:
            with open(temporary_path, "w", encoding="utf-8") as file:
                json.dump(
                    {"games": list(self.games.values())},
                    file,
                    indent=4,
                    ensure_ascii=False,
                )
            os.replace(temporary_path, self.path)
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

    def get_games(self):
        return list(self.games.values())

    def get_game(self, game_id):
        return self.games.get(game_id)

    def set_active_game(self, game_id):
        if game_id not in self.games:
            return False
        self.active_game_id = game_id
        return True

    def clear_active_game(self):
        self.active_game_id = None

    def get_active_game(self):
        return self.games.get(self.active_game_id)

    def get_process(self):
        game = self.get_active_game()
        return game.get("process") if game else None

    def get_window(self):
        game = self.get_active_game()
        return game.get("window") if game else None

    def get_resolution(self):
        game = self.get_active_game()
        resolution = game.get("resolution", {}) if game else {}
        return (
            resolution.get("width", 1920),
            resolution.get("height", 1080),
        )

    def create_game_id(self, name):
        normalized = unicodedata.normalize("NFKD", name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        base_id = re.sub(r"[^a-z0-9]+", "-", ascii_name.casefold()).strip("-")
        base_id = base_id or "game"

        candidate = base_id
        suffix = 2
        while candidate in self.games:
            candidate = f"{base_id}-{suffix}"
            suffix += 1
        return candidate

    def add_game(
        self,
        game_id,
        name,
        process,
        window,
        width=1920,
        height=1080,
    ):
        if not game_id or game_id in self.games:
            return False

        self.games[game_id] = {
            "id": game_id,
            "name": name,
            "process": process,
            "window": window,
            "resolution": {
                "width": int(width),
                "height": int(height),
            },
        }
        self.save()
        return True

    def remove_game(self, game_id):
        if game_id not in self.games:
            return False

        del self.games[game_id]
        if self.active_game_id == game_id:
            self.active_game_id = None
        self.save()
        return True
